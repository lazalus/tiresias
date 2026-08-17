"""
그래프 메모리 업데이트 서비스
시뮬레이션의 Agent 활동을 그래프 저장소에 일괄적으로 기록합니다.

이 모듈은 이전 public API를 유지하지만, 내부적으로 더 이상 Zep에 의존하지 않고,
대신 Neo4j 그래프 저장소의 append_activity 인터페이스를 통해 활동을 기록합니다.
"""

import importlib
import json
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from queue import Empty, Queue
from typing import Any, Callable, Dict, List, Optional

from ..config import Config
from ..utils.logger import get_logger
from .simulation_memory_compactor import SimulationMemoryCompactor

logger = get_logger('tiresias.zep_graph_memory_updater')


@dataclass
class AgentActivity:
    """Agent 활동 기록"""
    simulation_id: str
    platform: str
    agent_id: int
    agent_name: str
    action_type: str
    action_args: Dict[str, Any]
    round_num: int
    timestamp: str

    def _stable_activity_uuid(self) -> str:
        """활동에 대한 안정적인 UUID를 생성하여 재시도 시 중복 제거를 용이하게 합니다."""
        payload = json.dumps(
            {
                "simulation_id": self.simulation_id,
                "platform": self.platform,
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "action_type": self.action_type,
                "action_args": self.action_args,
                "round_num": self.round_num,
                "timestamp": self.timestamp,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return uuid.uuid5(uuid.NAMESPACE_URL, payload).hex

    def to_episode_text(self) -> str:
        """
        활동을 자연어 설명으로 변환하여 그래프 저장 및 검색에 사용합니다.
        """
        action_descriptions = {
            "CREATE_POST": self._describe_create_post,
            "LIKE_POST": self._describe_like_post,
            "DISLIKE_POST": self._describe_dislike_post,
            "REPOST": self._describe_repost,
            "QUOTE_POST": self._describe_quote_post,
            "FOLLOW": self._describe_follow,
            "CREATE_COMMENT": self._describe_create_comment,
            "LIKE_COMMENT": self._describe_like_comment,
            "DISLIKE_COMMENT": self._describe_dislike_comment,
            "SEARCH_POSTS": self._describe_search,
            "SEARCH_USER": self._describe_search_user,
            "MUTE": self._describe_mute,
        }

        describe_func = action_descriptions.get(self.action_type, self._describe_generic)
        return f"{self.agent_name}: {describe_func()}"

    def _build_search_text(self) -> str:
        """전체 텍스트 검색에 사용될 텍스트를 구성합니다."""
        text_parts = [
            self.simulation_id,
            self.platform,
            self.agent_name,
            self.action_type,
            self.to_episode_text(),
            f"round:{self.round_num}",
            f"timestamp:{self.timestamp}",
        ]

        for key in sorted(self.action_args.keys()):
            value = self.action_args.get(key)
            if value is None:
                continue
            if isinstance(value, (dict, list, tuple, set)):
                try:
                    value_text = json.dumps(value, ensure_ascii=False, sort_keys=True)
                except Exception:
                    value_text = str(value)
            else:
                value_text = str(value)

            if value_text.strip():
                text_parts.append(f"{key}:{value_text}")

        return "\n".join(text_parts)

    def to_dict(self) -> Dict[str, Any]:
        """표준 사전으로 변환합니다."""
        return {
            "activity_uuid": self._stable_activity_uuid(),
            "simulation_id": self.simulation_id,
            "platform": self.platform,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "action_type": self.action_type,
            "action_args": self.action_args,
            "round_num": self.round_num,
            "timestamp": self.timestamp,
            "description": self.to_episode_text(),
            "search_text": self._build_search_text(),
        }

    def to_graph_payload(self, graph_id: str) -> Dict[str, Any]:
        """그래프 저장소에 필요한 페이로드를 변환합니다."""
        payload = self.to_dict()
        payload.update(
            {
                "graph_id": graph_id,
                "created_at": datetime.now().isoformat(),
                "source": "simulation_activity",
                "source_type": "agent_activity",
            }
        )
        return payload

    def _describe_create_post(self) -> str:
        content = self.action_args.get("content", "")
        if content:
            return f"게시물을 작성했습니다: 「{content}」"
        return "게시물을 작성했습니다"

    def _describe_like_post(self) -> str:
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")

        if post_content and post_author:
            return f"{post_author}의 게시물에 좋아요를 눌렀습니다: 「{post_content}」"
        if post_content:
            return f"게시물에 좋아요를 눌렀습니다: 「{post_content}」"
        if post_author:
            return f"{post_author}의 게시물에 좋아요를 눌렀습니다"
        return "게시물에 좋아요를 눌렀습니다"

    def _describe_dislike_post(self) -> str:
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")

        if post_content and post_author:
            return f"{post_author}의 게시물에 싫어요를 눌렀습니다: 「{post_content}」"
        if post_content:
            return f"게시물에 싫어요를 눌렀습니다: 「{post_content}」"
        if post_author:
            return f"{post_author}의 게시물에 싫어요를 눌렀습니다"
        return "게시물에 싫어요를 눌렀습니다"

    def _describe_repost(self) -> str:
        original_content = self.action_args.get("original_content", "")
        original_author = self.action_args.get("original_author_name", "")

        if original_content and original_author:
            return f"{original_author}의 게시물을 리포스트했습니다: 「{original_content}」"
        if original_content:
            return f"게시물을 리포스트했습니다: 「{original_content}」"
        if original_author:
            return f"{original_author}의 게시물을 리포스트했습니다"
        return "게시물을 리포스트했습니다"

    def _describe_quote_post(self) -> str:
        original_content = self.action_args.get("original_content", "")
        original_author = self.action_args.get("original_author_name", "")
        quote_content = self.action_args.get("quote_content", "") or self.action_args.get("content", "")

        if original_content and original_author:
            base = f"{original_author}의 게시물 「{original_content}」을 인용했습니다"
        elif original_content:
            base = f"게시물 「{original_content}」을 인용했습니다"
        elif original_author:
            base = f"{original_author}의 게시물을 인용했습니다"
        else:
            base = "게시물을 인용했습니다"

        if quote_content:
            base += f", 그리고 다음과 같이 댓글을 달았습니다: 「{quote_content}」"
        return base

    def _describe_follow(self) -> str:
        target_user_name = self.action_args.get("target_user_name", "")
        if target_user_name:
            return f"사용자 「{target_user_name}」을 팔로우했습니다"
        return "사용자를 팔로우했습니다"

    def _describe_create_comment(self) -> str:
        content = self.action_args.get("content", "")
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")

        if content:
            if post_content and post_author:
                return f"{post_author}의 게시물 「{post_content}」에 댓글을 달았습니다: 「{content}」"
            if post_content:
                return f"게시물 「{post_content}」에 댓글을 달았습니다: 「{content}」"
            if post_author:
                return f"{post_author}의 게시물에 댓글을 달았습니다: 「{content}」"
            return f"댓글을 달았습니다: 「{content}」"
        return "댓글을 작성했습니다"

    def _describe_like_comment(self) -> str:
        comment_content = self.action_args.get("comment_content", "")
        comment_author = self.action_args.get("comment_author_name", "")

        if comment_content and comment_author:
            return f"{comment_author}의 댓글에 좋아요를 눌렀습니다: 「{comment_content}」"
        if comment_content:
            return f"댓글에 좋아요를 눌렀습니다: 「{comment_content}」"
        if comment_author:
            return f"{comment_author}의 댓글에 좋아요를 눌렀습니다"
        return "댓글에 좋아요를 눌렀습니다"

    def _describe_dislike_comment(self) -> str:
        comment_content = self.action_args.get("comment_content", "")
        comment_author = self.action_args.get("comment_author_name", "")

        if comment_content and comment_author:
            return f"{comment_author}의 댓글에 싫어요를 눌렀습니다: 「{comment_content}」"
        if comment_content:
            return f"댓글에 싫어요를 눌렀습니다: 「{comment_content}」"
        if comment_author:
            return f"{comment_author}의 댓글에 싫어요를 눌렀습니다"
        return "댓글에 싫어요를 눌렀습니다"

    def _describe_search(self) -> str:
        query = self.action_args.get("query", "") or self.action_args.get("keyword", "")
        return f"「{query}」을 검색했습니다" if query else "검색을 수행했습니다"

    def _describe_search_user(self) -> str:
        query = self.action_args.get("query", "") or self.action_args.get("username", "")
        return f"사용자 「{query}」을 검색했습니다" if query else "사용자를 검색했습니다"

    def _describe_mute(self) -> str:
        target_user_name = self.action_args.get("target_user_name", "")
        if target_user_name:
            return f"사용자 「{target_user_name}」을 차단했습니다"
        return "사용자를 차단했습니다"

    def _describe_generic(self) -> str:
        return f"{self.action_type} 작업을 실행했습니다"


class _Neo4jGraphStoreAdapter:
    """
    런타임 그래프 저장소 어댑터.

    지연 로딩을 통해 미래의 Neo4j 그래프 저장소 구현을 가져와 모듈 로딩 단계에서
    특정 저장소 구현에 의존하는 것을 방지합니다. 저장소가 아직 사용 가능하지 않으면, 첫 쓰기 시 명확한 오류가 발생합니다.
    """

    def __init__(self):
        self._backend = None
        self._resolved = False
        self._resolve_lock = threading.Lock()

    def _resolve(self):
        if self._resolved:
            return self._backend

        with self._resolve_lock:
            if self._resolved:
                return self._backend

            self._resolved = True

            try:
                module = importlib.import_module(".neo4j_graph_store", package=__package__)
            except Exception as exc:
                logger.warning(f"Neo4j 그래프 저장소 모듈이 아직 사용 가능하지 않습니다: {exc}")
                self._backend = None
                return None

            for factory_name in ("get_graph_store",):
                factory = getattr(module, factory_name, None)
                if callable(factory):
                    try:
                        self._backend = factory()
                        return self._backend
                    except Exception as exc:
                        logger.warning(f"{factory_name}을 통해 Neo4j 그래프 저장소 초기화 실패: {exc}")

            for class_name in ("Neo4jGraphStore", "GraphStore"):
                cls = getattr(module, class_name, None)
                if cls is not None:
                    try:
                        self._backend = cls()
                        return self._backend
                    except Exception as exc:
                        logger.warning(f"{class_name} 인스턴스화 실패: {exc}")

            self._backend = module
            return self._backend

    @staticmethod
    def _call_with_compatibility(func: Callable[..., Any], graph_id: str, payload: Any, payload_names: List[str]) -> Any:
        """다양한 호출 시그니처와 최대한 호환되도록 합니다."""
        attempts = [lambda: func(graph_id, payload)]

        for name in payload_names:
            attempts.append(lambda name=name: func(graph_id=graph_id, **{name: payload}))

        attempts.extend(
            [
                lambda: func(payload),
                lambda: func(**{payload_names[0]: payload}),
            ]
        )

        last_type_error: Optional[TypeError] = None
        for attempt in attempts:
            try:
                return attempt()
            except TypeError as exc:
                last_type_error = exc

        if last_type_error is not None:
            raise last_type_error
        raise RuntimeError("그래프 저장소 쓰기 인터페이스를 호출할 수 없습니다")

    def append_activity(self, graph_id: str, activity_payload: Dict[str, Any]) -> Any:
        backend = self._resolve()
        if backend is None:
            raise RuntimeError("Neo4j 그래프 저장소를 사용할 수 없습니다")

        append_func = getattr(backend, "append_activity", None)
        if not callable(append_func):
            raise AttributeError("그래프 저장소가 append_activity(graph_id, activity_dict)를 구현하지 않았습니다")

        return self._call_with_compatibility(
            append_func,
            graph_id,
            activity_payload,
            ["activity_dict", "activity", "payload"],
        )

    def append_activities(self, graph_id: str, activity_payloads: List[Dict[str, Any]]) -> Any:
        backend = self._resolve()
        if backend is None:
            raise RuntimeError("Neo4j 그래프 저장소를 사용할 수 없습니다")

        batch_func = getattr(backend, "append_activity_batch", None) or getattr(backend, "append_activities", None)
        if callable(batch_func):
            return self._call_with_compatibility(
                batch_func,
                graph_id,
                activity_payloads,
                ["activities", "activity_dicts", "payloads"],
            )

        results = []
        for payload in activity_payloads:
            results.append(self.append_activity(graph_id, payload))
        return results


class ZepGraphMemoryUpdater:
    """
    그래프 메모리 업데이트기

    시뮬레이션의 actions 로그 파일을 모니터링하고, 새로운 agent 활동을 Neo4j 그래프에 실시간으로 업데이트합니다.
    플랫폼별로 그룹화하여 BATCH_SIZE개의 활동이 누적될 때마다 일괄적으로 전송합니다.
    """

    BATCH_SIZE = 5

    PLATFORM_DISPLAY_NAMES = {
        "twitter": "세계1",
        "reddit": "세계2",
    }

    SEND_INTERVAL = 0.5
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self, graph_id: str, api_key: Optional[str] = None):
        """
        업데이트기를 초기화합니다.

        api_key 매개변수는 이전 호출자와의 호환성을 위해서만 유지되며, 더 이상 사용되지 않습니다.
        """
        self.graph_id = graph_id
        self.simulation_id = ""
        self.api_key = api_key

        self._graph_store = _Neo4jGraphStoreAdapter()
        self._memory_compactor: Optional[SimulationMemoryCompactor] = None

        self._activity_queue: Queue = Queue()
        self._platform_buffers: Dict[str, List[AgentActivity]] = {
            "twitter": [],
            "reddit": [],
        }
        self._buffer_lock = threading.Lock()
        self._send_lock = threading.Lock()

        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

        self._total_activities = 0
        self._total_sent = 0
        self._total_items_sent = 0
        self._failed_count = 0
        self._skipped_count = 0

        logger.info(f"그래프 메모리 업데이트기 초기화 완료: graph_id={graph_id}, batch_size={self.BATCH_SIZE}")

    def bind_simulation(self, simulation_id: str):
        """Bind a simulation id and initialize compaction state."""
        self.simulation_id = simulation_id
        self._memory_compactor = (
            SimulationMemoryCompactor(
                graph_id=self.graph_id,
                simulation_id=simulation_id,
                use_llm=False,
            )
            if Config.MEMORY_SUMMARY_ENABLED
            else None
        )

    def _get_platform_display_name(self, platform: str) -> str:
        return self.PLATFORM_DISPLAY_NAMES.get(platform.lower(), platform)

    def start(self):
        """백그라운드 작업 스레드를 시작합니다."""
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name=f"GraphMemoryUpdater-{self.graph_id[:8]}",
        )
        self._worker_thread.start()
        logger.info(f"그래프 메모리 업데이트기가 시작되었습니다: graph_id={self.graph_id}")

    def stop(self):
        """백그라운드 작업 스레드를 중지하고 남은 활동을 플러시합니다."""
        self._running = False

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=10)
            if self._worker_thread.is_alive():
                logger.warning("그래프 메모리 업데이트기 종료 대기 시간이 초과되어 잔여 버퍼를 강제로 플러시합니다")

        self._flush_remaining()

        if self._memory_compactor:
            try:
                self._memory_compactor.flush()
            except Exception as exc:
                logger.warning(f"압축된 메모리 플러시 실패: {exc}")

        logger.info(
            f"그래프 메모리 업데이트기가 중지되었습니다: graph_id={self.graph_id}, "
            f"total_activities={self._total_activities}, "
            f"batches_sent={self._total_sent}, "
            f"items_sent={self._total_items_sent}, "
            f"failed={self._failed_count}, "
            f"skipped={self._skipped_count}"
        )

    def add_activity(self, activity: AgentActivity):
        """
        큐에 agent 활동을 추가합니다.
        """
        if activity.action_type == "DO_NOTHING":
            self._skipped_count += 1
            return

        self._activity_queue.put(activity)
        self._total_activities += 1
        logger.debug(f"그래프 큐에 활동 추가: {activity.agent_name} - {activity.action_type}")

    def add_activity_from_dict(self, data: Dict[str, Any], platform: str):
        """
        사전 데이터에서 활동을 추가합니다.
        """
        if "event_type" in data:
            return

        activity = AgentActivity(
            simulation_id=self.simulation_id,
            platform=platform,
            agent_id=data.get("agent_id", 0),
            agent_name=data.get("agent_name", ""),
            action_type=data.get("action_type", ""),
            action_args=data.get("action_args") or {},
            round_num=data.get("round", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )

        self.add_activity(activity)

    def _worker_loop(self):
        """백그라운드 작업 루프 - 플랫폼별로 활동을 일괄 전송합니다."""
        while self._running or not self._activity_queue.empty():
            try:
                try:
                    activity = self._activity_queue.get(timeout=1)
                    platform = activity.platform.lower()

                    batch_to_send: Optional[List[AgentActivity]] = None
                    with self._buffer_lock:
                        if platform not in self._platform_buffers:
                            self._platform_buffers[platform] = []
                        self._platform_buffers[platform].append(activity)

                        if len(self._platform_buffers[platform]) >= self.BATCH_SIZE:
                            batch_to_send = self._platform_buffers[platform][: self.BATCH_SIZE]
                            self._platform_buffers[platform] = self._platform_buffers[platform][self.BATCH_SIZE :]

                    if batch_to_send:
                        self._send_batch_activities(batch_to_send, platform)
                        time.sleep(self.SEND_INTERVAL)
                except Empty:
                    pass
            except Exception as exc:
                logger.error(f"작업 루프 예외 발생: {exc}")
                time.sleep(1)

    def _send_batch_activities(self, activities: List[AgentActivity], platform: str):
        """
        Neo4j 그래프에 활동을 일괄 전송합니다.
        """
        if not activities:
            return

        payloads = [activity.to_graph_payload(self.graph_id) for activity in activities]

        with self._send_lock:
            last_error: Optional[Exception] = None

            for attempt in range(self.MAX_RETRIES):
                try:
                    self._graph_store.append_activities(self.graph_id, payloads)
                    if self._memory_compactor:
                        self._memory_compactor.ingest(activities)

                    self._total_sent += 1
                    self._total_items_sent += len(activities)
                    display_name = self._get_platform_display_name(platform)
                    logger.info(f"{len(activities)}개의 {display_name} 활동을 그래프 {self.graph_id}에 성공적으로 일괄 전송했습니다")
                    logger.debug(f"일괄 내용 미리보기: {payloads[0].get('description', '')[:200]}...")
                    return
                except Exception as exc:
                    last_error = exc
                    if attempt < self.MAX_RETRIES - 1:
                        logger.warning(
                            f"Neo4j 일괄 쓰기 실패 (시도 {attempt + 1}/{self.MAX_RETRIES}): {exc}"
                        )
                        time.sleep(self.RETRY_DELAY * (attempt + 1))
                    else:
                        logger.error(
                            f"Neo4j 일괄 쓰기 실패, {self.MAX_RETRIES}회 재시도 완료: {exc}"
                        )

            if last_error is not None:
                self._failed_count += 1

    def _flush_remaining(self):
        """큐와 버퍼에 남아있는 활동을 전송합니다."""
        while not self._activity_queue.empty():
            try:
                activity = self._activity_queue.get_nowait()
                platform = activity.platform.lower()
                with self._buffer_lock:
                    if platform not in self._platform_buffers:
                        self._platform_buffers[platform] = []
                    self._platform_buffers[platform].append(activity)
            except Empty:
                break

        with self._buffer_lock:
            buffers_snapshot = {
                platform: list(buffer)
                for platform, buffer in self._platform_buffers.items()
                if buffer
            }
            for platform in self._platform_buffers:
                self._platform_buffers[platform] = []

        for platform, buffer in buffers_snapshot.items():
            display_name = self._get_platform_display_name(platform)
            logger.info(f"{display_name} 플랫폼에 남아있는 {len(buffer)}개의 활동 전송")
            self._send_batch_activities(buffer, platform)

    def get_stats(self) -> Dict[str, Any]:
        """통계 정보를 가져옵니다."""
        with self._buffer_lock:
            buffer_sizes = {platform: len(buffer) for platform, buffer in self._platform_buffers.items()}

        return {
            "graph_id": self.graph_id,
            "batch_size": self.BATCH_SIZE,
            "total_activities": self._total_activities,
            "batches_sent": self._total_sent,
            "items_sent": self._total_items_sent,
            "failed_count": self._failed_count,
            "skipped_count": self._skipped_count,
            "queue_size": self._activity_queue.qsize(),
            "buffer_sizes": buffer_sizes,
            "running": self._running,
            "memory_compaction": self._memory_compactor.get_stats() if self._memory_compactor else None,
        }


class ZepGraphMemoryManager:
    """
    여러 시뮬레이션의 그래프 메모리 업데이트기를 관리합니다.
    """

    _updaters: Dict[str, ZepGraphMemoryUpdater] = {}
    _lock = threading.Lock()

    @classmethod
    def create_updater(cls, simulation_id: str, graph_id: str) -> ZepGraphMemoryUpdater:
        """
        시뮬레이션을 위한 그래프 메모리 업데이트기를 생성합니다.
        """
        with cls._lock:
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()

            updater = ZepGraphMemoryUpdater(graph_id)
            updater.bind_simulation(simulation_id)
            updater.start()
            cls._updaters[simulation_id] = updater

            logger.info(f"그래프 메모리 업데이트기 생성: simulation_id={simulation_id}, graph_id={graph_id}")
            return updater

    @classmethod
    def get_updater(cls, simulation_id: str) -> Optional[ZepGraphMemoryUpdater]:
        """시뮬레이션의 업데이트기를 가져옵니다."""
        return cls._updaters.get(simulation_id)

    @classmethod
    def stop_updater(cls, simulation_id: str):
        """시뮬레이션의 업데이트기를 중지하고 제거합니다."""
        with cls._lock:
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()
                del cls._updaters[simulation_id]
                logger.info(f"그래프 메모리 업데이트기가 중지되었습니다: simulation_id={simulation_id}")

    _stop_all_done = False

    @classmethod
    def stop_all(cls):
        """모든 업데이트기를 중지합니다."""
        if cls._stop_all_done:
            return
        cls._stop_all_done = True

        with cls._lock:
            if cls._updaters:
                for simulation_id, updater in list(cls._updaters.items()):
                    try:
                        updater.stop()
                    except Exception as exc:
                        logger.error(f"업데이트기 중지 실패: simulation_id={simulation_id}, error={exc}")
                cls._updaters.clear()
            logger.info("모든 그래프 메모리 업데이트기가 중지되었습니다")

    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """모든 업데이트기의 통계 정보를 가져옵니다."""
        return {
            sim_id: updater.get_stats()
            for sim_id, updater in cls._updaters.items()
        }
