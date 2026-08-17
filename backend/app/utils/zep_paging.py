"""Zep Graph 페이지별 읽기 도구.

Zep의 노드/엣지 목록 인터페이스는 UUID 커서로 페이지를 나누며,
이 모듈은 자동 페이지 넘김 로직(단일 페이지 재시도 포함)을 캡슐화하여 호출자에게 투명하게 전체 목록을 반환합니다.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

try:
    from zep_cloud import InternalServerError
    from zep_cloud.client import Zep
except Exception:  # pragma: no cover - legacy compatibility when Zep is removed
    class InternalServerError(Exception):
        """Fallback placeholder used when zep-cloud is no longer installed."""

    Zep = Any  # type: ignore[assignment]

from .logger import get_logger

logger = get_logger('tiresias.zep_paging')

_DEFAULT_PAGE_SIZE = 100
_MAX_NODES = 2000
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_RETRY_DELAY = 2.0  # seconds, doubles each retry


def _extract_rate_limit_delay(exc: Exception, fallback: float) -> float:
    headers = getattr(exc, "headers", None)
    if isinstance(headers, dict):
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
        if retry_after:
            try:
                return max(float(retry_after), fallback)
            except (TypeError, ValueError):
                return fallback
    return fallback


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, (ConnectionError, TimeoutError, OSError, InternalServerError)):
        return True

    status_code = getattr(exc, "status_code", None)
    message = str(exc)
    if status_code == 429:
        return True
    return "status_code: 429" in message or "Rate limit exceeded" in message


def _fetch_page_with_retry(
    api_call: Callable[..., list[Any]],
    *args: Any,
    max_retries: int = _DEFAULT_MAX_RETRIES,
    retry_delay: float = _DEFAULT_RETRY_DELAY,
    page_description: str = "page",
    **kwargs: Any,
) -> list[Any]:
    """단일 페이지 요청, 실패 시 지수 백오프 재시도. 네트워크/IO 유형의 일시적인 오류만 재시도합니다."""
    if max_retries < 1:
        raise ValueError("max_retries must be >= 1")

    last_exception: Exception | None = None
    delay = retry_delay

    for attempt in range(max_retries):
        try:
            return api_call(*args, **kwargs)
        except Exception as e:
            if not _is_retryable_exception(e):
                raise
            last_exception = e
            if attempt < max_retries - 1:
                wait_seconds = _extract_rate_limit_delay(e, delay)
                logger.warning(
                    f"Zep {page_description} attempt {attempt + 1} failed: {str(e)[:100]}, retrying in {wait_seconds:.1f}s..."
                )
                time.sleep(wait_seconds)
                delay = max(delay * 2, wait_seconds)
            else:
                logger.error(f"Zep {page_description} failed after {max_retries} attempts: {str(e)}")

    assert last_exception is not None
    raise last_exception


def fetch_all_nodes(
    client: Zep,
    graph_id: str,
    page_size: int = _DEFAULT_PAGE_SIZE,
    max_items: int = _MAX_NODES,
    max_retries: int = _DEFAULT_MAX_RETRIES,
    retry_delay: float = _DEFAULT_RETRY_DELAY,
) -> list[Any]:
    """그래프 노드를 페이지별로 가져오며, 최대 max_items개(기본값 2000)를 반환합니다. 각 페이지 요청에는 재시도가 포함됩니다."""
    all_nodes: list[Any] = []
    cursor: str | None = None
    page_num = 0

    while True:
        kwargs: dict[str, Any] = {"limit": page_size}
        if cursor is not None:
            kwargs["uuid_cursor"] = cursor

        page_num += 1
        batch = _fetch_page_with_retry(
            client.graph.node.get_by_graph_id,
            graph_id,
            max_retries=max_retries,
            retry_delay=retry_delay,
            page_description=f"fetch nodes page {page_num} (graph={graph_id})",
            **kwargs,
        )
        if not batch:
            break

        all_nodes.extend(batch)
        if len(all_nodes) >= max_items:
            all_nodes = all_nodes[:max_items]
            logger.warning(f"Node count reached limit ({max_items}), stopping pagination for graph {graph_id}")
            break
        if len(batch) < page_size:
            break

        cursor = getattr(batch[-1], "uuid_", None) or getattr(batch[-1], "uuid", None)
        if cursor is None:
            logger.warning(f"Node missing uuid field, stopping pagination at {len(all_nodes)} nodes")
            break

    return all_nodes


def fetch_all_edges(
    client: Zep,
    graph_id: str,
    page_size: int = _DEFAULT_PAGE_SIZE,
    max_retries: int = _DEFAULT_MAX_RETRIES,
    retry_delay: float = _DEFAULT_RETRY_DELAY,
) -> list[Any]:
    """그래프의 모든 엣지를 페이지별로 가져오며, 전체 목록을 반환합니다. 각 페이지 요청에는 재시도가 포함됩니다."""
    all_edges: list[Any] = []
    cursor: str | None = None
    page_num = 0

    while True:
        kwargs: dict[str, Any] = {"limit": page_size}
        if cursor is not None:
            kwargs["uuid_cursor"] = cursor

        page_num += 1
        batch = _fetch_page_with_retry(
            client.graph.edge.get_by_graph_id,
            graph_id,
            max_retries=max_retries,
            retry_delay=retry_delay,
            page_description=f"fetch edges page {page_num} (graph={graph_id})",
            **kwargs,
        )
        if not batch:
            break

        all_edges.extend(batch)
        if len(batch) < page_size:
            break

        cursor = getattr(batch[-1], "uuid_", None) or getattr(batch[-1], "uuid", None)
        if cursor is None:
            logger.warning(f"Edge missing uuid field, stopping pagination at {len(all_edges)} edges")
            break

    return all_edges