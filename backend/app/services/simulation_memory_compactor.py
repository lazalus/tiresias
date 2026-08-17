"""
Simulation memory compaction service.

This service keeps a compact, simulation-scoped memory layer in Neo4j so report
and retrieval flows can read summaries before scanning every raw activity.
"""

from __future__ import annotations

import dataclasses
import json
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Sequence

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from .neo4j_graph_store import Neo4jGraphStore

logger = get_logger("tiresias.simulation_memory_compactor")


class SimulationMemoryCompactor:
    """Build and update compact simulation memory summaries."""

    ACTION_LABELS = {
        "CREATE_POST": "게시 작성",
        "LIKE_POST": "게시 좋아요",
        "DISLIKE_POST": "게시 비추천",
        "REPOST": "리포스트",
        "QUOTE_POST": "인용 게시",
        "FOLLOW": "팔로우",
        "CREATE_COMMENT": "댓글 작성",
        "LIKE_COMMENT": "댓글 좋아요",
        "DISLIKE_COMMENT": "댓글 비추천",
        "SEARCH_POSTS": "게시 검색",
        "SEARCH_USER": "사용자 검색",
        "MUTE": "뮤트",
        "DO_NOTHING": "관망",
    }

    PLATFORM_LABELS = {
        "twitter": "트위터",
        "reddit": "레딧",
    }

    KEYWORD_STOPWORDS = {
        "about",
        "agent",
        "analysis",
        "comment",
        "content",
        "create",
        "data",
        "graph",
        "like",
        "memory",
        "post",
        "query",
        "reddit",
        "round",
        "search",
        "simulation",
        "summary",
        "target",
        "this",
        "timestamp",
        "twitter",
        "user",
        "게시",
        "게시물",
        "댓글",
        "관련",
        "검색",
        "내용",
        "시뮬레이션",
        "에이전트",
        "요약",
        "조회",
    }

    def __init__(
        self,
        graph_id: Optional[str] = None,
        simulation_id: Optional[str] = None,
        store: Optional[Neo4jGraphStore] = None,
        llm_client: Optional[LLMClient] = None,
        use_llm: Optional[bool] = None,
        max_recent: Optional[int] = None,
    ) -> None:
        self.graph_id = (graph_id or "").strip()
        self.simulation_id = (simulation_id or "").strip()
        self.store = store or Neo4jGraphStore()
        self._llm_client = llm_client
        self.use_llm = Config.MEMORY_SUMMARY_USE_LLM if use_llm is None else use_llm
        self.max_recent = max(3, max_recent or Config.MEMORY_SUMMARY_MAX_RECENT)
        self.batch_size = max(1, int(getattr(Config, "MEMORY_SUMMARY_BATCH_SIZE", 12)))
        self._pending_activities: List[Dict[str, Any]] = []
        self._ingested_activity_count = 0
        self._summary_updates = 0
        self._rebuild_count = 0
        self._last_simulation_id = ""

    @property
    def llm(self) -> LLMClient:
        if self._llm_client is None:
            self._llm_client = LLMClient()
        return self._llm_client

    def ingest(self, activities: Sequence[Any]) -> List[Dict[str, Any]]:
        if not Config.MEMORY_SUMMARY_ENABLED:
            return []
        if not self.graph_id or not self.simulation_id:
            raise ValueError("graph_id and simulation_id must be bound before ingest")
        normalized = self._normalize_activities(activities, simulation_id=self.simulation_id)
        self._pending_activities.extend(normalized)
        self._ingested_activity_count += len(normalized)
        if len(self._pending_activities) < self.batch_size:
            return []
        return self._flush_pending()

    def flush(self) -> List[Dict[str, Any]]:
        if not self._pending_activities:
            return []
        return self._flush_pending()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "simulation_id": self.simulation_id or self._last_simulation_id,
            "enabled": bool(Config.MEMORY_SUMMARY_ENABLED),
            "batch_size": self.batch_size,
            "ingested_activity_count": self._ingested_activity_count,
            "pending_activity_count": len(self._pending_activities),
            "summary_updates": self._summary_updates,
            "rebuild_count": self._rebuild_count,
        }

    def update_with_activities(
        self,
        graph_id: str,
        simulation_id: str,
        activities: Sequence[Any],
    ) -> List[Dict[str, Any]]:
        self._last_simulation_id = simulation_id
        normalized = self._normalize_activities(activities, simulation_id=simulation_id)
        return self._update_normalized_activities(graph_id, normalized)

    def _flush_pending(self) -> List[Dict[str, Any]]:
        pending = list(self._pending_activities)
        self._pending_activities = []
        try:
            return self._update_normalized_activities(self.graph_id, pending)
        except Exception:
            self._pending_activities = [*pending, *self._pending_activities]
            raise

    def _update_normalized_activities(
        self,
        graph_id: str,
        normalized: Sequence[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not normalized:
            return []

        results: List[Dict[str, Any]] = []
        for group in self._build_groups(normalized):
            existing = self.store.get_memory_summary(graph_id, group["summary_id"])
            payload = self._merge_summary(existing, group)
            results.append(self.store.upsert_memory_summary(graph_id, payload))
        self._summary_updates += len(results)
        return results

    def rebuild_simulation_memory(self, graph_id: str, simulation_id: str) -> Dict[str, Any]:
        simulation_id = (simulation_id or "").strip()
        if not simulation_id:
            raise ValueError("simulation_id is required")

        activities = self.store.get_activities(graph_id, simulation_id=simulation_id)
        normalized = self._normalize_activities(activities, simulation_id=simulation_id)
        self.store.delete_memory_summaries(graph_id, simulation_id=simulation_id)
        if not normalized:
            return {
                "graph_id": graph_id,
                "simulation_id": simulation_id,
                "summary_count": 0,
                "activity_count": 0,
            }

        payloads = [self._build_fresh_summary(group) for group in self._build_groups(normalized)]
        self.store.upsert_memory_summaries(graph_id, payloads)
        self._summary_updates += len(payloads)
        self._rebuild_count += 1
        self._last_simulation_id = simulation_id
        return {
            "graph_id": graph_id,
            "simulation_id": simulation_id,
            "summary_count": len(payloads),
            "activity_count": len(normalized),
        }

    def _normalize_activities(
        self,
        activities: Sequence[Any],
        simulation_id: str,
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for activity in activities or []:
            data = self._to_mapping(activity)
            resolved_simulation_id = self._normalize_text(data.get("simulation_id") or simulation_id)
            if not resolved_simulation_id:
                continue
            normalized.append(
                {
                    "simulation_id": resolved_simulation_id,
                    "platform": self._normalize_text(data.get("platform")).lower(),
                    "agent_id": data.get("agent_id"),
                    "agent_name": self._normalize_text(data.get("agent_name")),
                    "action_type": self._normalize_text(data.get("action_type")).upper(),
                    "action_args": data.get("action_args") or {},
                    "round_num": self._normalize_int(data.get("round_num") or data.get("round")),
                    "timestamp": self._normalize_text(data.get("timestamp") or data.get("created_at")),
                    "description": self._normalize_text(data.get("description")),
                }
            )
        return normalized

    def _build_groups(self, activities: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        groups: Dict[str, Dict[str, Any]] = {}

        for activity in activities:
            simulation_id = activity["simulation_id"]
            platform = activity["platform"]
            agent_id = activity.get("agent_id")
            agent_name = activity.get("agent_name", "")

            keys = [
                ("simulation", "", None, ""),
            ]
            if platform:
                keys.append(("platform", platform, None, ""))
            if platform and (agent_name or agent_id is not None):
                keys.append(("agent", platform, agent_id, agent_name))

            for summary_scope, scoped_platform, scoped_agent_id, scoped_agent_name in keys:
                summary_id = self._build_summary_id(
                    simulation_id=simulation_id,
                    summary_scope=summary_scope,
                    platform=scoped_platform,
                    agent_id=scoped_agent_id,
                    agent_name=scoped_agent_name,
                )
                group = groups.setdefault(
                    summary_id,
                    {
                        "summary_id": summary_id,
                        "summary_scope": summary_scope,
                        "simulation_id": simulation_id,
                        "platform": scoped_platform,
                        "agent_id": scoped_agent_id,
                        "agent_name": scoped_agent_name,
                        "event_count": 0,
                        "action_counts": {},
                        "recent_fragments": [],
                        "recent_descriptions": [],
                        "round_from": None,
                        "round_to": None,
                        "last_activity_at": "",
                    },
                )
                self._accumulate_group(group, activity)

        return list(groups.values())

    def _accumulate_group(self, group: Dict[str, Any], activity: Dict[str, Any]) -> None:
        group["event_count"] += 1

        action_counts = dict(group.get("action_counts") or {})
        action_type = activity.get("action_type") or "UNKNOWN"
        action_counts[action_type] = int(action_counts.get(action_type, 0)) + 1
        group["action_counts"] = action_counts

        round_num = self._normalize_int(activity.get("round_num"))
        if round_num is not None:
            if group["round_from"] is None or round_num < group["round_from"]:
                group["round_from"] = round_num
            if group["round_to"] is None or round_num > group["round_to"]:
                group["round_to"] = round_num

        timestamp = self._normalize_text(activity.get("timestamp"))
        if timestamp and timestamp > (group.get("last_activity_at") or ""):
            group["last_activity_at"] = timestamp

        description = self._normalize_text(activity.get("description")) or self._describe_activity(activity)
        if description:
            group["recent_descriptions"] = self._merge_recent_values(
                group.get("recent_descriptions", []),
                [description],
            )

        fragments = self._extract_fragments(activity)
        if fragments:
            group["recent_fragments"] = self._merge_recent_values(
                group.get("recent_fragments", []),
                fragments,
            )

    def _build_fresh_summary(self, group: Dict[str, Any]) -> Dict[str, Any]:
        return self._merge_summary(None, group)

    def _merge_summary(
        self,
        existing: Optional[Dict[str, Any]],
        group: Dict[str, Any],
    ) -> Dict[str, Any]:
        existing = existing or {}
        title = self._build_title(group)
        event_count = int(existing.get("event_count") or 0) + int(group.get("event_count") or 0)
        action_counts = self._merge_action_counts(
            existing.get("action_counts") or {},
            group.get("action_counts") or {},
        )
        recent_descriptions = self._merge_recent_values(
            existing.get("recent_descriptions") or [],
            group.get("recent_descriptions") or [],
        )
        highlights = self._merge_recent_values(
            existing.get("highlights") or [],
            group.get("recent_fragments") or [],
        )
        round_from = self._min_optional(
            self._normalize_int(existing.get("round_from")),
            self._normalize_int(group.get("round_from")),
        )
        round_to = self._max_optional(
            self._normalize_int(existing.get("round_to")),
            self._normalize_int(group.get("round_to")),
        )
        last_activity_at = max(
            self._normalize_text(existing.get("last_activity_at")),
            self._normalize_text(group.get("last_activity_at")),
        )

        keywords = self._extract_keywords([*recent_descriptions, *highlights, existing.get("summary_text", "")])
        summary_text = self._compose_summary(
            title=title,
            summary_scope=group.get("summary_scope", ""),
            platform=group.get("platform", ""),
            agent_name=group.get("agent_name", ""),
            event_count=event_count,
            action_counts=action_counts,
            round_from=round_from,
            round_to=round_to,
            highlights=highlights,
            keywords=keywords,
            existing_summary=self._normalize_text(existing.get("summary_text")),
        )
        search_text = " ".join(
            part
            for part in [
                title,
                summary_text,
                " ".join(highlights),
                " ".join(keywords),
                " ".join(
                    f"{self.ACTION_LABELS.get(action, action)} {count}"
                    for action, count in sorted(
                        action_counts.items(),
                        key=lambda item: (-item[1], item[0]),
                    )
                ),
                group.get("simulation_id", ""),
                group.get("platform", ""),
                group.get("agent_name", ""),
            ]
            if part
        ).strip()

        return {
            "summary_id": group.get("summary_id"),
            "summary_scope": group.get("summary_scope"),
            "simulation_id": group.get("simulation_id"),
            "platform": group.get("platform", ""),
            "agent_id": group.get("agent_id"),
            "agent_name": group.get("agent_name", ""),
            "title": title,
            "summary_text": summary_text,
            "highlights": highlights,
            "recent_descriptions": recent_descriptions,
            "keywords": keywords,
            "action_counts": action_counts,
            "event_count": event_count,
            "round_from": round_from,
            "round_to": round_to,
            "last_activity_at": last_activity_at,
            "search_text": search_text,
        }

    def _compose_summary(
        self,
        title: str,
        summary_scope: str,
        platform: str,
        agent_name: str,
        event_count: int,
        action_counts: Dict[str, int],
        round_from: Optional[int],
        round_to: Optional[int],
        highlights: Sequence[str],
        keywords: Sequence[str],
        existing_summary: str,
    ) -> str:
        if self.use_llm and summary_scope in {"simulation", "platform"} and event_count >= 6:
            try:
                return self._compose_summary_with_llm(
                    title=title,
                    summary_scope=summary_scope,
                    platform=platform,
                    agent_name=agent_name,
                    event_count=event_count,
                    action_counts=action_counts,
                    round_from=round_from,
                    round_to=round_to,
                    highlights=highlights,
                    keywords=keywords,
                    existing_summary=existing_summary,
                )
            except Exception as exc:
                logger.warning("Memory summary LLM fallback triggered: %s", exc)

        action_text = self._format_action_counts(action_counts)
        parts = [f"{title}에는 현재까지 {event_count}개의 활동이 누적됐다."]

        if round_from is not None and round_to is not None:
            if round_from == round_to:
                parts.append(f"주요 기록 범위는 {round_from}라운드다.")
            else:
                parts.append(f"주요 기록 범위는 {round_from}라운드부터 {round_to}라운드까지다.")

        if action_text:
            parts.append(f"행동 분포는 {action_text} 순이다.")

        if highlights:
            highlight_text = " / ".join(
                self._normalize_clause_text(highlight)
                for highlight in list(highlights)[:3]
                if self._normalize_clause_text(highlight)
            )
            if highlight_text:
                parts.append(f"최근 핵심 맥락은 {highlight_text}.")
        elif keywords:
            parts.append(f"핵심 주제는 {', '.join(list(keywords)[:4])}다.")

        return " ".join(part for part in parts if part).strip()

    def _compose_summary_with_llm(
        self,
        title: str,
        summary_scope: str,
        platform: str,
        agent_name: str,
        event_count: int,
        action_counts: Dict[str, int],
        round_from: Optional[int],
        round_to: Optional[int],
        highlights: Sequence[str],
        keywords: Sequence[str],
        existing_summary: str,
    ) -> str:
        response = self.llm.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "너는 다중 에이전트 시뮬레이션의 메모리 압축기다. "
                        "반드시 한국어로, 과장 없이, 검색과 보고서 작성에 바로 쓸 수 있는 2~3문장 요약만 반환해라. "
                        "중국어를 쓰지 마라. JSON 형식으로 summary_text만 반환해라."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "title": title,
                            "summary_scope": summary_scope,
                            "platform": platform,
                            "agent_name": agent_name,
                            "event_count": event_count,
                            "round_from": round_from,
                            "round_to": round_to,
                            "action_counts": action_counts,
                            "highlights": list(highlights)[:5],
                            "keywords": list(keywords)[:8],
                            "existing_summary": existing_summary,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=320,
        )
        summary_text = self._normalize_text(response.get("summary_text"))
        if not summary_text:
            raise ValueError("summary_text missing from LLM response")
        return summary_text

    def _build_title(self, group: Dict[str, Any]) -> str:
        summary_scope = group.get("summary_scope", "")
        platform = self._platform_label(group.get("platform", ""))
        agent_name = self._normalize_text(group.get("agent_name"))

        if summary_scope == "simulation":
            return "시뮬레이션 전체 기억"
        if summary_scope == "platform":
            return f"{platform} 흐름 요약" if platform else "플랫폼 흐름 요약"
        if summary_scope == "agent":
            subject = agent_name or f"agent-{group.get('agent_id')}"
            if platform:
                return f"{subject} {platform} 기억"
            return f"{subject} 기억"
        return "시뮬레이션 기억"

    def _build_summary_id(
        self,
        simulation_id: str,
        summary_scope: str,
        platform: str,
        agent_id: Any,
        agent_name: str,
    ) -> str:
        if summary_scope == "simulation":
            return f"memory::{simulation_id}::simulation"
        if summary_scope == "platform":
            return f"memory::{simulation_id}::platform::{platform or 'unknown'}"

        agent_part = self._slugify(agent_name) if agent_name else ""
        if agent_id is not None and str(agent_id).strip() != "":
            agent_part = f"id-{agent_id}"
        if not agent_part:
            agent_part = "unknown"
        return f"memory::{simulation_id}::agent::{platform or 'unknown'}::{agent_part}"

    def _extract_fragments(
        self,
        activity: Dict[str, Any],
        *,
        include_description: bool = True,
    ) -> List[str]:
        fragments: List[str] = []
        description = self._normalize_text(activity.get("description"))
        if include_description and description:
            fragments.append(description)

        action_args = activity.get("action_args") or {}
        if not isinstance(action_args, dict):
            return self._trim_fragments(fragments)

        preferred_keys = [
            "content",
            "quote_content",
            "query",
            "keyword",
            "post_content",
            "original_content",
            "comment_content",
            "target_user_name",
            "post_author_name",
            "original_author_name",
        ]
        for key in preferred_keys:
            value = self._normalize_text(action_args.get(key))
            if value:
                fragments.append(value)

        return self._trim_fragments(fragments)

    def _trim_fragments(self, values: Sequence[str]) -> List[str]:
        result: List[str] = []
        seen = set()
        for value in values:
            normalized = re.sub(r"\s+", " ", self._normalize_text(value)).strip(" .,:;\"'[]()")
            if len(normalized) < 3:
                continue
            if len(normalized) > 120:
                normalized = normalized[:117].rstrip() + "..."
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(normalized)
        return result[: self.max_recent]

    def _extract_keywords(self, texts: Sequence[str], limit: int = 8) -> List[str]:
        counter: Counter[str] = Counter()
        for text in texts:
            for token in re.findall(r"[0-9A-Za-z\uAC00-\uD7AF]{2,}", self._normalize_text(text).lower()):
                if token in self.KEYWORD_STOPWORDS:
                    continue
                counter[token] += 1
        return [token for token, _ in counter.most_common(limit)]

    def _format_action_counts(self, action_counts: Dict[str, int], limit: int = 4) -> str:
        if not action_counts:
            return ""
        parts = []
        for action, count in sorted(action_counts.items(), key=lambda item: (-item[1], item[0]))[:limit]:
            parts.append(f"{self.ACTION_LABELS.get(action, action)} {count}회")
        return ", ".join(parts)

    def _describe_activity(self, activity: Dict[str, Any]) -> str:
        action_type = self._normalize_text(activity.get("action_type")).upper()
        label = self.ACTION_LABELS.get(action_type, action_type or "행동")
        agent_name = self._normalize_text(activity.get("agent_name"))
        fragments = self._extract_fragments(activity, include_description=False)
        base = f"{agent_name} 활동 기록 - {label}" if agent_name else f"행동 기록 - {label}"
        if fragments:
            return f"{base}: {' / '.join(fragments[:2])}"
        return base

    def _normalize_clause_text(self, text: str) -> str:
        normalized = self._normalize_text(text)
        if not normalized:
            return ""
        return re.sub(r"[.!?]+$", "", normalized).strip()

    def _merge_action_counts(self, current: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, int]:
        merged: Dict[str, int] = {}
        for source in (current or {}, delta or {}):
            for key, value in source.items():
                merged[key] = int(merged.get(key, 0)) + int(value or 0)
        return merged

    def _merge_recent_values(self, current: Sequence[str], delta: Sequence[str]) -> List[str]:
        merged: List[str] = []
        seen = set()
        for value in [*(current or []), *(delta or [])]:
            normalized = self._normalize_text(value)
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(normalized)
        if len(merged) > self.max_recent:
            merged = merged[-self.max_recent :]
        return merged

    def _platform_label(self, platform: str) -> str:
        return self.PLATFORM_LABELS.get(platform, platform or "플랫폼")

    @staticmethod
    def _slugify(value: str) -> str:
        lowered = re.sub(r"[^0-9a-zA-Z]+", "-", (value or "").strip().lower())
        lowered = lowered.strip("-")
        return lowered[:48] or "unknown"

    @staticmethod
    def _to_mapping(value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return dict(value)
        if dataclasses.is_dataclass(value):
            return dataclasses.asdict(value)
        if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
            result = value.to_dict()
            if isinstance(result, dict):
                return dict(result)
        if hasattr(value, "__dict__"):
            return {k: v for k, v in vars(value).items() if not k.startswith("_")}
        return {}

    @staticmethod
    def _normalize_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    @staticmethod
    def _normalize_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except Exception:
            return None

    @staticmethod
    def _min_optional(*values: Optional[int]) -> Optional[int]:
        filtered = [value for value in values if value is not None]
        return min(filtered) if filtered else None

    @staticmethod
    def _max_optional(*values: Optional[int]) -> Optional[int]:
        filtered = [value for value in values if value is not None]
        return max(filtered) if filtered else None
