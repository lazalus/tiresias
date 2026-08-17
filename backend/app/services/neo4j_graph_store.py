"""
Neo4j-backed graph storage layer.

This module provides a generic, property-based storage abstraction that keeps the
existing graph_id namespace while avoiding dynamic Cypher labels. It stores all
graph entities under a single generic node label and all relationships under a
single generic relationship type.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

try:
    from neo4j import GraphDatabase, Driver
except Exception:  # pragma: no cover - import guard for environments without neo4j
    GraphDatabase = None  # type: ignore[assignment]
    Driver = Any  # type: ignore[assignment]

from ..utils.logger import get_logger

logger = get_logger("tiresias.neo4j_graph_store")


class Neo4jGraphStore:
    """Generic graph storage backed by Neo4j."""

    _driver: Optional[Driver] = None
    _driver_lock = threading.Lock()
    _schema_ready = False

    GRAPH_META_LABEL = "GraphMeta"
    GRAPH_ONTOLOGY_LABEL = "GraphOntology"
    GRAPH_NODE_LABEL = "GraphNode"
    GRAPH_ACTIVITY_LABEL = "GraphActivity"
    MEMORY_SUMMARY_LABEL = "MemorySummary"
    SIMULATION_ACTIVITY_LABEL = "SimulationActivity"
    RELATED_RELATIONSHIP = "RELATED"

    NODE_FULLTEXT_INDEX = "graph_node_fulltext"
    REL_FULLTEXT_INDEX = "graph_relationship_fulltext"
    MEMORY_FULLTEXT_INDEX = "graph_memory_summary_fulltext"
    SEARCH_STOPWORDS = {
        "about",
        "all",
        "analysis",
        "and",
        "background",
        "context",
        "event",
        "events",
        "for",
        "how",
        "info",
        "information",
        "of",
        "on",
        "or",
        "please",
        "query",
        "relation",
        "relations",
        "relationship",
        "relationships",
        "scene",
        "simulation",
        "the",
        "what",
        "with",
        "대하여",
        "정보",
        "관계",
        "배경",
        "사건",
        "활동",
        "모든",
        "전부",
        "분석",
        "시뮬레이션",
        "관련",
        "대한",
        "대해",
        "모든",
        "정보",
        "관계",
        "배경",
        "사건",
        "활동",
        "분석",
        "시뮬레이션",
        "관련",
    }
    KOREAN_POSTPOSITIONS = (
        "으로",
        "에서",
        "에게",
        "까지",
        "부터",
        "께서",
        "처럼",
        "으로는",
        "으로도",
        "은",
        "는",
        "이",
        "가",
        "을",
        "를",
        "의",
        "와",
        "과",
        "도",
        "에",
        "로",
        "랑",
        "만",
    )

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ) -> None:
        if GraphDatabase is None:
            raise ImportError(
                "neo4j Python driver is not installed. Install the `neo4j` package first."
            )

        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.environ.get("NEO4J_USERNAME", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD", "neo4j")
        self.database = database or os.environ.get("NEO4J_DATABASE", "neo4j")

        self._ensure_driver()
        self.ensure_schema()

    @classmethod
    def _ensure_driver(cls, uri: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None) -> Driver:
        with cls._driver_lock:
            if cls._driver is not None:
                return cls._driver

            if GraphDatabase is None:
                raise ImportError(
                    "neo4j Python driver is not installed. Install the `neo4j` package first."
                )

            resolved_uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
            resolved_username = username or os.environ.get("NEO4J_USERNAME", "neo4j")
            resolved_password = password or os.environ.get("NEO4J_PASSWORD", "neo4j")

            cls._driver = GraphDatabase.driver(
                resolved_uri,
                auth=(resolved_username, resolved_password),
            )
            return cls._driver

    @classmethod
    def _get_driver(cls) -> Driver:
        if cls._driver is None:
            return cls._ensure_driver()
        return cls._driver

    @classmethod
    def close_driver(cls) -> None:
        with cls._driver_lock:
            if cls._driver is not None:
                try:
                    cls._driver.close()
                finally:
                    cls._driver = None
                    cls._schema_ready = False

    def close(self) -> None:
        self.close_driver()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _to_mapping(value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return dict(value)
        if dataclasses.is_dataclass(value):
            return dataclasses.asdict(value)
        if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
            try:
                result = value.to_dict()
                if isinstance(result, dict):
                    return dict(result)
            except Exception:
                pass
        if hasattr(value, "__dict__"):
            return {k: v for k, v in vars(value).items() if not k.startswith("_")}
        raise TypeError(f"Unsupported item type: {type(value)!r}")

    @staticmethod
    def _normalize_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    @staticmethod
    def _normalize_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        text = str(value).strip()
        return [text] if text else []

    @staticmethod
    def _normalize_attributes(value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return {}
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    return parsed
                return {"value": parsed}
            except Exception:
                return {"value": raw}
        if dataclasses.is_dataclass(value):
            return dataclasses.asdict(value)
        if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
            try:
                result = value.to_dict()
                if isinstance(result, dict):
                    return dict(result)
            except Exception:
                pass
        if hasattr(value, "__dict__"):
            return {k: v for k, v in vars(value).items() if not k.startswith("_")}
        return {"value": str(value)}

    @staticmethod
    def _json_dumps(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)

    @staticmethod
    def _json_loads(raw: Any, default: Any = None) -> Any:
        if raw is None:
            return default
        if isinstance(raw, (dict, list, int, float, bool)):
            return raw
        if not isinstance(raw, str):
            return default
        try:
            return json.loads(raw)
        except Exception:
            return default

    @staticmethod
    def _record_properties(value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return dict(value)
        items = getattr(value, "items", None)
        if callable(items):
            try:
                return {key: item for key, item in items()}
            except Exception:
                pass
        properties = getattr(value, "_properties", None)
        if isinstance(properties, dict):
            return dict(properties)
        try:
            return dict(value)
        except Exception:
            return {}

    @staticmethod
    def _build_search_text(parts: Sequence[Any]) -> str:
        flattened: List[str] = []
        for part in parts:
            if part is None:
                continue
            if isinstance(part, (list, tuple, set)):
                flattened.extend(Neo4jGraphStore._build_search_text(part).split())
                continue
            if isinstance(part, dict):
                flattened.append(Neo4jGraphStore._json_dumps(part))
                continue
            text = str(part).strip()
            if text:
                flattened.append(text)
        return " ".join(flattened).strip()

    @classmethod
    def _has_label(cls, labels: Sequence[str], label: str) -> bool:
        return label in set(labels or [])

    @classmethod
    def _normalize_query(cls, query: str) -> str:
        return re.sub(r"\s+", " ", cls._normalize_text(query)).strip()

    @classmethod
    def _strip_korean_postposition(cls, token: str) -> str:
        for suffix in cls.KOREAN_POSTPOSITIONS:
            if token.endswith(suffix) and len(token) > len(suffix) + 1:
                return token[: -len(suffix)]
        return token

    @classmethod
    def _extract_focus_query(cls, query: str) -> str:
        simplified = cls._normalize_query(query)
        wrapper_patterns = [
            r"^(?P<focus>.+?)에 대한 모든 정보.*$",
            r"^(?P<focus>.+?)에 대한.*$",
            r"^(?P<focus>.+?)에 대한 모든 정보.*$",
            r"^(?P<focus>.+?)에 대한.*$",
            r"^all information about (?P<focus>.+)$",
            r"^information about (?P<focus>.+)$",
        ]
        for pattern in wrapper_patterns:
            match = re.match(pattern, simplified, flags=re.IGNORECASE)
            if match:
                focus = cls._normalize_query(match.group("focus"))
                if focus:
                    return focus
        return simplified

    @classmethod
    def _tokenize_query(cls, query: str) -> List[str]:
        base_query = cls._extract_focus_query(query)
        raw_tokens = re.findall(r"[0-9A-Za-z\u00C0-\u024F\u0400-\u04FF\u3040-\u30FF\u3400-\u4DBF\u4E00-\u9FFF\uAC00-\uD7AF_]+", base_query.lower())
        tokens: List[str] = []
        seen: set[str] = set()

        def add_token(token: str) -> None:
            normalized = token.strip().lower()
            if len(normalized) < 2 and not normalized.isdigit():
                return
            if normalized in cls.SEARCH_STOPWORDS:
                return
            if normalized not in seen:
                seen.add(normalized)
                tokens.append(normalized)

        for token in raw_tokens:
            add_token(token)
            stripped = cls._strip_korean_postposition(token)
            if stripped != token:
                add_token(stripped)

        if not tokens and base_query:
            add_token(base_query.lower())

        return tokens[:12]

    @staticmethod
    def _escape_lucene_term(term: str) -> str:
        return re.sub(r'([+\-!(){}\[\]^"~*?:\\/|&])', r"\\\1", term)

    @classmethod
    def _build_fulltext_queries(cls, query: str) -> List[str]:
        normalized_query = cls._normalize_query(query)
        focus_query = cls._extract_focus_query(query)
        tokens = cls._tokenize_query(query)
        queries: List[str] = []

        def add(candidate: str) -> None:
            cleaned = candidate.strip()
            if cleaned and cleaned not in queries:
                queries.append(cleaned)

        if normalized_query:
            add(f'"{cls._escape_lucene_term(normalized_query)}"')
        if focus_query and focus_query != normalized_query:
            add(f'"{cls._escape_lucene_term(focus_query)}"')
        if tokens:
            parts = [f"{cls._escape_lucene_term(token)}^3" for token in tokens]
            wildcard_parts = [
                f"{cls._escape_lucene_term(token)}*"
                for token in tokens
                if len(token) >= 4 and not any(ch.isdigit() for ch in token)
            ]
            add(" OR ".join(parts + wildcard_parts))

        return queries

    @staticmethod
    def _first_custom_label(labels: Sequence[str]) -> Optional[str]:
        for label in labels:
            if label not in {"Entity", "Node", Neo4jGraphStore.GRAPH_NODE_LABEL}:
                return label
        return None

    def _session(self):
        driver = self._get_driver()
        return driver.session(database=self.database)

    def _run_read(self, cypher: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        parameters = parameters or {}
        with self._session() as session:
            result = session.run(cypher, parameters)
            return [record.data() for record in result]

    def _run_write(self, cypher: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        parameters = parameters or {}
        with self._session() as session:
            result = session.run(cypher, parameters)
            return [record.data() for record in result]

    def ensure_schema(self) -> None:
        if self.__class__._schema_ready:
            return

        statements = [
            f"""
            CREATE CONSTRAINT graph_meta_graph_id IF NOT EXISTS
            FOR (g:{self.GRAPH_META_LABEL})
            REQUIRE g.graph_id IS UNIQUE
            """,
            f"""
            CREATE CONSTRAINT graph_ontology_graph_id IF NOT EXISTS
            FOR (o:{self.GRAPH_ONTOLOGY_LABEL})
            REQUIRE o.graph_id IS UNIQUE
            """,
            f"""
            CREATE CONSTRAINT graph_node_identity IF NOT EXISTS
            FOR (n:{self.GRAPH_NODE_LABEL})
            REQUIRE (n.graph_id, n.uuid) IS UNIQUE
            """,
            f"""
            CREATE CONSTRAINT graph_activity_identity IF NOT EXISTS
            FOR (a:{self.GRAPH_ACTIVITY_LABEL})
            REQUIRE (a.graph_id, a.activity_id) IS UNIQUE
            """,
            f"""
            CREATE CONSTRAINT memory_summary_identity IF NOT EXISTS
            FOR (m:{self.MEMORY_SUMMARY_LABEL})
            REQUIRE (m.graph_id, m.summary_id) IS UNIQUE
            """,
            f"""
            CREATE INDEX graph_node_graph_id IF NOT EXISTS
            FOR (n:{self.GRAPH_NODE_LABEL})
            ON (n.graph_id)
            """,
            f"""
            CREATE INDEX graph_activity_graph_id IF NOT EXISTS
            FOR (a:{self.GRAPH_ACTIVITY_LABEL})
            ON (a.graph_id)
            """,
            f"""
            CREATE INDEX memory_summary_graph_id IF NOT EXISTS
            FOR (m:{self.MEMORY_SUMMARY_LABEL})
            ON (m.graph_id)
            """,
            f"""
            CREATE INDEX memory_summary_simulation_id IF NOT EXISTS
            FOR (m:{self.MEMORY_SUMMARY_LABEL})
            ON (m.simulation_id)
            """,
        ]

        fulltext_statements = [
            f"""
            CREATE FULLTEXT INDEX {self.NODE_FULLTEXT_INDEX} IF NOT EXISTS
            FOR (n:{self.GRAPH_NODE_LABEL})
            ON EACH [n.name, n.summary, n.search_text]
            """,
            f"""
            CREATE FULLTEXT INDEX {self.REL_FULLTEXT_INDEX} IF NOT EXISTS
            FOR ()-[r:{self.RELATED_RELATIONSHIP}]-()
            ON EACH [r.name, r.fact, r.search_text]
            """,
            f"""
            CREATE FULLTEXT INDEX {self.MEMORY_FULLTEXT_INDEX} IF NOT EXISTS
            FOR (m:{self.MEMORY_SUMMARY_LABEL})
            ON EACH [m.title, m.summary, m.search_text]
            """,
        ]

        with self._session() as session:
            for statement in statements:
                session.run(statement)

            for statement in fulltext_statements:
                try:
                    session.run(statement)
                except Exception as exc:
                    logger.warning("Fulltext index creation skipped: %s", exc)

        self.__class__._schema_ready = True

    def create_graph(self, graph_id: str, name: str, description: str = "") -> Dict[str, Any]:
        now = self._now_iso()
        query = f"""
        MERGE (g:{self.GRAPH_META_LABEL} {{graph_id: $graph_id}})
        ON CREATE SET
            g.name = $name,
            g.description = $description,
            g.created_at = $now,
            g.updated_at = $now,
            g.ontology_json = NULL
        ON MATCH SET
            g.name = CASE WHEN $name = '' THEN g.name ELSE $name END,
            g.description = CASE WHEN $description = '' THEN g.description ELSE $description END,
            g.updated_at = $now
        RETURN g.graph_id AS graph_id, g.name AS name, g.description AS description,
               g.created_at AS created_at, g.updated_at AS updated_at
        """
        rows = self._run_write(query, {"graph_id": graph_id, "name": name, "description": description, "now": now})
        return rows[0] if rows else {"graph_id": graph_id, "name": name, "description": description}

    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]) -> Dict[str, Any]:
        ontology = ontology or {}
        now = self._now_iso()
        ontology_json = self._json_dumps(ontology)
        search_text = self._build_search_text(
            [
                ontology.get("analysis_summary", ""),
                ontology.get("entity_types", []),
                ontology.get("edge_types", []),
            ]
        )
        query = f"""
        MERGE (g:{self.GRAPH_META_LABEL} {{graph_id: $graph_id}})
        ON CREATE SET
            g.created_at = $now,
            g.name = coalesce(g.name, $graph_id)
        SET g.updated_at = $now,
            g.has_ontology = true
        MERGE (o:{self.GRAPH_ONTOLOGY_LABEL} {{graph_id: $graph_id}})
        SET o.ontology_json = $ontology_json,
            o.search_text = $search_text,
            o.updated_at = $now,
            o.created_at = coalesce(o.created_at, $now)
        RETURN o.graph_id AS graph_id, o.ontology_json AS ontology_json, o.created_at AS created_at, o.updated_at AS updated_at
        """
        rows = self._run_write(
            query,
            {
                "graph_id": graph_id,
                "ontology_json": ontology_json,
                "search_text": search_text,
                "now": now,
            },
        )
        return {
            "graph_id": graph_id,
            "ontology": ontology,
            "stored_at": now,
            "raw": rows[0] if rows else None,
        }

    def get_ontology(self, graph_id: str) -> Optional[Dict[str, Any]]:
        query = f"""
        MATCH (o:{self.GRAPH_ONTOLOGY_LABEL} {{graph_id: $graph_id}})
        RETURN o.ontology_json AS ontology_json
        LIMIT 1
        """
        rows = self._run_read(query, {"graph_id": graph_id})
        if not rows:
            query = f"""
            MATCH (g:{self.GRAPH_META_LABEL} {{graph_id: $graph_id}})
            RETURN g.ontology_json AS ontology_json
            LIMIT 1
            """
            rows = self._run_read(query, {"graph_id": graph_id})

        if not rows:
            return None
        return self._json_loads(rows[0].get("ontology_json"), default=None)

    def upsert_entities(self, graph_id: str, entities: Sequence[Any]) -> Dict[str, Any]:
        now = self._now_iso()
        normalized: List[Dict[str, Any]] = []

        for entity in entities or []:
            data = self._to_mapping(entity)
            entity_uuid = self._normalize_text(data.get("uuid") or data.get("uuid_") or data.get("id") or uuid.uuid4().hex)
            labels = self._normalize_list(data.get("labels"))
            name = self._normalize_text(data.get("name") or entity_uuid)
            summary = self._normalize_text(data.get("summary"))
            attributes = self._normalize_attributes(data.get("attributes"))
            attributes_json = self._json_dumps(attributes)
            search_text = self._build_search_text(
                [
                    graph_id,
                    entity_uuid,
                    name,
                    summary,
                    labels,
                    attributes,
                    data.get("entity_type"),
                    data.get("type"),
                ]
            )
            normalized.append(
                {
                    "uuid": entity_uuid,
                    "name": name,
                    "labels": labels,
                    "summary": summary,
                    "attributes": attributes,
                    "attributes_json": attributes_json,
                    "search_text": search_text,
                    "created_at": self._normalize_text(data.get("created_at") or now),
                    "updated_at": self._normalize_text(data.get("updated_at") or now),
                }
            )

        query = f"""
        UNWIND $entities AS entity
        MERGE (n:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id, uuid: entity.uuid}})
        ON CREATE SET
            n.created_at = entity.created_at
        SET
            n.name = entity.name,
            n.labels = CASE WHEN size(entity.labels) = 0 THEN coalesce(n.labels, []) ELSE entity.labels END,
            n.summary = entity.summary,
            n.attributes_json = entity.attributes_json,
            n.search_text = entity.search_text,
            n.updated_at = entity.updated_at,
            n.graph_id = $graph_id
        RETURN n.uuid AS uuid
        """
        self._run_write(query, {"graph_id": graph_id, "entities": normalized})
        return {"graph_id": graph_id, "count": len(normalized), "entities": normalized}

    def upsert_relationships(self, graph_id: str, relationships: Sequence[Any]) -> Dict[str, Any]:
        now = self._now_iso()
        normalized: List[Dict[str, Any]] = []

        for relationship in relationships or []:
            data = self._to_mapping(relationship)
            edge_uuid = self._normalize_text(data.get("edge_uuid") or data.get("uuid") or uuid.uuid4().hex)
            source_uuid = self._normalize_text(data.get("source_node_uuid") or data.get("source_uuid") or data.get("source"))
            target_uuid = self._normalize_text(data.get("target_node_uuid") or data.get("target_uuid") or data.get("target"))
            if not source_uuid or not target_uuid:
                continue

            source_name = self._normalize_text(data.get("source_node_name") or data.get("source_name"))
            target_name = self._normalize_text(data.get("target_node_name") or data.get("target_name"))
            name = self._normalize_text(data.get("name") or data.get("edge_name") or data.get("relation_type") or "RELATED")
            fact = self._normalize_text(data.get("fact") or data.get("summary") or data.get("description"))
            attributes = self._normalize_attributes(data.get("attributes"))
            attributes_json = self._json_dumps(attributes)

            source_labels = self._normalize_list(data.get("source_labels"))
            target_labels = self._normalize_list(data.get("target_labels"))

            source_search_text = self._build_search_text(
                [graph_id, source_uuid, source_name, data.get("source_summary"), source_labels, data.get("source_attributes"), fact]
            )
            target_search_text = self._build_search_text(
                [graph_id, target_uuid, target_name, data.get("target_summary"), target_labels, data.get("target_attributes"), fact]
            )
            search_text = self._build_search_text(
                [
                    graph_id,
                    edge_uuid,
                    name,
                    fact,
                    source_uuid,
                    source_name,
                    target_uuid,
                    target_name,
                    attributes,
                ]
            )

            normalized.append(
                {
                    "edge_uuid": edge_uuid,
                    "source_node_uuid": source_uuid,
                    "target_node_uuid": target_uuid,
                    "source_node_name": source_name,
                    "target_node_name": target_name,
                    "name": name,
                    "fact": fact,
                    "attributes_json": attributes_json,
                    "search_text": search_text,
                    "source_labels": source_labels,
                    "target_labels": target_labels,
                    "source_summary": self._normalize_text(data.get("source_summary")),
                    "target_summary": self._normalize_text(data.get("target_summary")),
                    "source_attributes_json": self._json_dumps(self._normalize_attributes(data.get("source_attributes"))),
                    "target_attributes_json": self._json_dumps(self._normalize_attributes(data.get("target_attributes"))),
                    "source_search_text": source_search_text,
                    "target_search_text": target_search_text,
                    "created_at": self._normalize_text(data.get("created_at") or now),
                    "valid_at": self._normalize_text(data.get("valid_at")),
                    "invalid_at": self._normalize_text(data.get("invalid_at")),
                    "expired_at": self._normalize_text(data.get("expired_at")),
                    "updated_at": self._normalize_text(data.get("updated_at") or now),
                }
            )

        query = f"""
        UNWIND $relationships AS rel
        MERGE (s:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id, uuid: rel.source_node_uuid}})
        ON CREATE SET
            s.name = CASE WHEN rel.source_node_name = '' THEN rel.source_node_uuid ELSE rel.source_node_name END,
            s.labels = CASE WHEN size(rel.source_labels) = 0 THEN ['{self.GRAPH_NODE_LABEL}'] ELSE rel.source_labels END,
            s.summary = CASE WHEN rel.source_summary = '' THEN '' ELSE rel.source_summary END,
            s.attributes_json = CASE WHEN rel.source_attributes_json = '' THEN '{{}}' ELSE rel.source_attributes_json END,
            s.search_text = CASE WHEN rel.source_search_text = '' THEN rel.source_node_uuid ELSE rel.source_search_text END,
            s.created_at = rel.created_at,
            s.updated_at = rel.updated_at
        SET
            s.name = CASE WHEN rel.source_node_name = '' THEN s.name ELSE rel.source_node_name END,
            s.labels = CASE WHEN size(rel.source_labels) = 0 THEN coalesce(s.labels, ['{self.GRAPH_NODE_LABEL}']) ELSE rel.source_labels END,
            s.summary = CASE WHEN rel.source_summary = '' THEN coalesce(s.summary, '') ELSE rel.source_summary END,
            s.attributes_json = CASE WHEN rel.source_attributes_json = '' THEN coalesce(s.attributes_json, '{{}}') ELSE rel.source_attributes_json END,
            s.search_text = CASE WHEN rel.source_search_text = '' THEN coalesce(s.search_text, s.name) ELSE rel.source_search_text END,
            s.updated_at = rel.updated_at,
            s.graph_id = $graph_id
        MERGE (t:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id, uuid: rel.target_node_uuid}})
        ON CREATE SET
            t.name = CASE WHEN rel.target_node_name = '' THEN rel.target_node_uuid ELSE rel.target_node_name END,
            t.labels = CASE WHEN size(rel.target_labels) = 0 THEN ['{self.GRAPH_NODE_LABEL}'] ELSE rel.target_labels END,
            t.summary = CASE WHEN rel.target_summary = '' THEN '' ELSE rel.target_summary END,
            t.attributes_json = CASE WHEN rel.target_attributes_json = '' THEN '{{}}' ELSE rel.target_attributes_json END,
            t.search_text = CASE WHEN rel.target_search_text = '' THEN rel.target_node_uuid ELSE rel.target_search_text END,
            t.created_at = rel.created_at,
            t.updated_at = rel.updated_at
        SET
            t.name = CASE WHEN rel.target_node_name = '' THEN t.name ELSE rel.target_node_name END,
            t.labels = CASE WHEN size(rel.target_labels) = 0 THEN coalesce(t.labels, ['{self.GRAPH_NODE_LABEL}']) ELSE rel.target_labels END,
            t.summary = CASE WHEN rel.target_summary = '' THEN coalesce(t.summary, '') ELSE rel.target_summary END,
            t.attributes_json = CASE WHEN rel.target_attributes_json = '' THEN coalesce(t.attributes_json, '{{}}') ELSE rel.target_attributes_json END,
            t.search_text = CASE WHEN rel.target_search_text = '' THEN coalesce(t.search_text, t.name) ELSE rel.target_search_text END,
            t.updated_at = rel.updated_at,
            t.graph_id = $graph_id
        MERGE (s)-[r:{self.RELATED_RELATIONSHIP} {{graph_id: $graph_id, edge_uuid: rel.edge_uuid}}]->(t)
        SET
            r.name = rel.name,
            r.fact = rel.fact,
            r.attributes_json = rel.attributes_json,
            r.search_text = rel.search_text,
            r.created_at = coalesce(r.created_at, rel.created_at),
            r.valid_at = rel.valid_at,
            r.invalid_at = rel.invalid_at,
            r.expired_at = rel.expired_at,
            r.updated_at = rel.updated_at,
            r.source_node_uuid = rel.source_node_uuid,
            r.target_node_uuid = rel.target_node_uuid,
            r.source_node_name = rel.source_node_name,
            r.target_node_name = rel.target_node_name
        RETURN r.edge_uuid AS edge_uuid
        """
        self._run_write(query, {"graph_id": graph_id, "relationships": normalized})
        return {"graph_id": graph_id, "count": len(normalized), "relationships": normalized}

    def get_all_nodes(self, graph_id: str, simulation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        simulation_id = self._normalize_text(simulation_id)
        query = f"""
        MATCH (n:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id}})
        WHERE $simulation_id = '' OR coalesce(n.simulation_id, '') = '' OR n.simulation_id = $simulation_id
        RETURN n
        ORDER BY coalesce(n.updated_at, n.created_at, n.name, n.uuid)
        """
        rows = self._run_read(query, {"graph_id": graph_id, "simulation_id": simulation_id})
        result: List[Dict[str, Any]] = []
        for row in rows:
            node = row.get("n", {})
            if not node:
                continue
            properties = self._record_properties(node)
            labels = self._normalize_list(properties.get("labels"))
            attributes = self._json_loads(properties.get("attributes_json"), default={})
            result.append(
                {
                    "uuid": properties.get("uuid", ""),
                    "name": properties.get("name", ""),
                    "labels": labels,
                    "summary": properties.get("summary", ""),
                    "attributes": attributes if isinstance(attributes, dict) else {},
                    "graph_id": properties.get("graph_id", graph_id),
                    "created_at": properties.get("created_at"),
                    "updated_at": properties.get("updated_at"),
                    "search_text": properties.get("search_text", ""),
                    "simulation_id": properties.get("simulation_id"),
                    "is_runtime_memory": bool(properties.get("is_runtime_memory")),
                    "entity_type": self._first_custom_label(labels),
                }
            )
        return result

    def get_all_edges(self, graph_id: str, simulation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        simulation_id = self._normalize_text(simulation_id)
        query = f"""
        MATCH (s:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id}})-[r:{self.RELATED_RELATIONSHIP} {{graph_id: $graph_id}}]->(t:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id}})
        WHERE $simulation_id = '' OR coalesce(r.simulation_id, '') = '' OR r.simulation_id = $simulation_id
        RETURN properties(r) AS r, properties(s) AS s, properties(t) AS t
        ORDER BY coalesce(r.updated_at, r.created_at, r.name, r.edge_uuid)
        """
        rows = self._run_read(query, {"graph_id": graph_id, "simulation_id": simulation_id})
        result: List[Dict[str, Any]] = []
        for row in rows:
            rel = row.get("r", {})
            source = row.get("s", {})
            target = row.get("t", {})
            if not rel:
                continue
            rel_props = self._record_properties(rel)
            source_props = self._record_properties(source)
            target_props = self._record_properties(target)
            result.append(
                {
                    "uuid": rel_props.get("edge_uuid", rel_props.get("uuid", "")),
                    "name": rel_props.get("name", ""),
                    "fact": rel_props.get("fact", ""),
                    "source_node_uuid": rel_props.get("source_node_uuid") or source_props.get("uuid", ""),
                    "target_node_uuid": rel_props.get("target_node_uuid") or target_props.get("uuid", ""),
                    "source_node_name": rel_props.get("source_node_name") or source_props.get("name", ""),
                    "target_node_name": rel_props.get("target_node_name") or target_props.get("name", ""),
                    "attributes": self._json_loads(rel_props.get("attributes_json"), default={}) or {},
                    "graph_id": rel_props.get("graph_id", graph_id),
                    "created_at": rel_props.get("created_at"),
                    "updated_at": rel_props.get("updated_at"),
                    "valid_at": rel_props.get("valid_at"),
                    "invalid_at": rel_props.get("invalid_at"),
                    "expired_at": rel_props.get("expired_at"),
                    "search_text": rel_props.get("search_text", ""),
                    "simulation_id": rel_props.get("simulation_id"),
                    "is_runtime_memory": bool(rel_props.get("is_runtime_memory")),
                }
            )
        return result

    def get_node(self, node_uuid: str) -> Optional[Dict[str, Any]]:
        query = f"""
        MATCH (n:{self.GRAPH_NODE_LABEL} {{uuid: $node_uuid}})
        RETURN n
        ORDER BY coalesce(n.updated_at, n.created_at) DESC
        LIMIT 1
        """
        rows = self._run_read(query, {"node_uuid": node_uuid})
        if not rows:
            return None
        node = rows[0].get("n", {})
        if not node:
            return None
        properties = self._record_properties(node)
        labels = self._normalize_list(properties.get("labels"))
        attributes = self._json_loads(properties.get("attributes_json"), default={})
        return {
            "uuid": properties.get("uuid", ""),
            "name": properties.get("name", ""),
            "labels": labels,
            "summary": properties.get("summary", ""),
            "attributes": attributes if isinstance(attributes, dict) else {},
            "graph_id": properties.get("graph_id", ""),
            "created_at": properties.get("created_at"),
            "updated_at": properties.get("updated_at"),
            "search_text": properties.get("search_text", ""),
            "simulation_id": properties.get("simulation_id"),
            "is_runtime_memory": bool(properties.get("is_runtime_memory")),
            "entity_type": self._first_custom_label(labels),
        }

    def get_node_edges(self, graph_id: str, node_uuid: str, simulation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        simulation_id = self._normalize_text(simulation_id)
        query = f"""
        MATCH (n:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id, uuid: $node_uuid}})-[r:{self.RELATED_RELATIONSHIP} {{graph_id: $graph_id}}]-(other:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id}})
        WHERE $simulation_id = '' OR coalesce(r.simulation_id, '') = '' OR r.simulation_id = $simulation_id
        RETURN properties(r) AS r, properties(n) AS n, properties(other) AS other,
               CASE WHEN startNode(r).uuid = n.uuid THEN 'outgoing' ELSE 'incoming' END AS direction
        ORDER BY coalesce(r.updated_at, r.created_at, r.name, r.edge_uuid)
        """
        rows = self._run_read(query, {"graph_id": graph_id, "node_uuid": node_uuid, "simulation_id": simulation_id})
        result: List[Dict[str, Any]] = []
        for row in rows:
            rel = row.get("r", {})
            rel_props = self._record_properties(rel)
            current = row.get("n", {})
            current_props = self._record_properties(current)
            other = row.get("other", {})
            other_props = self._record_properties(other)
            direction = row.get("direction", "outgoing")
            edge_payload = {
                "uuid": rel_props.get("edge_uuid", rel_props.get("uuid", "")),
                "name": rel_props.get("name", ""),
                "fact": rel_props.get("fact", ""),
                "source_node_uuid": rel_props.get("source_node_uuid") or (node_uuid if direction == "outgoing" else other_props.get("uuid", "")),
                "target_node_uuid": rel_props.get("target_node_uuid") or (other_props.get("uuid", "") if direction == "outgoing" else node_uuid),
                "source_node_name": rel_props.get("source_node_name") or (current_props.get("name", "") if direction == "outgoing" else other_props.get("name", "")),
                "target_node_name": rel_props.get("target_node_name") or (other_props.get("name", "") if direction == "outgoing" else current_props.get("name", "")),
                "attributes": self._json_loads(rel_props.get("attributes_json"), default={}) or {},
                "graph_id": rel_props.get("graph_id", graph_id),
                "created_at": rel_props.get("created_at"),
                "updated_at": rel_props.get("updated_at"),
                "valid_at": rel_props.get("valid_at"),
                "invalid_at": rel_props.get("invalid_at"),
                "expired_at": rel_props.get("expired_at"),
                "search_text": rel_props.get("search_text", ""),
                "simulation_id": rel_props.get("simulation_id"),
                "is_runtime_memory": bool(rel_props.get("is_runtime_memory")),
                "direction": direction,
            }
            if other:
                edge_payload["other_node_uuid"] = other_props.get("uuid", "")
                edge_payload["other_node_name"] = other_props.get("name", "")
            result.append(edge_payload)
        return result

    def search_nodes(self, graph_id: str, query: str, limit: int = 10, simulation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = self._normalize_text(query)
        simulation_id = self._normalize_text(simulation_id)
        if limit <= 0:
            return []
        if not query:
            nodes = self.get_all_nodes(graph_id, simulation_id=simulation_id)
            return nodes[:limit]

        cypher = f"""
        CALL db.index.fulltext.queryNodes($index_name, $query) YIELD node, score
        WHERE node.graph_id = $graph_id
          AND ($simulation_id = '' OR coalesce(node.simulation_id, '') = '' OR node.simulation_id = $simulation_id)
        WITH node,
             score
             + CASE
                 WHEN $simulation_id <> '' AND '{self.MEMORY_SUMMARY_LABEL}' IN coalesce(node.labels, []) THEN 18
                 WHEN $simulation_id <> '' AND '{self.SIMULATION_ACTIVITY_LABEL}' IN coalesce(node.labels, []) THEN 6
                 ELSE 0
               END AS score
        RETURN node, score
        ORDER BY score DESC
        LIMIT $limit
        """
        for fulltext_query in self._build_fulltext_queries(query):
            try:
                rows = self._run_read(
                    cypher,
                    {
                        "graph_id": graph_id,
                        "simulation_id": simulation_id,
                        "query": fulltext_query,
                        "limit": limit,
                        "index_name": self.NODE_FULLTEXT_INDEX,
                    },
                )
                if rows:
                    return [self._format_node_search_row(row) for row in rows]
            except Exception as exc:
                logger.debug("Node fulltext search fallback triggered: %s", exc)

        lowered = self._normalize_query(query).lower()
        terms = self._tokenize_query(query)
        cypher = f"""
        MATCH (n:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id}})
        WHERE $simulation_id = '' OR coalesce(n.simulation_id, '') = '' OR n.simulation_id = $simulation_id
        WITH n,
             CASE
                 WHEN $query_lower <> '' AND (
                     toLower(coalesce(n.search_text, '')) CONTAINS $query_lower
                     OR toLower(coalesce(n.name, '')) CONTAINS $query_lower
                     OR toLower(coalesce(n.summary, '')) CONTAINS $query_lower
                 ) THEN 20
                 ELSE 0
             END +
             reduce(score = 0, term IN $terms |
                 score +
                 CASE
                     WHEN $simulation_id <> '' AND '{self.MEMORY_SUMMARY_LABEL}' IN coalesce(n.labels, []) THEN 18
                     WHEN $simulation_id <> '' AND '{self.SIMULATION_ACTIVITY_LABEL}' IN coalesce(n.labels, []) THEN 6
                     ELSE 0
                 END +
                 CASE WHEN toLower(coalesce(n.name, '')) CONTAINS term THEN 8 ELSE 0 END +
                 CASE WHEN toLower(coalesce(n.summary, '')) CONTAINS term THEN 5 ELSE 0 END +
                 CASE WHEN toLower(coalesce(n.search_text, '')) CONTAINS term THEN 3 ELSE 0 END
             ) AS score
        WHERE score > 0
        RETURN n, score
        ORDER BY score DESC, coalesce(n.updated_at, n.created_at, n.name, n.uuid)
        LIMIT $limit
        """
        rows = self._run_read(
            cypher,
            {
                "graph_id": graph_id,
                "simulation_id": simulation_id,
                "query_lower": lowered,
                "terms": terms,
                "limit": limit,
            },
        )
        return [self._format_node_search_row(row) for row in rows]

    def search_edges(self, graph_id: str, query: str, limit: int = 10, simulation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = self._normalize_text(query)
        simulation_id = self._normalize_text(simulation_id)
        if limit <= 0:
            return []
        if not query:
            edges = self.get_all_edges(graph_id, simulation_id=simulation_id)
            return edges[:limit]

        cypher = f"""
        CALL db.index.fulltext.queryRelationships($index_name, $query) YIELD relationship, score
        WHERE relationship.graph_id = $graph_id
          AND ($simulation_id = '' OR coalesce(relationship.simulation_id, '') = '' OR relationship.simulation_id = $simulation_id)
        WITH relationship,
             score
             + CASE
                 WHEN $simulation_id <> '' AND coalesce(relationship.name, '') = 'SIMULATION_MEMORY_SUMMARY' THEN 18
                 WHEN $simulation_id <> '' AND coalesce(relationship.name, '') = 'SIMULATION_ACTIVITY' THEN 6
                 ELSE 0
               END AS score
        RETURN properties(relationship) AS relationship,
               properties(startNode(relationship)) AS startNode,
               properties(endNode(relationship)) AS endNode,
               score
        ORDER BY score DESC
        LIMIT $limit
        """
        for fulltext_query in self._build_fulltext_queries(query):
            try:
                rows = self._run_read(
                    cypher,
                    {
                        "graph_id": graph_id,
                        "simulation_id": simulation_id,
                        "query": fulltext_query,
                        "limit": limit,
                        "index_name": self.REL_FULLTEXT_INDEX,
                    },
                )
                if rows:
                    return [self._format_edge_search_row(row) for row in rows]
            except Exception as exc:
                logger.debug("Relationship fulltext search fallback triggered: %s", exc)

        lowered = self._normalize_query(query).lower()
        terms = self._tokenize_query(query)
        cypher = f"""
        MATCH (s:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id}})-[r:{self.RELATED_RELATIONSHIP} {{graph_id: $graph_id}}]->(t:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id}})
        WHERE $simulation_id = '' OR coalesce(r.simulation_id, '') = '' OR r.simulation_id = $simulation_id
        WITH r, s, t,
             CASE
                 WHEN $query_lower <> '' AND (
                     toLower(coalesce(r.search_text, '')) CONTAINS $query_lower
                     OR toLower(coalesce(r.name, '')) CONTAINS $query_lower
                     OR toLower(coalesce(r.fact, '')) CONTAINS $query_lower
                     OR toLower(coalesce(s.name, '')) CONTAINS $query_lower
                     OR toLower(coalesce(t.name, '')) CONTAINS $query_lower
                 ) THEN 24
                 ELSE 0
             END +
             reduce(score = 0, term IN $terms |
                 score +
                 CASE
                     WHEN $simulation_id <> '' AND coalesce(r.name, '') = 'SIMULATION_MEMORY_SUMMARY' THEN 18
                     WHEN $simulation_id <> '' AND coalesce(r.name, '') = 'SIMULATION_ACTIVITY' THEN 6
                     ELSE 0
                 END +
                 CASE WHEN toLower(coalesce(r.fact, '')) CONTAINS term THEN 8 ELSE 0 END +
                 CASE WHEN toLower(coalesce(r.name, '')) CONTAINS term THEN 5 ELSE 0 END +
                 CASE WHEN toLower(coalesce(s.name, '')) CONTAINS term THEN 4 ELSE 0 END +
                 CASE WHEN toLower(coalesce(t.name, '')) CONTAINS term THEN 4 ELSE 0 END +
                 CASE WHEN toLower(coalesce(r.search_text, '')) CONTAINS term THEN 3 ELSE 0 END
             ) AS score
        WHERE score > 0
        RETURN properties(r) AS r, properties(s) AS s, properties(t) AS t, score
        ORDER BY score DESC, coalesce(r.updated_at, r.created_at, r.name, r.edge_uuid)
        LIMIT $limit
        """
        rows = self._run_read(
            cypher,
            {
                "graph_id": graph_id,
                "simulation_id": simulation_id,
                "query_lower": lowered,
                "terms": terms,
                "limit": limit,
            },
        )
        return [self._format_edge_search_row(row) for row in rows]

    def delete_graph(self, graph_id: str) -> Dict[str, Any]:
        query = f"""
        CALL {{
            MATCH (n)
            WHERE n.graph_id = $graph_id
            RETURN count(n) AS deleted_count
        }}
        MATCH (n)
        WHERE n.graph_id = $graph_id
        DETACH DELETE n
        RETURN deleted_count
        """
        rows = self._run_write(query, {"graph_id": graph_id})
        deleted_count = rows[0].get("deleted_count", 0) if rows else 0
        return {"graph_id": graph_id, "deleted_count": deleted_count}

    def delete_runtime_memory(
        self,
        graph_id: Optional[str] = None,
        simulation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        graph_id = self._normalize_text(graph_id)
        simulation_id = self._normalize_text(simulation_id)
        params = {
            "graph_id": graph_id,
            "simulation_id": simulation_id,
        }

        memory_query = f"""
        MATCH (m:{self.MEMORY_SUMMARY_LABEL})
        WHERE ($graph_id = '' OR m.graph_id = $graph_id)
          AND ($simulation_id = '' OR m.simulation_id = $simulation_id)
        WITH collect(m) AS items
        FOREACH (item IN items | DETACH DELETE item)
        RETURN size(items) AS deleted_count
        """
        activity_query = f"""
        MATCH (a:{self.GRAPH_ACTIVITY_LABEL})
        WHERE ($graph_id = '' OR a.graph_id = $graph_id)
          AND ($simulation_id = '' OR a.simulation_id = $simulation_id)
        WITH collect(a) AS items
        FOREACH (item IN items | DETACH DELETE item)
        RETURN size(items) AS deleted_count
        """
        runtime_edge_query = f"""
        MATCH ()-[r]->()
        WHERE (
            coalesce(r.is_runtime_memory, false) = true
            OR coalesce(r.name, '') = 'SIMULATION_ACTIVITY'
            OR coalesce(r.simulation_id, '') <> ''
        )
          AND ($graph_id = '' OR r.graph_id = $graph_id)
          AND ($simulation_id = '' OR coalesce(r.simulation_id, '') = $simulation_id)
        WITH collect(r) AS items
        FOREACH (item IN items | DELETE item)
        RETURN size(items) AS deleted_count
        """
        runtime_node_query = f"""
        MATCH (n:{self.GRAPH_NODE_LABEL})
        WHERE (
            coalesce(n.is_runtime_memory, false) = true
            OR '{self.SIMULATION_ACTIVITY_LABEL}' IN coalesce(n.labels, [])
            OR coalesce(n.simulation_id, '') <> ''
        )
          AND ($graph_id = '' OR n.graph_id = $graph_id)
          AND ($simulation_id = '' OR coalesce(n.simulation_id, '') = $simulation_id)
        WITH collect(n) AS items
        FOREACH (item IN items | DETACH DELETE item)
        RETURN size(items) AS deleted_count
        """

        memory_rows = self._run_write(memory_query, params)
        activity_rows = self._run_write(activity_query, params)
        runtime_edge_rows = self._run_write(runtime_edge_query, params)
        runtime_node_rows = self._run_write(runtime_node_query, params)

        return {
            "graph_id": graph_id or None,
            "simulation_id": simulation_id or None,
            "deleted_memory_summaries": memory_rows[0].get("deleted_count", 0) if memory_rows else 0,
            "deleted_activity_records": activity_rows[0].get("deleted_count", 0) if activity_rows else 0,
            "deleted_runtime_edges": runtime_edge_rows[0].get("deleted_count", 0) if runtime_edge_rows else 0,
            "deleted_runtime_nodes": runtime_node_rows[0].get("deleted_count", 0) if runtime_node_rows else 0,
        }

    def append_activity(self, graph_id: str, activity: Any) -> Dict[str, Any]:
        data = self._to_mapping(activity)
        now = self._now_iso()
        activity_id = self._normalize_text(
            data.get("activity_id") or data.get("activity_uuid") or data.get("uuid") or uuid.uuid4().hex
        )
        simulation_id = self._normalize_text(data.get("simulation_id"))
        activity_node_uuid = f"activity_{activity_id}"
        activity_edge_uuid = f"activity_edge_{activity_id}"
        description = self._normalize_text(data.get("description") or data.get("result") or data.get("action_type"))
        payload = {
            "activity_id": activity_id,
            "graph_id": graph_id,
            "simulation_id": simulation_id,
            "platform": self._normalize_text(data.get("platform")),
            "round_num": data.get("round_num"),
            "timestamp": self._normalize_text(data.get("timestamp") or now),
            "agent_id": data.get("agent_id"),
            "agent_name": self._normalize_text(data.get("agent_name")),
            "action_type": self._normalize_text(data.get("action_type")),
            "action_args_json": self._json_dumps(data.get("action_args", {})),
            "result": self._normalize_text(data.get("result")),
            "success": bool(data.get("success", True)),
            "activity_json": self._json_dumps(data),
            "activity_node_uuid": activity_node_uuid,
            "activity_edge_uuid": activity_edge_uuid,
            "description": description,
            "search_text": self._build_search_text(
                [
                    graph_id,
                    simulation_id,
                    data.get("platform"),
                    data.get("agent_name"),
                    data.get("action_type"),
                    data.get("description"),
                    data.get("result"),
                    data.get("action_args"),
                ]
            ),
            "created_at": now,
            "updated_at": now,
        }

        query = f"""
        MERGE (g:{self.GRAPH_META_LABEL} {{graph_id: $graph_id}})
        ON CREATE SET g.created_at = $now, g.name = coalesce(g.name, $graph_id)
        SET g.updated_at = $now
        MERGE (activity_node:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id, uuid: $activity_node_uuid}})
        SET activity_node.name = CASE WHEN $agent_name = '' THEN $action_type ELSE $agent_name + ' ' + $action_type END,
            activity_node.labels = ['Node', '{self.SIMULATION_ACTIVITY_LABEL}'],
            activity_node.summary = $description,
            activity_node.attributes_json = $activity_json,
            activity_node.search_text = $search_text,
            activity_node.simulation_id = $simulation_id,
            activity_node.is_runtime_memory = true,
            activity_node.created_at = coalesce(activity_node.created_at, $created_at),
            activity_node.updated_at = $updated_at
        WITH g, activity_node
        OPTIONAL MATCH (actor:{self.GRAPH_NODE_LABEL} {{graph_id: $graph_id, name: $agent_name}})
        WITH g, activity_node, head(collect(actor)) AS actor
        FOREACH (_ IN CASE WHEN actor IS NULL THEN [] ELSE [1] END |
            MERGE (actor)-[rel:{self.RELATED_RELATIONSHIP} {{graph_id: $graph_id, edge_uuid: $activity_edge_uuid}}]->(activity_node)
            SET rel.name = 'SIMULATION_ACTIVITY',
                rel.fact = $description,
                rel.attributes_json = $activity_json,
                rel.search_text = $search_text,
                rel.simulation_id = $simulation_id,
                rel.is_runtime_memory = true,
                rel.created_at = coalesce(rel.created_at, $created_at),
                rel.updated_at = $updated_at,
                rel.source_node_uuid = actor.uuid,
                rel.target_node_uuid = activity_node.uuid,
                rel.source_node_name = actor.name,
                rel.target_node_name = activity_node.name
        )
        MERGE (a:{self.GRAPH_ACTIVITY_LABEL} {{graph_id: $graph_id, activity_id: $activity_id}})
        SET a.platform = $platform,
            a.simulation_id = $simulation_id,
            a.round_num = $round_num,
            a.timestamp = $timestamp,
            a.agent_id = $agent_id,
            a.agent_name = $agent_name,
            a.action_type = $action_type,
            a.action_args_json = $action_args_json,
            a.description = $description,
            a.result = $result,
            a.success = $success,
            a.activity_json = $activity_json,
            a.search_text = $search_text,
            a.created_at = coalesce(a.created_at, $created_at),
            a.updated_at = $updated_at
        MERGE (g)-[:HAS_ACTIVITY {{graph_id: $graph_id}}]->(a)
        RETURN a.activity_id AS activity_id
        """
        rows = self._run_write(query, {**payload, "now": now})
        return {"graph_id": graph_id, "activity_id": activity_id, "raw": rows[0] if rows else None}

    def append_activities(self, graph_id: str, activities: Sequence[Any]) -> List[Dict[str, Any]]:
        return [self.append_activity(graph_id, activity) for activity in activities or []]

    def get_activities(
        self,
        graph_id: str,
        simulation_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        simulation_id = self._normalize_text(simulation_id)
        limit_clause = "LIMIT $limit" if limit and limit > 0 else ""
        query = f"""
        MATCH (a:{self.GRAPH_ACTIVITY_LABEL} {{graph_id: $graph_id}})
        WHERE $simulation_id = '' OR a.simulation_id = $simulation_id
        RETURN a
        ORDER BY coalesce(a.round_num, 0), coalesce(a.timestamp, a.updated_at, a.created_at)
        {limit_clause}
        """
        rows = self._run_read(
            query,
            {
                "graph_id": graph_id,
                "simulation_id": simulation_id,
                "limit": limit or 0,
            },
        )
        result: List[Dict[str, Any]] = []
        for row in rows:
            activity = row.get("a", {})
            props = self._record_properties(activity)
            result.append(
                {
                    "activity_id": props.get("activity_id", ""),
                    "graph_id": props.get("graph_id", graph_id),
                    "simulation_id": props.get("simulation_id", ""),
                    "platform": props.get("platform", ""),
                    "round_num": props.get("round_num"),
                    "timestamp": props.get("timestamp"),
                    "agent_id": props.get("agent_id"),
                    "agent_name": props.get("agent_name", ""),
                    "action_type": props.get("action_type", ""),
                    "action_args": self._json_loads(props.get("action_args_json"), default={}) or {},
                    "description": props.get("description", ""),
                    "result": props.get("result", ""),
                    "success": props.get("success", True),
                    "search_text": props.get("search_text", ""),
                }
            )
        return result

    def get_memory_summary(self, graph_id: str, summary_id: str) -> Optional[Dict[str, Any]]:
        summary_id = self._normalize_text(summary_id)
        if not summary_id:
            return None
        query = f"""
        MATCH (m:{self.MEMORY_SUMMARY_LABEL} {{graph_id: $graph_id, summary_id: $summary_id}})
        RETURN m
        LIMIT 1
        """
        rows = self._run_read(query, {"graph_id": graph_id, "summary_id": summary_id})
        if not rows:
            return None
        return self._format_memory_summary_row({"m": rows[0].get("m")})

    def delete_memory_summaries(
        self,
        graph_id: str,
        simulation_id: Optional[str] = None,
        summary_scope: Optional[str] = None,
    ) -> Dict[str, Any]:
        simulation_id = self._normalize_text(simulation_id)
        summary_scope = self._normalize_text(summary_scope)
        query = f"""
        MATCH (m:{self.MEMORY_SUMMARY_LABEL} {{graph_id: $graph_id}})
        WHERE ($simulation_id = '' OR m.simulation_id = $simulation_id)
          AND ($summary_scope = '' OR m.summary_scope = $summary_scope)
        WITH collect(m) AS items
        FOREACH (item IN items | DETACH DELETE item)
        RETURN size(items) AS deleted_count
        """
        rows = self._run_write(
            query,
            {
                "graph_id": graph_id,
                "simulation_id": simulation_id,
                "summary_scope": summary_scope,
            },
        )
        return {
            "graph_id": graph_id,
            "simulation_id": simulation_id or None,
            "summary_scope": summary_scope or None,
            "deleted_count": rows[0].get("deleted_count", 0) if rows else 0,
        }

    def upsert_memory_summary(self, graph_id: str, summary: Any) -> Dict[str, Any]:
        data = self._to_mapping(summary)
        now = self._now_iso()
        summary_id = self._normalize_text(data.get("summary_id") or data.get("uuid") or uuid.uuid4().hex)
        summary_text = self._normalize_text(data.get("summary_text") or data.get("summary"))
        memory_level = self._normalize_text(data.get("memory_level") or data.get("summary_scope") or "batch")
        payload = {
            "summary_id": summary_id,
            "graph_id": graph_id,
            "simulation_id": self._normalize_text(data.get("simulation_id")),
            "summary_scope": memory_level,
            "memory_level": memory_level,
            "platform": self._normalize_text(data.get("platform")),
            "agent_id": data.get("agent_id"),
            "agent_name": self._normalize_text(data.get("agent_name")),
            "title": self._normalize_text(data.get("title")),
            "summary": summary_text,
            "summary_text": summary_text,
            "facts_json": self._json_dumps(data.get("facts", data.get("highlights", []))),
            "keywords_json": self._json_dumps(data.get("keywords", [])),
            "entities_json": self._json_dumps(data.get("entities", [])),
            "source_refs_json": self._json_dumps(data.get("source_refs", data.get("recent_descriptions", []))),
            "action_counts_json": self._json_dumps(data.get("action_counts", {})),
            "activity_count": int(data.get("activity_count") or data.get("event_count") or 0),
            "round_start": int(data.get("round_start") or data.get("round_from") or 0),
            "round_end": int(data.get("round_end") or data.get("round_to") or 0),
            "last_activity_at": self._normalize_text(data.get("last_activity_at") or data.get("updated_at") or data.get("created_at") or now),
            "search_text": self._normalize_text(data.get("search_text"))
            or self._build_search_text(
                [
                    graph_id,
                    data.get("simulation_id"),
                    memory_level,
                    data.get("platform"),
                    data.get("agent_name"),
                    data.get("title"),
                    summary_text,
                    data.get("facts", data.get("highlights", [])),
                    data.get("keywords", []),
                    data.get("entities", []),
                ]
            ),
            "created_at": self._normalize_text(data.get("created_at") or now),
            "updated_at": self._normalize_text(data.get("updated_at") or now),
        }

        query = f"""
        MERGE (g:{self.GRAPH_META_LABEL} {{graph_id: $graph_id}})
        ON CREATE SET g.created_at = $now, g.name = coalesce(g.name, $graph_id)
        SET g.updated_at = $now
        MERGE (m:{self.MEMORY_SUMMARY_LABEL} {{graph_id: $graph_id, summary_id: $summary_id}})
        SET m.simulation_id = $simulation_id,
            m.summary_scope = $summary_scope,
            m.memory_level = $memory_level,
            m.platform = $platform,
            m.agent_id = $agent_id,
            m.agent_name = $agent_name,
            m.title = $title,
            m.summary = $summary,
            m.summary_text = $summary_text,
            m.facts_json = $facts_json,
            m.keywords_json = $keywords_json,
            m.entities_json = $entities_json,
            m.source_refs_json = $source_refs_json,
            m.action_counts_json = $action_counts_json,
            m.activity_count = $activity_count,
            m.event_count = $activity_count,
            m.round_start = $round_start,
            m.round_end = $round_end,
            m.round_from = $round_start,
            m.round_to = $round_end,
            m.last_activity_at = $last_activity_at,
            m.search_text = $search_text,
            m.created_at = coalesce(m.created_at, $created_at),
            m.updated_at = $updated_at
        MERGE (g)-[:HAS_MEMORY_SUMMARY {{graph_id: $graph_id}}]->(m)
        RETURN m.summary_id AS summary_id
        """
        rows = self._run_write(query, {**payload, "now": now})
        return {"graph_id": graph_id, "summary_id": summary_id, "raw": rows[0] if rows else None}

    def upsert_memory_summaries(self, graph_id: str, summaries: Sequence[Any]) -> List[Dict[str, Any]]:
        return [self.upsert_memory_summary(graph_id, summary) for summary in summaries or []]

    def get_memory_summaries(
        self,
        graph_id: str,
        simulation_id: Optional[str] = None,
        summary_scope: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        simulation_id = self._normalize_text(simulation_id)
        summary_scope = self._normalize_text(summary_scope)
        query = f"""
        MATCH (m:{self.MEMORY_SUMMARY_LABEL} {{graph_id: $graph_id}})
        WHERE ($simulation_id = '' OR m.simulation_id = $simulation_id)
          AND ($summary_scope = '' OR m.summary_scope = $summary_scope)
        RETURN m
        ORDER BY
            CASE coalesce(m.memory_level, m.summary_scope, '')
                WHEN 'overview' THEN 0
                WHEN 'simulation' THEN 0
                WHEN 'platform' THEN 1
                ELSE 2
            END,
            coalesce(m.updated_at, m.created_at)
        """
        rows = self._run_read(
            query,
            {
                "graph_id": graph_id,
                "simulation_id": simulation_id,
                "summary_scope": summary_scope,
            },
        )
        return [self._format_memory_summary_row({"m": row.get("m")}) for row in rows]

    def list_memory_summaries(
        self,
        graph_id: str,
        simulation_id: Optional[str] = None,
        memory_level: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self.get_memory_summaries(
            graph_id,
            simulation_id=simulation_id,
            summary_scope=memory_level,
        )

    def search_memory_summaries(
        self,
        graph_id: str,
        query: str,
        limit: int = 5,
        simulation_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = self._normalize_text(query)
        simulation_id = self._normalize_text(simulation_id)
        if limit <= 0 or not simulation_id:
            return []
        if not query:
            return self.get_memory_summaries(graph_id, simulation_id=simulation_id)[:limit]

        cypher = f"""
        CALL db.index.fulltext.queryNodes($index_name, $query) YIELD node, score
        WHERE node.graph_id = $graph_id
          AND node.simulation_id = $simulation_id
        RETURN node, score
        ORDER BY
            CASE coalesce(node.memory_level, node.summary_scope, '')
                WHEN 'overview' THEN 0
                WHEN 'simulation' THEN 0
                WHEN 'platform' THEN 1
                ELSE 2
            END,
            score DESC
        LIMIT $limit
        """
        for fulltext_query in self._build_fulltext_queries(query):
            try:
                rows = self._run_read(
                    cypher,
                    {
                        "graph_id": graph_id,
                        "simulation_id": simulation_id,
                        "query": fulltext_query,
                        "limit": limit,
                        "index_name": self.MEMORY_FULLTEXT_INDEX,
                    },
                )
                if rows:
                    return [self._format_memory_summary_search_row(row) for row in rows]
            except Exception as exc:
                logger.debug("Memory summary fulltext search fallback triggered: %s", exc)

        lowered = self._normalize_query(query).lower()
        terms = self._tokenize_query(query)
        cypher = f"""
        MATCH (m:{self.MEMORY_SUMMARY_LABEL} {{graph_id: $graph_id}})
        WHERE m.simulation_id = $simulation_id
        WITH m,
             CASE
                 WHEN $query_lower <> '' AND (
                     toLower(coalesce(m.search_text, '')) CONTAINS $query_lower
                     OR toLower(coalesce(m.title, '')) CONTAINS $query_lower
                     OR toLower(coalesce(m.summary, '')) CONTAINS $query_lower
                 ) THEN 28
                 ELSE 0
             END +
             reduce(score = 0, term IN $terms |
                 score +
                 CASE WHEN toLower(coalesce(m.title, '')) CONTAINS term THEN 9 ELSE 0 END +
                 CASE WHEN toLower(coalesce(m.summary, '')) CONTAINS term THEN 7 ELSE 0 END +
                 CASE WHEN toLower(coalesce(m.search_text, '')) CONTAINS term THEN 4 ELSE 0 END
             ) AS score
        WHERE score > 0
        RETURN m, score
        ORDER BY
            CASE coalesce(m.memory_level, m.summary_scope, '')
                WHEN 'overview' THEN 0
                WHEN 'simulation' THEN 0
                WHEN 'platform' THEN 1
                ELSE 2
            END,
            score DESC,
            coalesce(m.updated_at, m.created_at)
        LIMIT $limit
        """
        rows = self._run_read(
            cypher,
            {
                "graph_id": graph_id,
                "simulation_id": simulation_id,
                "query_lower": lowered,
                "terms": terms,
                "limit": limit,
            },
        )
        return [self._format_memory_summary_search_row(row) for row in rows]

    def search_graph(self, graph_id: str, query: str, limit: int = 10, scope: str = "edges", simulation_id: Optional[str] = None) -> Dict[str, Any]:
        """Convenience wrapper for compatibility with existing services."""
        query = self._normalize_text(query)
        simulation_id = self._normalize_text(simulation_id)
        memory_limit = max(1, min(limit, int(os.environ.get("MEMORY_SUMMARY_SEARCH_LIMIT", "4"))))
        memory_summaries = self.search_memory_summaries(
            graph_id,
            query,
            limit=memory_limit,
            simulation_id=simulation_id,
        ) if simulation_id else []

        if scope == "nodes":
            nodes = self.search_nodes(graph_id, query, limit, simulation_id=simulation_id)
            if simulation_id and memory_summaries:
                nodes = [
                    node
                    for node in nodes
                    if not (
                        node.get("is_runtime_memory")
                        or node.get("simulation_id")
                    )
                ]
            facts = self._memory_summary_facts(memory_summaries)
            facts.extend([node.get("summary", "") for node in nodes if node.get("summary")])
            facts = [fact for fact in facts if fact]
            facts = list(dict.fromkeys(facts))
            return {
                "facts": facts,
                "edges": [],
                "nodes": nodes,
                "memory_summaries": memory_summaries,
                "query": query,
                "total_count": len(memory_summaries) + len(nodes) or len(facts),
            }

        if scope == "both":
            nodes = self.search_nodes(graph_id, query, limit, simulation_id=simulation_id)
            edges = self.search_edges(graph_id, query, limit, simulation_id=simulation_id)
        else:
            edges = self.search_edges(graph_id, query, limit, simulation_id=simulation_id)
            nodes = []

        if simulation_id and memory_summaries:
            edges = [
                edge
                for edge in edges
                if not (
                    edge.get("is_runtime_memory")
                    or edge.get("simulation_id")
                    or edge.get("name") == "SIMULATION_ACTIVITY"
                )
            ]
            nodes = [
                node
                for node in nodes
                if not (
                    node.get("is_runtime_memory")
                    or node.get("simulation_id")
                )
            ]

        facts = self._memory_summary_facts(memory_summaries)
        facts.extend([edge.get("fact", "") for edge in edges if edge.get("fact")])
        facts.extend([f"[{node.get('name', '')}]: {node.get('summary', '')}" for node in nodes if node.get("summary")])
        facts = [fact for fact in facts if fact]
        facts = list(dict.fromkeys(facts))
        total_count = len(memory_summaries) + len(edges) + len(nodes)
        if not total_count:
            total_count = len(facts)
        return {
            "facts": facts,
            "edges": edges,
            "nodes": nodes,
            "memory_summaries": memory_summaries,
            "query": query,
            "total_count": total_count,
        }

    def _format_memory_summary_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        memory = row.get("m") or row.get("node") or {}
        props = self._record_properties(memory)
        summary_text = props.get("summary") or props.get("summary_text", "")
        memory_level = props.get("memory_level") or props.get("summary_scope", "")
        facts = self._json_loads(props.get("facts_json"), default=[]) or []
        source_refs = self._json_loads(props.get("source_refs_json"), default=[]) or []
        return {
            "summary_id": props.get("summary_id", ""),
            "graph_id": props.get("graph_id", ""),
            "simulation_id": props.get("simulation_id", ""),
            "summary_scope": props.get("summary_scope", "") or memory_level,
            "memory_level": memory_level,
            "platform": props.get("platform", ""),
            "agent_id": props.get("agent_id"),
            "agent_name": props.get("agent_name", ""),
            "title": props.get("title", ""),
            "summary_text": summary_text,
            "summary": summary_text,
            "facts": facts,
            "highlights": facts,
            "recent_descriptions": source_refs,
            "keywords": self._json_loads(props.get("keywords_json"), default=[]) or [],
            "entities": self._json_loads(props.get("entities_json"), default=[]) or [],
            "source_refs": source_refs,
            "action_counts": self._json_loads(props.get("action_counts_json"), default={}) or {},
            "event_count": props.get("event_count", props.get("activity_count", 0)),
            "activity_count": props.get("activity_count", props.get("event_count", 0)),
            "round_from": props.get("round_from", props.get("round_start")),
            "round_to": props.get("round_to", props.get("round_end")),
            "round_start": props.get("round_start", props.get("round_from")),
            "round_end": props.get("round_end", props.get("round_to")),
            "last_activity_at": props.get("last_activity_at", ""),
            "search_text": props.get("search_text", ""),
            "created_at": props.get("created_at"),
            "updated_at": props.get("updated_at"),
        }

    def _format_memory_summary_search_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        summary_dict = self._format_memory_summary_row(row)
        summary_dict["score"] = row.get("score", 0.0)
        return summary_dict

    @staticmethod
    def _memory_summary_facts(memory_summaries: Sequence[Dict[str, Any]]) -> List[str]:
        facts: List[str] = []
        for summary in memory_summaries or []:
            level = summary.get("memory_level") or summary.get("summary_scope") or "batch"
            platform = summary.get("platform") or "all"
            round_start = summary.get("round_start", summary.get("round_from", 0))
            round_end = summary.get("round_end", summary.get("round_to", 0))
            prefix = f"[memory/{level}/{platform}/R{round_start}-{round_end}]"
            title = str(summary.get("title", "")).strip()
            summary_text = str(summary.get("summary_text", "") or summary.get("summary", "")).strip()
            if title and summary_text:
                facts.append(f"{prefix} {title}: {summary_text}")
            elif summary_text:
                facts.append(f"{prefix} {summary_text}")
            for fact in summary.get("facts", summary.get("highlights", [])) or []:
                fact_text = str(fact).strip()
                if fact_text:
                    facts.append(f"{prefix} {fact_text}")
        return facts

    def _format_node_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        node = row.get("n") or row.get("node") or {}
        properties = self._record_properties(node)
        labels = self._normalize_list(properties.get("labels"))
        attributes = self._json_loads(properties.get("attributes_json"), default={})
        return {
            "uuid": properties.get("uuid", ""),
            "name": properties.get("name", ""),
            "labels": labels,
            "summary": properties.get("summary", ""),
            "attributes": attributes if isinstance(attributes, dict) else {},
            "graph_id": properties.get("graph_id", ""),
            "created_at": properties.get("created_at"),
            "updated_at": properties.get("updated_at"),
            "search_text": properties.get("search_text", ""),
            "simulation_id": properties.get("simulation_id"),
            "is_runtime_memory": bool(properties.get("is_runtime_memory")),
            "entity_type": self._first_custom_label(labels),
        }

    def _format_node_search_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        node_dict = self._format_node_row({"n": row.get("node")})
        node_dict["score"] = row.get("score", 0.0)
        return node_dict

    def _format_edge_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        rel = row.get("r") or row.get("relationship") or {}
        source = row.get("s") or row.get("startNode") or {}
        target = row.get("t") or row.get("endNode") or {}
        rel_props = self._record_properties(rel)
        source_props = self._record_properties(source)
        target_props = self._record_properties(target)
        return {
            "uuid": rel_props.get("edge_uuid", rel_props.get("uuid", "")),
            "name": rel_props.get("name", ""),
            "fact": rel_props.get("fact", ""),
            "source_node_uuid": rel_props.get("source_node_uuid") or source_props.get("uuid", ""),
            "target_node_uuid": rel_props.get("target_node_uuid") or target_props.get("uuid", ""),
            "source_node_name": rel_props.get("source_node_name") or source_props.get("name", ""),
            "target_node_name": rel_props.get("target_node_name") or target_props.get("name", ""),
            "attributes": self._json_loads(rel_props.get("attributes_json"), default={}) or {},
            "graph_id": rel_props.get("graph_id", ""),
            "created_at": rel_props.get("created_at"),
            "updated_at": rel_props.get("updated_at"),
            "valid_at": rel_props.get("valid_at"),
            "invalid_at": rel_props.get("invalid_at"),
            "expired_at": rel_props.get("expired_at"),
            "search_text": rel_props.get("search_text", ""),
            "simulation_id": rel_props.get("simulation_id"),
            "is_runtime_memory": bool(rel_props.get("is_runtime_memory")),
        }

    def _format_edge_search_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        edge_dict = self._format_edge_row(
            {
                "relationship": row.get("relationship"),
                "startNode": row.get("startNode"),
                "endNode": row.get("endNode"),
            }
        )
        edge_dict["score"] = row.get("score", 0.0)
        return edge_dict


def get_graph_store() -> Neo4jGraphStore:
    return Neo4jGraphStore()


__all__ = ["Neo4jGraphStore", "get_graph_store"]
