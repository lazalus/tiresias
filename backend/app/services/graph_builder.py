"""
그래프 구축 서비스
LLM + Neo4j를 사용하여 로컬 지식 그래프를 구축합니다.
"""

import concurrent.futures
import json
import re
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from ..models.task import TaskManager, TaskStatus
from ..config import Config
from ..utils.llm_client import LLMClient
from .neo4j_graph_store import Neo4jGraphStore
from .text_processor import TextProcessor


ENTITY_NAMESPACE = uuid.UUID("4ba77888-75c7-4b64-ac9d-4ef8797670db")
EDGE_NAMESPACE = uuid.UUID("3364fdd0-c55a-4671-93ac-fb86672895df")
ENTITY_STAGE_PROGRESS_SHARE = 0.45
RELATION_STAGE_PROGRESS_SHARE = 0.55
ENTITY_EXTRACTION_MAX_TOKENS = 1600
RELATION_EXTRACTION_MAX_TOKENS = 1200
RELATION_CANDIDATE_LIMIT = 12


@dataclass
class GraphInfo:
    """그래프 정보"""

    graph_id: str
    node_count: int
    edge_count: int
    entity_types: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "entity_types": self.entity_types,
        }


class GraphBuilderService:
    """
    그래프 구축 서비스.

    외부적으로는 이전 Zep 구현과 호환되는 메서드 시그니처를 유지하고,
    내부적으로는 온톨로지와 추출 결과를 Neo4j에 작성하도록 변경합니다.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,  # 이전 호출자와 호환되도록, 현재는 무시
        llm_client: Optional[LLMClient] = None,
        store: Optional[Neo4jGraphStore] = None,
    ):
        self.task_manager = TaskManager()
        self.llm = llm_client or LLMClient()
        self.store = store or Neo4jGraphStore()
        self.store.ensure_schema()
        self._ontology_cache: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _normalize_key(value: str) -> str:
        return re.sub(r"[\W_]+", "", (value or "").strip().lower())

    @staticmethod
    def _clean_text(value: Any) -> str:
        return str(value or "").strip()

    @classmethod
    def _normalize_mention(cls, value: str) -> str:
        return re.sub(r"[\s\W_]+", "", (value or "").strip().lower())

    @classmethod
    def _entity_aliases(cls, name: str) -> List[str]:
        aliases: List[str] = []

        def add_alias(candidate: str) -> None:
            cleaned = cls._clean_text(candidate)
            if not cleaned:
                return
            if cls._normalize_mention(cleaned) and cleaned not in aliases:
                aliases.append(cleaned)

        add_alias(name)
        add_alias(re.sub(r"\([^)]*\)", "", name).strip())
        for match in re.findall(r"\(([^)]{2,})\)", name or ""):
            add_alias(match)

        return aliases

    @classmethod
    def _text_mentions_candidate(cls, text: str, candidate: str) -> bool:
        normalized_candidate = cls._normalize_mention(candidate)
        if len(normalized_candidate) < 2:
            return False

        if candidate and candidate in text:
            return True

        normalized_text = cls._normalize_mention(text)
        return normalized_candidate in normalized_text

    @classmethod
    def _is_generic_entity_name(cls, name: str, ontology: Dict[str, Any]) -> bool:
        if not name:
            return True

        normalized = cls._normalize_mention(name)
        if not normalized:
            return True

        generic_names = {
            "entity",
            "person",
            "organization",
            "company",
            "institution",
            "agency",
            "government",
            "country",
            "brand",
            "platform",
            "group",
            "individual",
            "기업",
            "회사",
            "기관",
            "정부",
            "국가",
            "조직",
            "개인",
            "인물",
            "브랜드",
            "플랫폼",
            "집단",
            "산업",
            "업계",
        }
        if normalized in generic_names:
            return True

        ontology_entity_names = {
            cls._normalize_mention(item.get("name", ""))
            for item in (ontology.get("entity_types", []) or [])
            if item.get("name")
        }
        return normalized in ontology_entity_names

    @staticmethod
    def _coerce_json_scalar(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            result = []
            for item in value:
                coerced = GraphBuilderService._coerce_json_scalar(item)
                if coerced is not None:
                    result.append(coerced)
            return result
        return str(value)

    @staticmethod
    def _is_runtime_memory_node(node: Dict[str, Any]) -> bool:
        labels = node.get("labels", []) or []
        if node.get("simulation_id"):
            return True
        if node.get("is_runtime_memory"):
            return True
        return "MemorySummary" in labels or "SimulationActivity" in labels

    @staticmethod
    def _is_runtime_memory_edge(edge: Dict[str, Any]) -> bool:
        if edge.get("simulation_id"):
            return True
        if edge.get("is_runtime_memory"):
            return True
        return edge.get("name") in {"SIMULATION_ACTIVITY", "SIMULATION_MEMORY_SUMMARY"}

    @classmethod
    def _canonical_entity_uuid(cls, graph_id: str, entity_type: str, name: str) -> str:
        seed = f"{graph_id}:{cls._normalize_key(entity_type)}:{cls._normalize_key(name)}"
        return str(uuid.uuid5(ENTITY_NAMESPACE, seed))

    @classmethod
    def _canonical_edge_uuid(
        cls,
        graph_id: str,
        source_uuid: str,
        edge_name: str,
        target_uuid: str,
        fact: str,
    ) -> str:
        seed = "|".join(
            [
                graph_id,
                source_uuid,
                cls._normalize_key(edge_name),
                target_uuid,
                cls._normalize_key(fact),
            ]
        )
        return str(uuid.uuid5(EDGE_NAMESPACE, seed))

    @staticmethod
    def _pick_fallback_entity_type(
        candidate: str,
        entity_names: List[str],
    ) -> str:
        normalized = (candidate or "").strip().lower()
        organization_like = (
            "company",
            "organization",
            "agency",
            "university",
            "school",
            "media",
            "outlet",
            "institution",
            "committee",
            "group",
            "platform",
            "brand",
            "association",
        )
        if normalized and any(token in normalized for token in organization_like):
            for fallback in entity_names:
                if fallback.lower() == "organization":
                    return fallback

        for fallback in entity_names:
            if fallback.lower() == "person":
                return fallback

        return entity_names[0] if entity_names else "Entity"

    @classmethod
    def _resolve_entity_type(cls, candidate: str, ontology: Dict[str, Any]) -> str:
        entity_defs = ontology.get("entity_types", []) or []
        entity_names = [item.get("name", "Entity") for item in entity_defs if item.get("name")]
        lookup = {cls._normalize_key(name): name for name in entity_names}
        normalized = cls._normalize_key(candidate)
        if normalized in lookup:
            return lookup[normalized]
        return cls._pick_fallback_entity_type(candidate, entity_names)

    @classmethod
    def _resolve_edge_type(
        cls,
        candidate: str,
        source_type: str,
        target_type: str,
        ontology: Dict[str, Any],
    ) -> str:
        edge_defs = ontology.get("edge_types", []) or []
        if not edge_defs:
            return "RELATED_TO"

        canonical_names = [item.get("name", "RELATED_TO") for item in edge_defs if item.get("name")]
        lookup = {cls._normalize_key(name): name for name in canonical_names}
        allowed_by_pair: List[str] = []

        for edge_def in edge_defs:
            edge_name = edge_def.get("name")
            if not edge_name:
                continue
            for pair in edge_def.get("source_targets", []) or []:
                if pair.get("source") == source_type and pair.get("target") == target_type:
                    allowed_by_pair.append(edge_name)
                    break

        normalized = cls._normalize_key(candidate)
        if normalized in lookup:
            matched = lookup[normalized]
            if not allowed_by_pair or matched in allowed_by_pair:
                return matched

        if allowed_by_pair:
            return allowed_by_pair[0]

        return canonical_names[0]

    @staticmethod
    def _ontology_attribute_names(ontology: Dict[str, Any], entity_type: str) -> List[str]:
        for entity_def in ontology.get("entity_types", []) or []:
            if entity_def.get("name") == entity_type:
                return [attr.get("name") for attr in entity_def.get("attributes", []) if attr.get("name")]
        return []

    @staticmethod
    def _filter_entity_attributes(attributes: Any, allowed_names: List[str]) -> Dict[str, Any]:
        if not isinstance(attributes, dict):
            return {}

        allowed = set(allowed_names)
        result: Dict[str, Any] = {}
        for key, value in attributes.items():
            if key not in allowed:
                continue
            coerced = GraphBuilderService._coerce_json_scalar(value)
            if coerced is None:
                continue
            if isinstance(coerced, str) and not coerced.strip():
                continue
            result[key] = coerced
        return result

    @staticmethod
    def _coerce_temporal(value: Any) -> Optional[str]:
        text = str(value or "").strip()
        return text or None

    @classmethod
    def _entity_appears_in_chunk(cls, entity: Dict[str, Any], chunk_text: str) -> bool:
        aliases = entity.get("aliases") or cls._entity_aliases(entity.get("name", ""))
        for alias in aliases:
            if cls._text_mentions_candidate(chunk_text, alias):
                return True
        return False

    @classmethod
    def _candidate_prompt_payload(cls, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        payload: List[Dict[str, Any]] = []
        for entity in entities[:RELATION_CANDIDATE_LIMIT]:
            payload.append(
                {
                    "name": entity.get("name", ""),
                    "type": entity.get("entity_type", ""),
                    "aliases": entity.get("aliases", [])[:3],
                    "summary": entity.get("summary", ""),
                }
            )
        return payload

    @classmethod
    def _candidate_lookup(cls, entities: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        lookup: Dict[str, Dict[str, Any]] = {}
        for entity in entities.values():
            aliases = entity.get("aliases") or cls._entity_aliases(entity.get("name", ""))
            for alias in aliases:
                normalized = cls._normalize_mention(alias)
                if normalized and normalized not in lookup:
                    lookup[normalized] = entity
        return lookup

    @classmethod
    def _resolve_candidate_entity(
        cls,
        lookup: Dict[str, Dict[str, Any]],
        candidate_name: str,
    ) -> Optional[Dict[str, Any]]:
        normalized = cls._normalize_mention(candidate_name)
        if not normalized:
            return None
        return lookup.get(normalized)

    def build_graph_async(
        self,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str = "Tiresias Graph",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 3,
    ) -> str:
        """
        비동기적으로 그래프를 구축합니다.
        이전 인터페이스를 유지하여 해당 서비스가 필요한 내부 호출에서 재사용할 수 있도록 합니다.
        """
        task_id = self.task_manager.create_task(
            task_type="graph_build",
            metadata={
                "graph_name": graph_name,
                "chunk_size": chunk_size,
                "text_length": len(text),
            },
        )

        thread = threading.Thread(
            target=self._build_graph_worker,
            args=(task_id, text, ontology, graph_name, chunk_size, chunk_overlap, batch_size),
            daemon=True,
        )
        thread.start()

        return task_id

    def _build_graph_worker(
        self,
        task_id: str,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        batch_size: int,
    ):
        try:
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                progress=5,
                message="그래프 구축 시작...",
            )

            graph_id = self.create_graph(graph_name)
            self.task_manager.update_task(task_id, progress=10, message=f"그래프가 생성됨: {graph_id}")

            self.set_ontology(graph_id, ontology)
            self.task_manager.update_task(task_id, progress=15, message="온톨로지가 설정됨")

            chunks = TextProcessor.split_text(text, chunk_size, chunk_overlap)
            total_chunks = len(chunks)
            self.task_manager.update_task(
                task_id,
                progress=20,
                message=f"텍스트가 {total_chunks}개 청크로 분할됨",
            )

            self.add_text_batches(
                graph_id,
                chunks,
                batch_size,
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=20 + int(prog * 0.7),
                    message=msg,
                ),
            )

            self._wait_for_episodes(
                [],
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=90 + int(prog * 0.05),
                    message=msg,
                ),
            )

            self.task_manager.update_task(task_id, progress=95, message="그래프 정보 가져오는 중...")
            graph_info = self._get_graph_info(graph_id)
            self.task_manager.complete_task(
                task_id,
                {
                    "graph_id": graph_id,
                    "graph_info": graph_info.to_dict(),
                    "chunks_processed": total_chunks,
                },
            )

        except Exception as exc:
            import traceback

            error_msg = f"{str(exc)}\n{traceback.format_exc()}"
            self.task_manager.fail_task(task_id, error_msg)

    def create_graph(self, name: str) -> str:
        """로컬 그래프를 생성합니다."""
        graph_id = f"tiresias_{uuid.uuid4().hex[:16]}"
        self.store.create_graph(
            graph_id=graph_id,
            name=name,
            description="Tiresias Local Neo4j Graph",
        )
        return graph_id

    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """그래프 온톨로지를 저장합니다."""
        self._ontology_cache[graph_id] = ontology
        self.store.set_ontology(graph_id, ontology)

    def _extract_chunk_entities(
        self,
        ontology: Dict[str, Any],
        chunk: str,
        chunk_index: int,
    ) -> Dict[str, Any]:
        system_prompt = """당신은 엄격한 지식 그래프 엔티티 추출기입니다. 주어진 온톨로지에 따라 텍스트 청크에서 엔티티만 추출합니다.

규칙:
1. 온톨로지에 정의된 엔티티 유형 및 관계 유형만 사용해야 합니다.
2. 텍스트에 명확하게 나타나고 소셜 미디어 시뮬레이션에 적합한 실제 주체(개인, 조직, 회사, 미디어, 기관, 플랫폼, 그룹)만 추출합니다.
3. 청크에 명시적으로 적혀 있지 않은 이름을 절대 만들어내지 마십시오.
4. 일반명사(예: Organization, 정부, 기업, 업계, 주요 여행사 등)나 분류명만으로 엔티티를 만들지 마십시오.
5. 수치 지표, 일반 개념, 제목, 목차 항목은 엔티티로 만들지 마십시오.
6. 동일한 이름과 유형의 엔티티는 동일한 정식 이름을 사용해야 합니다.
7. 요약은 최대 2문장이어야 하며, 속성은 온톨로지에 정의된 속성만 유지합니다.
8. 확실하지 않으면 추측하지 말고 빈 배열을 반환하십시오.

JSON 반환:
{
  "entities": [
    {
      "name": "엔티티 이름",
      "type": "엔티티 유형",
      "summary": "간략 요약",
      "attributes": {}
    }
  ]
}"""

        user_prompt = (
            f"Ontology:\n{json.dumps(ontology, ensure_ascii=False, indent=2)}\n\n"
            f"Chunk #{chunk_index}:\n{chunk}\n"
        )

        payload = self.llm.chat_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=ENTITY_EXTRACTION_MAX_TOKENS,
        )
        payload["_chunk_text"] = chunk
        return payload

    def _extract_chunk_relationships(
        self,
        ontology: Dict[str, Any],
        chunk: str,
        chunk_index: int,
        candidate_entities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        system_prompt = """당신은 엄격한 지식 그래프 관계 추출기입니다. 주어진 후보 엔티티 목록을 기준으로 관계만 추출합니다.

규칙:
1. 아래 후보 엔티티 목록에 있는 이름만 사용해야 합니다.
2. 출력하는 source_name, target_name은 후보 목록의 canonical name과 정확히 일치해야 합니다.
3. 소스와 타깃 엔티티 이름이 둘 다 청크에 직접 등장할 때만 관계를 추출합니다.
4. 관계 유형은 온톨로지에 정의된 관계만 사용합니다.
5. 자기 자신으로 향하는 관계는 만들지 마십시오.
6. 확실하지 않으면 빈 배열을 반환하십시오.

JSON 반환:
{
  "relationships": [
    {
      "source_name": "소스 엔티티 이름",
      "target_name": "대상 엔티티 이름",
      "relation_type": "관계 유형",
      "fact": "사실 설명",
      "valid_at": null,
      "invalid_at": null,
      "expired_at": null,
      "attributes": {}
    }
  ]
}"""

        user_prompt = (
            f"Ontology:\n{json.dumps(ontology, ensure_ascii=False, indent=2)}\n\n"
            f"Candidate Entities:\n{json.dumps(self._candidate_prompt_payload(candidate_entities), ensure_ascii=False, indent=2)}\n\n"
            f"Chunk #{chunk_index}:\n{chunk}\n"
        )

        payload = self.llm.chat_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=RELATION_EXTRACTION_MAX_TOKENS,
        )
        payload["_chunk_text"] = chunk
        return payload

    def _run_chunk_stage(
        self,
        chunks: List[str],
        batch_size: int,
        stage_label: str,
        stage_offset: float,
        stage_share: float,
        progress_callback: Optional[Callable],
        extractor: Callable[[str, int], Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        payloads: List[Dict[str, Any]] = []
        total_chunks = len(chunks)

        for start in range(0, total_chunks, batch_size):
            batch_chunks = chunks[start : start + batch_size]
            batch_num = start // batch_size + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size

            if progress_callback:
                progress_callback(
                    f"{stage_label} {batch_num}/{total_batches} 배치 처리 중...",
                    stage_offset + stage_share * (start / max(total_chunks, 1)),
                )

            max_workers = max(1, min(len(batch_chunks), Config.GRAPH_EXTRACTION_MAX_WORKERS))
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {}
                for offset, chunk in enumerate(batch_chunks):
                    chunk_index = start + offset + 1
                    future = executor.submit(extractor, chunk, chunk_index)
                    future_map[future] = chunk_index

                for future in concurrent.futures.as_completed(future_map):
                    chunk_index = future_map[future]
                    payload = future.result()
                    payload["_chunk_index"] = chunk_index
                    payloads.append(payload)

            if progress_callback:
                processed = min(start + len(batch_chunks), total_chunks)
                progress_callback(
                    f"{stage_label} {batch_num}/{total_batches} 배치 완료 (누적 {processed}/{total_chunks} 청크)",
                    stage_offset + stage_share * (processed / max(total_chunks, 1)),
                )

        return payloads

    def add_text_batches(
        self,
        graph_id: str,
        chunks: List[str],
        batch_size: int = 3,
        progress_callback: Optional[Callable] = None,
    ) -> List[str]:
        """텍스트를 일괄 추출하여 Neo4j에 작성합니다. 처리된 청크 식별자를 반환합니다."""
        if not chunks:
            return []

        ontology = self._ontology_cache.get(graph_id) or self.store.get_ontology(graph_id)
        if not ontology:
            raise ValueError("그래프 온톨로지가 존재하지 않습니다. 먼저 온톨로지를 설정하십시오.")

        entity_payloads = self._run_chunk_stage(
            chunks=chunks,
            batch_size=batch_size,
            stage_label="후보 엔티티 사전 구축",
            stage_offset=0.0,
            stage_share=ENTITY_STAGE_PROGRESS_SHARE,
            progress_callback=progress_callback,
            extractor=lambda chunk, chunk_index: self._extract_chunk_entities(ontology, chunk, chunk_index),
        )

        entity_map = self._normalize_entity_extractions(graph_id, ontology, entity_payloads)
        entities = list(entity_map.values())
        if entities:
            self.store.upsert_entities(graph_id, entities)

        if progress_callback:
            progress_callback(
                f"후보 엔티티 {len(entities)}개 확정, 관계 추출 단계로 이동",
                ENTITY_STAGE_PROGRESS_SHARE,
            )

        relation_payloads: List[Dict[str, Any]] = []
        if len(entity_map) >= 2:
            candidate_entities = list(entity_map.values())

            def relationship_extractor(chunk: str, chunk_index: int) -> Dict[str, Any]:
                chunk_candidates = [
                    entity for entity in candidate_entities
                    if self._entity_appears_in_chunk(entity, chunk)
                ]
                if len(chunk_candidates) < 2:
                    return {"relationships": [], "_chunk_text": chunk}
                return self._extract_chunk_relationships(
                    ontology,
                    chunk,
                    chunk_index,
                    chunk_candidates[:RELATION_CANDIDATE_LIMIT],
                )

            relation_payloads = self._run_chunk_stage(
                chunks=chunks,
                batch_size=batch_size,
                stage_label="관계 추출",
                stage_offset=ENTITY_STAGE_PROGRESS_SHARE,
                stage_share=RELATION_STAGE_PROGRESS_SHARE,
                progress_callback=progress_callback,
                extractor=relationship_extractor,
            )

        relationships = self._normalize_relationship_extractions(
            graph_id,
            ontology,
            relation_payloads,
            entity_map,
        )
        if relationships:
            self.store.upsert_relationships(graph_id, relationships)

        if progress_callback:
            progress_callback(
                f"그래프에 엔티티 {len(entities)}개, 관계 {len(relationships)}개 반영됨",
                1.0,
            )

        return [f"chunk_{index + 1}" for index in range(len(chunks))]

    def _normalize_entity_extractions(
        self,
        graph_id: str,
        ontology: Dict[str, Any],
        payloads: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        entity_map: Dict[str, Dict[str, Any]] = {}

        for payload in payloads:
            raw_entities = payload.get("entities", []) or []
            chunk_text = self._clean_text(payload.get("_chunk_text", ""))

            for raw_entity in raw_entities:
                if not isinstance(raw_entity, dict):
                    continue
                entity_name = self._clean_text(raw_entity.get("name"))
                if not entity_name:
                    continue
                if self._is_generic_entity_name(entity_name, ontology):
                    continue
                if chunk_text and not self._text_mentions_candidate(chunk_text, entity_name):
                    continue
                entity_type = self._resolve_entity_type(raw_entity.get("type", ""), ontology)
                entity_uuid = self._canonical_entity_uuid(graph_id, entity_type, entity_name)
                attribute_names = self._ontology_attribute_names(ontology, entity_type)
                attributes = self._filter_entity_attributes(raw_entity.get("attributes"), attribute_names)
                summary = self._clean_text(raw_entity.get("summary"))
                labels = ["Entity", "Node", entity_type]
                aliases = self._entity_aliases(entity_name)

                existing = entity_map.get(entity_uuid)
                if existing:
                    merged_summary = summary if len(summary) > len(existing.get("summary", "")) else existing.get("summary", "")
                    merged_attributes = dict(existing.get("attributes", {}))
                    merged_attributes.update({k: v for k, v in attributes.items() if v not in (None, "", [])})
                    existing["summary"] = merged_summary
                    existing["attributes"] = merged_attributes
                    existing["labels"] = sorted(set(existing.get("labels", []) + labels))
                    existing["aliases"] = sorted(set(existing.get("aliases", []) + aliases))
                    continue

                entity_map[entity_uuid] = {
                    "uuid": entity_uuid,
                    "name": entity_name,
                    "entity_type": entity_type,
                    "labels": labels,
                    "summary": summary,
                    "attributes": attributes,
                    "aliases": aliases,
                }

        return entity_map

    def _normalize_relationship_extractions(
        self,
        graph_id: str,
        ontology: Dict[str, Any],
        payloads: List[Dict[str, Any]],
        entity_map: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        relationships: List[Dict[str, Any]] = []
        candidate_lookup = self._candidate_lookup(entity_map)

        for payload in payloads:
            raw_relationships = payload.get("relationships", []) or []
            chunk_text = self._clean_text(payload.get("_chunk_text", ""))

            for raw_relationship in raw_relationships:
                if not isinstance(raw_relationship, dict):
                    continue

                source_name = self._clean_text(raw_relationship.get("source_name"))
                target_name = self._clean_text(raw_relationship.get("target_name"))
                fact = self._clean_text(raw_relationship.get("fact"))

                if not source_name or not target_name or not fact:
                    continue
                if chunk_text:
                    if not self._text_mentions_candidate(chunk_text, source_name):
                        continue
                    if not self._text_mentions_candidate(chunk_text, target_name):
                        continue

                source_entity = self._resolve_candidate_entity(candidate_lookup, source_name)
                target_entity = self._resolve_candidate_entity(candidate_lookup, target_name)
                if not source_entity or not target_entity:
                    continue

                source_uuid = source_entity["uuid"]
                target_uuid = target_entity["uuid"]
                if source_uuid == target_uuid:
                    continue

                source_type = source_entity.get("entity_type") or self._resolve_entity_type("", ontology)
                target_type = target_entity.get("entity_type") or self._resolve_entity_type("", ontology)
                relation_type = self._resolve_edge_type(
                    raw_relationship.get("relation_type", ""),
                    source_type,
                    target_type,
                    ontology,
                )
                edge_uuid = self._canonical_edge_uuid(graph_id, source_uuid, relation_type, target_uuid, fact)

                relationships.append(
                    {
                        "edge_uuid": edge_uuid,
                        "name": relation_type,
                        "fact": fact,
                        "source_node_uuid": source_uuid,
                        "target_node_uuid": target_uuid,
                        "source_node_name": source_entity.get("name", ""),
                        "target_node_name": target_entity.get("name", ""),
                        "source_labels": source_entity.get("labels", []),
                        "target_labels": target_entity.get("labels", []),
                        "source_summary": source_entity.get("summary", ""),
                        "target_summary": target_entity.get("summary", ""),
                        "source_attributes": source_entity.get("attributes", {}),
                        "target_attributes": target_entity.get("attributes", {}),
                        "attributes": self._filter_entity_attributes(raw_relationship.get("attributes"), []),
                        "valid_at": self._coerce_temporal(raw_relationship.get("valid_at")),
                        "invalid_at": self._coerce_temporal(raw_relationship.get("invalid_at")),
                        "expired_at": self._coerce_temporal(raw_relationship.get("expired_at")),
                    }
                )

        return relationships

    def _wait_for_episodes(
        self,
        episode_uuids: List[str],
        progress_callback: Optional[Callable] = None,
        timeout: int = 600,
        initial_poll_delay: int = 0,
        poll_interval: int = 0,
    ):
        """
        이전 인터페이스와 호환됩니다.
        Neo4j 쓰기는 동기적으로 완료되므로, 여기서는 완료 상태만 반환합니다.
        """
        del episode_uuids, timeout, initial_poll_delay, poll_interval
        if progress_callback:
            progress_callback("그래프 데이터가 로컬 저장소에 작성됨", 1.0)

    def _get_graph_info(self, graph_id: str) -> GraphInfo:
        nodes = self.store.get_all_nodes(graph_id)
        edges = self.store.get_all_edges(graph_id)
        entity_types = set()
        for node in nodes:
            for label in node.get("labels", []) or []:
                if label not in ["Entity", "Node"]:
                    entity_types.add(label)

        return GraphInfo(
            graph_id=graph_id,
            node_count=len(nodes),
            edge_count=len(edges),
            entity_types=sorted(entity_types),
        )

    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """전체 그래프 데이터를 가져옵니다."""
        nodes_data = [
            node
            for node in self.store.get_all_nodes(graph_id)
            if not self._is_runtime_memory_node(node)
        ]
        edges_data = [
            edge
            for edge in self.store.get_all_edges(graph_id)
            if not self._is_runtime_memory_edge(edge)
        ]
        node_map = {node.get("uuid"): node.get("name", "") for node in nodes_data}

        normalized_edges: List[Dict[str, Any]] = []
        for edge in edges_data:
            normalized_edges.append(
                {
                    "uuid": edge.get("uuid", ""),
                    "name": edge.get("name", ""),
                    "fact": edge.get("fact", ""),
                    "fact_type": edge.get("name", ""),
                    "source_node_uuid": edge.get("source_node_uuid", ""),
                    "target_node_uuid": edge.get("target_node_uuid", ""),
                    "source_node_name": node_map.get(edge.get("source_node_uuid", ""), ""),
                    "target_node_name": node_map.get(edge.get("target_node_uuid", ""), ""),
                    "attributes": edge.get("attributes", {}) or {},
                    "created_at": edge.get("created_at"),
                    "valid_at": edge.get("valid_at"),
                    "invalid_at": edge.get("invalid_at"),
                    "expired_at": edge.get("expired_at"),
                    "episodes": edge.get("episodes", []) or [],
                }
            )

        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": normalized_edges,
            "node_count": len(nodes_data),
            "edge_count": len(normalized_edges),
        }

    def delete_graph(self, graph_id: str):
        """그래프를 삭제합니다."""
        self.store.delete_graph(graph_id)
