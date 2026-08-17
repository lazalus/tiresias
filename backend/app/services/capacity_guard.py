"""
서버 과부하 방지용 전역 용량 가드
"""

from dataclasses import dataclass
from typing import Dict, Any

from ..config import Config
from ..models.task import TaskManager
from ..utils.logger import get_logger
from .simulation_runner import SimulationRunner

logger = get_logger('tiresias.capacity')


@dataclass
class CapacitySnapshot:
    """현재 서버 작업 점유 현황"""

    preparing: int
    graph_building: int
    report_generating: int
    running_simulations: int
    warm_simulation_envs: int
    alive_simulation_envs: int
    heavy_jobs: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preparing": self.preparing,
            "graph_building": self.graph_building,
            "report_generating": self.report_generating,
            "running_simulations": self.running_simulations,
            "warm_simulation_envs": self.warm_simulation_envs,
            "alive_simulation_envs": self.alive_simulation_envs,
            "heavy_jobs": self.heavy_jobs,
            "limits": {
                "max_concurrent_prepares": Config.MAX_CONCURRENT_PREPARES,
                "max_concurrent_graph_builds": Config.MAX_CONCURRENT_GRAPH_BUILDS,
                "max_concurrent_reports": Config.MAX_CONCURRENT_REPORTS,
                "max_concurrent_running_simulations": Config.MAX_CONCURRENT_RUNNING_SIMULATIONS,
                "max_concurrent_simulation_envs": Config.MAX_CONCURRENT_SIMULATION_ENVS,
                "max_concurrent_heavy_jobs": Config.MAX_CONCURRENT_HEAVY_JOBS,
                "simulation_env_ttl_seconds": Config.SIMULATION_ENV_TTL_SECONDS,
            },
        }


class CapacityExceededError(RuntimeError):
    """용량 한도 초과 예외"""

    def __init__(self, message: str, snapshot: CapacitySnapshot):
        super().__init__(message)
        self.snapshot = snapshot

    def to_payload(self) -> Dict[str, Any]:
        return {
            "success": False,
            "error": str(self),
            "capacity": self.snapshot.to_dict(),
        }


class CapacityGuard:
    """전역 작업 점유량을 계산하고 새 작업 시작 가능 여부를 판단합니다."""

    @classmethod
    def snapshot(cls) -> CapacitySnapshot:
        task_manager = TaskManager()
        process_counts = SimulationRunner.count_process_slots()

        preparing = task_manager.count_active_tasks("simulation_prepare")
        graph_building = task_manager.count_active_tasks("graph_build")
        report_generating = task_manager.count_active_tasks("report_generate")
        running_simulations = process_counts["running"]
        warm_simulation_envs = process_counts["warm"]
        alive_simulation_envs = process_counts["alive"]
        heavy_jobs = preparing + graph_building + report_generating + running_simulations

        return CapacitySnapshot(
            preparing=preparing,
            graph_building=graph_building,
            report_generating=report_generating,
            running_simulations=running_simulations,
            warm_simulation_envs=warm_simulation_envs,
            alive_simulation_envs=alive_simulation_envs,
            heavy_jobs=heavy_jobs,
        )

    @classmethod
    def _ensure_under_limit(
        cls,
        current: int,
        limit: int,
        message: str,
        snapshot: CapacitySnapshot
    ) -> None:
        if limit > 0 and current >= limit:
            logger.warning("용량 제한 도달: %s | snapshot=%s", message, snapshot.to_dict())
            raise CapacityExceededError(message, snapshot)

    @classmethod
    def _ensure_global_heavy_job_capacity(cls, snapshot: CapacitySnapshot) -> None:
        cls._ensure_under_limit(
            snapshot.heavy_jobs,
            Config.MAX_CONCURRENT_HEAVY_JOBS,
            "현재 서버가 바빠 새 작업을 시작할 수 없습니다. 잠시 후 다시 시도해주세요.",
            snapshot,
        )

    @classmethod
    def ensure_prepare_capacity(cls) -> CapacitySnapshot:
        snapshot = cls.snapshot()
        cls._ensure_under_limit(
            snapshot.preparing,
            Config.MAX_CONCURRENT_PREPARES,
            "현재 다른 시뮬레이션 준비 작업이 진행 중입니다. 잠시 후 다시 시도해주세요.",
            snapshot,
        )
        cls._ensure_global_heavy_job_capacity(snapshot)
        return snapshot

    @classmethod
    def ensure_graph_build_capacity(cls) -> CapacitySnapshot:
        snapshot = cls.snapshot()
        cls._ensure_under_limit(
            snapshot.graph_building,
            Config.MAX_CONCURRENT_GRAPH_BUILDS,
            "현재 다른 그래프 구축 작업이 진행 중입니다. 잠시 후 다시 시도해주세요.",
            snapshot,
        )
        cls._ensure_global_heavy_job_capacity(snapshot)
        return snapshot

    @classmethod
    def ensure_report_capacity(cls) -> CapacitySnapshot:
        snapshot = cls.snapshot()
        cls._ensure_under_limit(
            snapshot.report_generating,
            Config.MAX_CONCURRENT_REPORTS,
            "현재 다른 보고서 생성 작업이 진행 중입니다. 잠시 후 다시 시도해주세요.",
            snapshot,
        )
        cls._ensure_global_heavy_job_capacity(snapshot)
        return snapshot

    @classmethod
    def ensure_simulation_start_capacity(cls) -> CapacitySnapshot:
        snapshot = cls.snapshot()
        cls._ensure_under_limit(
            snapshot.running_simulations,
            Config.MAX_CONCURRENT_RUNNING_SIMULATIONS,
            "현재 실행 중인 시뮬레이션이 많아 새 시뮬레이션을 시작할 수 없습니다. 잠시 후 다시 시도해주세요.",
            snapshot,
        )
        cls._ensure_under_limit(
            snapshot.alive_simulation_envs,
            Config.MAX_CONCURRENT_SIMULATION_ENVS,
            "기존 시뮬레이션 환경이 아직 정리되지 않아 새 시뮬레이션을 시작할 수 없습니다. 잠시 후 다시 시도해주세요.",
            snapshot,
        )
        cls._ensure_global_heavy_job_capacity(snapshot)
        return snapshot
