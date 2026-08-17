"""
엔티티 읽기 및 필터링 서비스.
기존 호출자와의 호환성을 위해 이전 클래스 이름을 유지하며, 내부적으로 Neo4j 로컬 그래프를 읽도록 변경되었습니다.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from ..utils.logger import get_logger
from .neo4j_graph_store import Neo4jGraphStore

logger = get_logger("tiresias.zep_entity_reader")


@dataclass
class EntityNode:
    """엔티티 노드 데이터 구조"""

    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    related_edges: List[Dict[str, Any]] = field(default_factory=list)
    related_nodes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes,
            "related_edges": self.related_edges,
            "related_nodes": self.related_nodes,
        }

    def get_entity_type(self) -> Optional[str]:
        for label in self.labels:
            if label not in ["Entity", "Node"]:
                return label
        return None


@dataclass
class FilteredEntities:
    """필터링된 엔티티 컬렉션"""

    entities: List[EntityNode]
    entity_types: Set[str]
    total_count: int
    filtered_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [entity.to_dict() for entity in self.entities],
            "entity_types": list(self.entity_types),
            "total_count": self.total_count,
            "filtered_count": self.filtered_count,
        }


class ZepEntityReader:
    """
    이전 인터페이스와 호환되는 엔티티 읽기 서비스.

    핵심 의미는 변경되지 않습니다:
    - 사용자 정의 타입 레이블이 있는 노드만 유지
    - enrich_with_edges=True일 때 related_edges / related_nodes를 보완
    """

    def __init__(self, api_key: Optional[str] = None, store: Optional[Neo4jGraphStore] = None):
        del api_key
        self.store = store or Neo4jGraphStore()

    @staticmethod
    def _custom_labels(labels: List[str]) -> List[str]:
        return [label for label in labels if label not in ["Entity", "Node"]]

    def _resolve_graph_id_for_node(self, node_uuid: str) -> Optional[str]:
        node = self.store.get_node(node_uuid)
        if not node:
            return None
        return node.get("graph_id")

    def get_all_nodes(self, graph_id: str) -> List[Dict[str, Any]]:
        logger.info(f"그래프 {graph_id}의 모든 노드 가져오기...")
        nodes = self.store.get_all_nodes(graph_id)
        logger.info(f"총 {len(nodes)}개 노드 가져옴")
        return nodes

    def get_all_edges(self, graph_id: str) -> List[Dict[str, Any]]:
        logger.info(f"그래프 {graph_id}의 모든 엣지 가져오기...")
        edges = self.store.get_all_edges(graph_id)
        logger.info(f"총 {len(edges)}개 엣지 가져옴")
        return edges

    def get_node_edges(self, node_uuid: str, graph_id: Optional[str] = None) -> List[Dict[str, Any]]:
        graph_id = graph_id or self._resolve_graph_id_for_node(node_uuid)
        if not graph_id:
            logger.warning(f"노드가 존재하지 않거나 graph_id가 없습니다: {node_uuid}")
            return []

        try:
            edges = self.store.get_node_edges(graph_id, node_uuid)
        except Exception as exc:
            logger.warning(f"노드 {node_uuid}의 엣지 가져오기 실패: {exc}")
            return []

        edges_data: List[Dict[str, Any]] = []
        for edge in edges:
            payload = {
                "uuid": edge.get("uuid", ""),
                "name": edge.get("name", ""),
                "fact": edge.get("fact", ""),
                "source_node_uuid": edge.get("source_node_uuid", ""),
                "target_node_uuid": edge.get("target_node_uuid", ""),
                "attributes": edge.get("attributes", {}) or {},
            }
            if edge.get("direction"):
                payload["direction"] = edge.get("direction")
            edges_data.append(payload)

        return edges_data

    def filter_defined_entities(
        self,
        graph_id: str,
        defined_entity_types: Optional[List[str]] = None,
        enrich_with_edges: bool = True,
    ) -> FilteredEntities:
        logger.info(f"그래프 {graph_id}의 엔티티 필터링 시작...")

        all_nodes = self.get_all_nodes(graph_id)
        total_count = len(all_nodes)
        all_edges = self.get_all_edges(graph_id) if enrich_with_edges else []
        node_map = {node["uuid"]: node for node in all_nodes}

        filtered_entities: List[EntityNode] = []
        entity_types_found: Set[str] = set()

        for node in all_nodes:
            labels = node.get("labels", []) or []
            custom_labels = self._custom_labels(labels)
            if not custom_labels:
                continue

            if defined_entity_types:
                matching_labels = [label for label in custom_labels if label in defined_entity_types]
                if not matching_labels:
                    continue
                entity_type = matching_labels[0]
            else:
                entity_type = custom_labels[0]

            entity_types_found.add(entity_type)

            entity = EntityNode(
                uuid=node.get("uuid", ""),
                name=node.get("name", ""),
                labels=labels,
                summary=node.get("summary", ""),
                attributes=node.get("attributes", {}) or {},
            )

            if enrich_with_edges:
                related_edges: List[Dict[str, Any]] = []
                related_node_uuids: Set[str] = set()

                for edge in all_edges:
                    source_uuid = edge.get("source_node_uuid", "")
                    target_uuid = edge.get("target_node_uuid", "")
                    if source_uuid == entity.uuid:
                        related_edges.append(
                            {
                                "direction": "outgoing",
                                "edge_name": edge.get("name", ""),
                                "fact": edge.get("fact", ""),
                                "target_node_uuid": target_uuid,
                            }
                        )
                        if target_uuid:
                            related_node_uuids.add(target_uuid)
                    elif target_uuid == entity.uuid:
                        related_edges.append(
                            {
                                "direction": "incoming",
                                "edge_name": edge.get("name", ""),
                                "fact": edge.get("fact", ""),
                                "source_node_uuid": source_uuid,
                            }
                        )
                        if source_uuid:
                            related_node_uuids.add(source_uuid)

                entity.related_edges = related_edges
                entity.related_nodes = [
                    {
                        "uuid": related_node.get("uuid", ""),
                        "name": related_node.get("name", ""),
                        "labels": related_node.get("labels", []) or [],
                        "summary": related_node.get("summary", ""),
                    }
                    for related_uuid in related_node_uuids
                    if (related_node := node_map.get(related_uuid))
                ]

            filtered_entities.append(entity)

        logger.info(
            f"필터링 완료: 총 노드 {total_count}, 조건 일치 {len(filtered_entities)}, 엔티티 타입: {entity_types_found}"
        )

        return FilteredEntities(
            entities=filtered_entities,
            entity_types=entity_types_found,
            total_count=total_count,
            filtered_count=len(filtered_entities),
        )

    def get_entity_with_context(self, graph_id: str, entity_uuid: str) -> Optional[EntityNode]:
        try:
            node = self.store.get_node(entity_uuid)
            if not node or node.get("graph_id") != graph_id:
                return None

            edges = self.get_node_edges(entity_uuid, graph_id)
            all_nodes = self.get_all_nodes(graph_id)
            node_map = {item["uuid"]: item for item in all_nodes}

            related_edges: List[Dict[str, Any]] = []
            related_node_uuids: Set[str] = set()

            for edge in edges:
                source_uuid = edge.get("source_node_uuid", "")
                target_uuid = edge.get("target_node_uuid", "")
                if source_uuid == entity_uuid:
                    related_edges.append(
                        {
                            "direction": "outgoing",
                            "edge_name": edge.get("name", ""),
                            "fact": edge.get("fact", ""),
                            "target_node_uuid": target_uuid,
                        }
                    )
                    if target_uuid:
                        related_node_uuids.add(target_uuid)
                else:
                    related_edges.append(
                        {
                            "direction": "incoming",
                            "edge_name": edge.get("name", ""),
                            "fact": edge.get("fact", ""),
                            "source_node_uuid": source_uuid,
                        }
                    )
                    if source_uuid:
                        related_node_uuids.add(source_uuid)

            related_nodes = [
                {
                    "uuid": related_node.get("uuid", ""),
                    "name": related_node.get("name", ""),
                    "labels": related_node.get("labels", []) or [],
                    "summary": related_node.get("summary", ""),
                }
                for related_uuid in related_node_uuids
                if (related_node := node_map.get(related_uuid))
            ]

            return EntityNode(
                uuid=node.get("uuid", ""),
                name=node.get("name", ""),
                labels=node.get("labels", []) or [],
                summary=node.get("summary", ""),
                attributes=node.get("attributes", {}) or {},
                related_edges=related_edges,
                related_nodes=related_nodes,
            )
        except Exception as exc:
            logger.error(f"엔티티 {entity_uuid} 가져오기 실패: {exc}")
            return None

    def get_entities_by_type(
        self,
        graph_id: str,
        entity_type: str,
        enrich_with_edges: bool = True,
    ) -> List[EntityNode]:
        result = self.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=[entity_type],
            enrich_with_edges=enrich_with_edges,
        )
        return result.entities