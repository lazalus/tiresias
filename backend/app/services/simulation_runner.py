"""
OASIS 시뮬레이션 실행기
백그라운드에서 시뮬레이션을 실행하고 각 Agent의 동작을 기록하며, 실시간 상태 모니터링을 지원합니다.
"""

import os
import sys
import json
import time
import asyncio
import threading
import subprocess
import signal
import atexit
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import Queue

from ..config import Config
from ..utils.logger import get_logger
from .zep_graph_memory_updater import ZepGraphMemoryManager
from .simulation_ipc import SimulationIPCClient, CommandType, IPCResponse

logger = get_logger('tiresias.simulation_runner')

# 정리 함수 등록 여부 표시
_cleanup_registered = False

# 플랫폼 감지
IS_WINDOWS = sys.platform == 'win32'


class RunnerStatus(str, Enum):
    """실행기 상태"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentAction:
    """Agent 동작 기록"""
    round_num: int
    timestamp: str
    platform: str  # twitter / reddit
    agent_id: int
    agent_name: str
    action_type: str  # CREATE_POST, LIKE_POST, etc.
    action_args: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "timestamp": self.timestamp,
            "platform": self.platform,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "action_type": self.action_type,
            "action_args": self.action_args,
            "result": self.result,
            "success": self.success,
        }


@dataclass
class RoundSummary:
    """각 라운드 요약"""
    round_num: int
    start_time: str
    end_time: Optional[str] = None
    simulated_hour: int = 0
    twitter_actions: int = 0
    reddit_actions: int = 0
    active_agents: List[int] = field(default_factory=list)
    actions: List[AgentAction] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "simulated_hour": self.simulated_hour,
            "twitter_actions": self.twitter_actions,
            "reddit_actions": self.reddit_actions,
            "active_agents": self.active_agents,
            "actions_count": len(self.actions),
            "actions": [a.to_dict() for a in self.actions],
        }


@dataclass
class SimulationRunState:
    """시뮬레이션 실행 상태 (실시간)"""
    simulation_id: str
    runner_status: RunnerStatus = RunnerStatus.IDLE
    
    # 진행 정보
    current_round: int = 0
    total_rounds: int = 0
    simulated_hours: int = 0
    total_simulation_hours: int = 0
    
    # 각 플랫폼 독립 라운드 및 시뮬레이션 시간 (양 플랫폼 병렬 표시용)
    twitter_current_round: int = 0
    reddit_current_round: int = 0
    twitter_simulated_hours: int = 0
    reddit_simulated_hours: int = 0
    
    # 플랫폼 상태
    twitter_running: bool = False
    reddit_running: bool = False
    twitter_actions_count: int = 0
    reddit_actions_count: int = 0
    
    # 플랫폼 완료 상태 (actions.jsonl의 simulation_end 이벤트 감지를 통해)
    twitter_completed: bool = False
    reddit_completed: bool = False
    
    # 각 라운드 요약
    rounds: List[RoundSummary] = field(default_factory=list)
    
    # 최근 동작 (프론트엔드 실시간 표시용)
    recent_actions: List[AgentAction] = field(default_factory=list)
    max_recent_actions: int = 50
    
    # 타임스탬프
    started_at: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    
    # 오류 정보
    error: Optional[str] = None
    
    # 프로세스 ID (중지용)
    process_pid: Optional[int] = None
    
    def add_action(self, action: AgentAction):
        """최근 동작 목록에 동작 추가"""
        self.recent_actions.insert(0, action)
        if len(self.recent_actions) > self.max_recent_actions:
            self.recent_actions = self.recent_actions[:self.max_recent_actions]
        
        if action.platform == "twitter":
            self.twitter_actions_count += 1
        else:
            self.reddit_actions_count += 1
        
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "runner_status": self.runner_status.value,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "simulated_hours": self.simulated_hours,
            "total_simulation_hours": self.total_simulation_hours,
            "progress_percent": round(self.current_round / max(self.total_rounds, 1) * 100, 1),
            # 각 플랫폼 독립 라운드 및 시간
            "twitter_current_round": self.twitter_current_round,
            "reddit_current_round": self.reddit_current_round,
            "twitter_simulated_hours": self.twitter_simulated_hours,
            "reddit_simulated_hours": self.reddit_simulated_hours,
            "twitter_running": self.twitter_running,
            "reddit_running": self.reddit_running,
            "twitter_completed": self.twitter_completed,
            "reddit_completed": self.reddit_completed,
            "twitter_actions_count": self.twitter_actions_count,
            "reddit_actions_count": self.reddit_actions_count,
            "total_actions_count": self.twitter_actions_count + self.reddit_actions_count,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "process_pid": self.process_pid,
        }
    
    def to_detail_dict(self) -> Dict[str, Any]:
        """최근 동작을 포함한 상세 정보"""
        result = self.to_dict()
        result["recent_actions"] = [a.to_dict() for a in self.recent_actions]
        result["rounds_count"] = len(self.rounds)
        return result


class SimulationRunner:
    """
    시뮬레이션 실행기
    
    담당:
    1. 백그라운드 프로세스에서 OASIS 시뮬레이션 실행
    2. 실행 로그를 파싱하여 각 Agent의 동작 기록
    3. 실시간 상태 조회 인터페이스 제공
    4. 일시 중지/중지/재개 작업 지원
    """
    
    # 실행 상태 저장 디렉토리
    RUN_STATE_DIR = os.path.join(
        os.path.dirname(__file__),
        '../../uploads/simulations'
    )
    
    # 스크립트 디렉토리
    SCRIPTS_DIR = os.path.join(
        os.path.dirname(__file__),
        '../../scripts'
    )
    
    # 메모리의 실행 상태
    _run_states: Dict[str, SimulationRunState] = {}
    _processes: Dict[str, subprocess.Popen] = {}
    _action_queues: Dict[str, Queue] = {}
    _monitor_threads: Dict[str, threading.Thread] = {}
    _stdout_files: Dict[str, Any] = {}  # stdout 파일 핸들 저장
    _stderr_files: Dict[str, Any] = {}  # stderr 파일 핸들 저장
    _env_reaper_threads: Dict[str, threading.Thread] = {}
    
    # 그래프 메모리 업데이트 구성
    _graph_memory_enabled: Dict[str, bool] = {}  # simulation_id -> 활성화 여부
    
    @classmethod
    def get_run_state(cls, simulation_id: str) -> Optional[SimulationRunState]:
        """실행 상태 가져오기"""
        if simulation_id in cls._run_states:
            return cls._run_states[simulation_id]
        
        # 파일에서 로드 시도
        state = cls._load_run_state(simulation_id)
        if state:
            cls._run_states[simulation_id] = state
        return state
    
    @classmethod
    def _load_run_state(cls, simulation_id: str) -> Optional[SimulationRunState]:
        """파일에서 실행 상태 로드"""
        state_file = os.path.join(cls.RUN_STATE_DIR, simulation_id, "run_state.json")
        if not os.path.exists(state_file):
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state = SimulationRunState(
                simulation_id=simulation_id,
                runner_status=RunnerStatus(data.get("runner_status", "idle")),
                current_round=data.get("current_round", 0),
                total_rounds=data.get("total_rounds", 0),
                simulated_hours=data.get("simulated_hours", 0),
                total_simulation_hours=data.get("total_simulation_hours", 0),
                # 각 플랫폼 독립 라운드 및 시간
                twitter_current_round=data.get("twitter_current_round", 0),
                reddit_current_round=data.get("reddit_current_round", 0),
                twitter_simulated_hours=data.get("twitter_simulated_hours", 0),
                reddit_simulated_hours=data.get("reddit_simulated_hours", 0),
                twitter_running=data.get("twitter_running", False),
                reddit_running=data.get("reddit_running", False),
                twitter_completed=data.get("twitter_completed", False),
                reddit_completed=data.get("reddit_completed", False),
                twitter_actions_count=data.get("twitter_actions_count", 0),
                reddit_actions_count=data.get("reddit_actions_count", 0),
                started_at=data.get("started_at"),
                updated_at=data.get("updated_at", datetime.now().isoformat()),
                completed_at=data.get("completed_at"),
                error=data.get("error"),
                process_pid=data.get("process_pid"),
            )
            
            # 최근 동작 로드
            actions_data = data.get("recent_actions", [])
            for a in actions_data:
                state.recent_actions.append(AgentAction(
                    round_num=a.get("round_num", 0),
                    timestamp=a.get("timestamp", ""),
                    platform=a.get("platform", ""),
                    agent_id=a.get("agent_id", 0),
                    agent_name=a.get("agent_name", ""),
                    action_type=a.get("action_type", ""),
                    action_args=a.get("action_args", {}),
                    result=a.get("result"),
                    success=a.get("success", True),
                ))
            
            return state
        except Exception as e:
            logger.error(f"실행 상태 로드 실패: {str(e)}")
            return None
    
    @classmethod
    def _save_run_state(cls, state: SimulationRunState):
        """실행 상태를 파일에 저장"""
        sim_dir = os.path.join(cls.RUN_STATE_DIR, state.simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        state_file = os.path.join(sim_dir, "run_state.json")
        
        data = state.to_detail_dict()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        cls._run_states[state.simulation_id] = state

    @classmethod
    def _sync_simulation_status(cls, simulation_id: str, runner_status: RunnerStatus, error: Optional[str] = None):
        """실행 상태를 SimulationManager의 state.json에 동기화합니다."""
        try:
            from .simulation_manager import SimulationManager, SimulationStatus

            manager = SimulationManager()
            state = manager.get_simulation(simulation_id)
            if not state:
                return

            status_map = {
                RunnerStatus.RUNNING: SimulationStatus.RUNNING,
                RunnerStatus.STOPPING: SimulationStatus.RUNNING,
                RunnerStatus.STOPPED: SimulationStatus.STOPPED,
                RunnerStatus.COMPLETED: SimulationStatus.COMPLETED,
                RunnerStatus.FAILED: SimulationStatus.FAILED,
            }

            mapped_status = status_map.get(runner_status)
            if mapped_status:
                state.status = mapped_status

            if error is not None:
                state.error = error

            manager._save_simulation_state(state)
        except Exception as sync_error:
            logger.warning(f"시뮬레이션 상태 동기화 실패: {simulation_id}, error={sync_error}")

    @staticmethod
    def _is_pid_alive(pid: Optional[int]) -> bool:
        """PID가 아직 살아 있는지 확인합니다."""
        if not pid:
            return False
        try:
            os.kill(int(pid), 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    @classmethod
    def _iter_live_process_states(cls) -> Dict[str, SimulationRunState]:
        """현재 살아 있는 시뮬레이션 프로세스의 상태를 반환합니다."""
        live_states: Dict[str, SimulationRunState] = {}

        for simulation_id, process in list(cls._processes.items()):
            if process.poll() is not None:
                cls._processes.pop(simulation_id, None)
                continue
            state = cls.get_run_state(simulation_id)
            if state and cls._is_pid_alive(process.pid):
                live_states[simulation_id] = state

        if not os.path.exists(cls.RUN_STATE_DIR):
            return live_states

        for simulation_id in os.listdir(cls.RUN_STATE_DIR):
            if simulation_id in live_states:
                continue
            state = cls.get_run_state(simulation_id)
            if not state or not cls._is_pid_alive(state.process_pid):
                continue
            live_states[simulation_id] = state

        return live_states

    @classmethod
    def count_process_slots(cls) -> Dict[str, int]:
        """현재 살아 있는 시뮬레이션 프로세스 점유 현황을 반환합니다."""
        live_states = cls._iter_live_process_states().values()
        running_statuses = {
            RunnerStatus.STARTING,
            RunnerStatus.RUNNING,
            RunnerStatus.PAUSED,
            RunnerStatus.STOPPING,
        }

        running = 0
        warm = 0

        for state in live_states:
            if state.runner_status in running_statuses:
                running += 1
            else:
                warm += 1

        return {
            "running": running,
            "warm": warm,
            "alive": running + warm,
        }

    @classmethod
    def _ensure_env_reaper(cls, simulation_id: str):
        """완료된 시뮬레이션 환경을 TTL 이후 자동 종료하도록 스케줄링합니다."""
        ttl_seconds = Config.SIMULATION_ENV_TTL_SECONDS
        if ttl_seconds <= 0:
            return

        existing = cls._env_reaper_threads.get(simulation_id)
        if existing and existing.is_alive():
            return

        thread = threading.Thread(
            target=cls._auto_close_completed_env,
            args=(simulation_id,),
            daemon=True,
        )
        cls._env_reaper_threads[simulation_id] = thread
        thread.start()

    @classmethod
    def _auto_close_completed_env(cls, simulation_id: str):
        """TTL이 지난 완료 시뮬레이션 환경을 자동 종료합니다."""
        ttl_seconds = Config.SIMULATION_ENV_TTL_SECONDS
        deadline = time.time() + ttl_seconds

        try:
            while time.time() < deadline:
                state = cls.get_run_state(simulation_id)
                process = cls._processes.get(simulation_id)
                if not state or state.runner_status != RunnerStatus.COMPLETED:
                    return
                if not process or process.poll() is not None:
                    return
                time.sleep(min(10, max(deadline - time.time(), 1)))

            state = cls.get_run_state(simulation_id)
            process = cls._processes.get(simulation_id)
            if not state or state.runner_status != RunnerStatus.COMPLETED:
                return
            if not process or process.poll() is not None:
                return

            logger.info(
                "완료된 시뮬레이션 환경 TTL 만료, 자동 종료합니다: simulation_id=%s, ttl=%s",
                simulation_id,
                ttl_seconds,
            )

            try:
                cls.close_simulation_env(simulation_id, timeout=15.0)
            except Exception as close_error:
                logger.warning(f"환경 종료 명령 실패, 프로세스 종료로 대체합니다: {simulation_id}, error={close_error}")

            time.sleep(5)
            process = cls._processes.get(simulation_id)
            if process and process.poll() is None:
                cls._terminate_process(process, simulation_id, timeout=10)
        except Exception as reaper_error:
            logger.warning(f"시뮬레이션 환경 자동 종료 실패: {simulation_id}, error={reaper_error}")
        finally:
            cls._env_reaper_threads.pop(simulation_id, None)
    
    @classmethod
    def start_simulation(
        cls,
        simulation_id: str,
        platform: str = "parallel",  # twitter / reddit / parallel
        max_rounds: int = None,  # 최대 시뮬레이션 라운드 수 (선택 사항, 너무 긴 시뮬레이션을 잘라내는 데 사용)
        enable_graph_memory_update: bool = False,  # 활동을 Zep 그래프에 업데이트할지 여부
        graph_id: str = None  # Zep 그래프 ID (그래프 업데이트 활성화 시 필수)
    ) -> SimulationRunState:
        """
        시뮬레이션 시작
        
        Args:
            simulation_id: 시뮬레이션 ID
            platform: 실행 플랫폼 (twitter/reddit/parallel)
            max_rounds: 최대 시뮬레이션 라운드 수 (선택 사항, 너무 긴 시뮬레이션을 잘라내는 데 사용)
            enable_graph_memory_update: Agent 활동을 Zep 그래프에 동적으로 업데이트할지 여부
            graph_id: Zep 그래프 ID (그래프 업데이트 활성화 시 필수)
            
        Returns:
            SimulationRunState
        """
        # 이미 실행 중인지 확인
        existing = cls.get_run_state(simulation_id)
        if existing and existing.runner_status in [RunnerStatus.RUNNING, RunnerStatus.STARTING]:
            raise ValueError(f"시뮬레이션이 이미 실행 중: {simulation_id}")
        
        # 시뮬레이션 구성 로드
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            raise ValueError(f"시뮬레이션 구성이 존재하지 않습니다. 먼저 /prepare API를 호출하십시오.")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 실행 상태 초기화
        time_config = config.get("time_config", {})
        total_hours = time_config.get("total_simulation_hours", 72)
        minutes_per_round = time_config.get("minutes_per_round", 30)
        total_rounds = int(total_hours * 60 / minutes_per_round)
        
        # 최대 라운드 수가 지정된 경우, 잘라냅니다.
        if max_rounds is not None and max_rounds > 0:
            original_rounds = total_rounds
            total_rounds = min(total_rounds, max_rounds)
            if total_rounds < original_rounds:
                logger.info(f"라운드 수가 잘라내졌습니다: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
        
        state = SimulationRunState(
            simulation_id=simulation_id,
            runner_status=RunnerStatus.STARTING,
            total_rounds=total_rounds,
            total_simulation_hours=total_hours,
            started_at=datetime.now().isoformat(),
        )
        
        cls._save_run_state(state)
        
        # 그래프 메모리 업데이트가 활성화된 경우, 업데이트 생성
        if enable_graph_memory_update:
            if not graph_id:
                raise ValueError("그래프 메모리 업데이트를 활성화할 때 graph_id를 제공해야 합니다.")
            
            try:
                ZepGraphMemoryManager.create_updater(simulation_id, graph_id)
                cls._graph_memory_enabled[simulation_id] = True
                logger.info(f"그래프 메모리 업데이트 활성화됨: simulation_id={simulation_id}, graph_id={graph_id}")
            except Exception as e:
                logger.error(f"그래프 메모리 업데이트 생성 실패: {e}")
                cls._graph_memory_enabled[simulation_id] = False
        else:
            cls._graph_memory_enabled[simulation_id] = False
        
        # 어떤 스크립트를 실행할지 결정합니다 (스크립트는 backend/scripts/ 디렉토리에 있습니다).
        if platform == "twitter":
            script_name = "run_twitter_simulation.py"
            state.twitter_running = True
        elif platform == "reddit":
            script_name = "run_reddit_simulation.py"
            state.reddit_running = True
        else:
            script_name = "run_parallel_simulation.py"
            state.twitter_running = True
            state.reddit_running = True
        
        script_path = os.path.join(cls.SCRIPTS_DIR, script_name)
        
        if not os.path.exists(script_path):
            raise ValueError(f"스크립트가 존재하지 않습니다: {script_path}")
        
        # 액션 큐 생성
        action_queue = Queue()
        cls._action_queues[simulation_id] = action_queue
        
        # 시뮬레이션 프로세스 시작
        try:
            # 전체 경로를 사용하여 실행 명령 구축
            # 새로운 로그 구조:
            #   twitter/actions.jsonl - Twitter 액션 로그
            #   reddit/actions.jsonl  - Reddit 액션 로그
            #   simulation.log        - 메인 프로세스 로그
            
            cmd = [
                sys.executable,  # Python 인터프리터
                script_path,
                "--config", config_path,  # 전체 구성 파일 경로 사용
            ]
            
            # 최대 라운드 수가 지정된 경우, 명령줄 인수에 추가
            if max_rounds is not None and max_rounds > 0:
                cmd.extend(["--max-rounds", str(max_rounds)])
            
            # stdout/stderr 파이프 버퍼가 가득 차 프로세스가 블록되는 것을 방지하기 위해 메인 로그 파일 생성
            main_log_path = os.path.join(sim_dir, "simulation.log")
            main_log_file = open(main_log_path, 'w', encoding='utf-8')
            
            # 자식 프로세스 환경 변수를 설정하여 Windows에서 UTF-8 인코딩을 사용하도록 합니다.
            # 이는 OASIS와 같은 타사 라이브러리가 파일을 읽을 때 인코딩을 지정하지 않아 발생하는 문제를 해결할 수 있습니다.
            env = os.environ.copy()
            env['PYTHONUTF8'] = '1'  # Python 3.7+ 지원, 모든 open()이 기본적으로 UTF-8을 사용하도록 합니다.
            env['PYTHONIOENCODING'] = 'utf-8'  # stdout/stderr가 UTF-8을 사용하도록 보장
            
            # 작업 디렉토리를 시뮬레이션 디렉토리로 설정합니다 (데이터베이스 등의 파일이 여기에 생성됩니다).
            # start_new_session=True를 사용하여 새 프로세스 그룹을 생성하여 os.killpg를 통해 모든 자식 프로세스를 종료할 수 있도록 합니다.
            process = subprocess.Popen(
                cmd,
                cwd=sim_dir,
                stdout=main_log_file,
                stderr=subprocess.STDOUT,  # stderr도 동일한 파일에 기록
                text=True,
                encoding='utf-8',  # 명시적으로 인코딩 지정
                bufsize=1,
                env=env,  # UTF-8 설정이 포함된 환경 변수 전달
                start_new_session=True,  # 새 프로세스 그룹 생성, 서버 종료 시 모든 관련 프로세스가 종료되도록 보장
            )
            
            # 나중에 닫을 수 있도록 파일 핸들 저장
            cls._stdout_files[simulation_id] = main_log_file
            cls._stderr_files[simulation_id] = None  # 더 이상 별도의 stderr 필요 없음
            
            state.process_pid = process.pid
            state.runner_status = RunnerStatus.RUNNING
            cls._processes[simulation_id] = process
            cls._save_run_state(state)
            
            # 모니터링 스레드 시작
            monitor_thread = threading.Thread(
                target=cls._monitor_simulation,
                args=(simulation_id,),
                daemon=True
            )
            monitor_thread.start()
            cls._monitor_threads[simulation_id] = monitor_thread
            
            logger.info(f"시뮬레이션 시작 성공: {simulation_id}, pid={process.pid}, platform={platform}")
            
        except Exception as e:
            state.runner_status = RunnerStatus.FAILED
            state.error = str(e)
            cls._save_run_state(state)
            raise
        
        return state
    
    @classmethod
    def _monitor_simulation(cls, simulation_id: str):
        """시뮬레이션 프로세스 모니터링, 액션 로그 파싱"""
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        # 새로운 로그 구조: 플랫폼별 액션 로그
        twitter_actions_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        reddit_actions_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        
        process = cls._processes.get(simulation_id)
        state = cls.get_run_state(simulation_id)
        
        if not process or not state:
            return
        
        twitter_position = 0
        reddit_position = 0
        
        try:
            while process.poll() is None:  # 프로세스가 아직 실행 중
                # Twitter 액션 로그 읽기
                if os.path.exists(twitter_actions_log):
                    twitter_position = cls._read_action_log(
                        twitter_actions_log, twitter_position, state, "twitter"
                    )
                
                # Reddit 액션 로그 읽기
                if os.path.exists(reddit_actions_log):
                    reddit_position = cls._read_action_log(
                        reddit_actions_log, reddit_position, state, "reddit"
                    )
                
                # 상태 업데이트
                cls._save_run_state(state)
                time.sleep(2)
            
            # 프로세스 종료 후, 로그를 마지막으로 한 번 읽습니다.
            if os.path.exists(twitter_actions_log):
                cls._read_action_log(twitter_actions_log, twitter_position, state, "twitter")
            if os.path.exists(reddit_actions_log):
                cls._read_action_log(reddit_actions_log, reddit_position, state, "reddit")
            
            # 프로세스 종료
            exit_code = process.returncode
            
            if exit_code == 0:
                if state.runner_status in [RunnerStatus.STOPPING, RunnerStatus.STOPPED]:
                    state.runner_status = RunnerStatus.STOPPED
                else:
                    state.runner_status = RunnerStatus.COMPLETED
                state.completed_at = datetime.now().isoformat()
                logger.info(f"시뮬레이션 완료: {simulation_id}")
            else:
                if state.runner_status in [RunnerStatus.STOPPING, RunnerStatus.STOPPED]:
                    state.runner_status = RunnerStatus.STOPPED
                    state.completed_at = datetime.now().isoformat()
                    state.error = None
                    logger.info(f"시뮬레이션 중지 완료: {simulation_id}")
                else:
                    state.runner_status = RunnerStatus.FAILED
                    # 메인 로그 파일에서 오류 정보 읽기
                    main_log_path = os.path.join(sim_dir, "simulation.log")
                    error_info = ""
                    try:
                        if os.path.exists(main_log_path):
                            with open(main_log_path, 'r', encoding='utf-8') as f:
                                error_info = f.read()[-2000:]  # 마지막 2000자 가져오기
                    except Exception:
                        pass
                    state.error = f"프로세스 종료 코드: {exit_code}, 오류: {error_info}"
                    logger.error(f"시뮬레이션 실패: {simulation_id}, error={state.error}")
            
            state.twitter_running = False
            state.reddit_running = False
            cls._save_run_state(state)
            cls._sync_simulation_status(simulation_id, state.runner_status, state.error)
            
        except Exception as e:
            logger.error(f"모니터링 스레드 예외: {simulation_id}, error={str(e)}")
            if state.runner_status in [RunnerStatus.STOPPING, RunnerStatus.STOPPED]:
                state.runner_status = RunnerStatus.STOPPED
                state.error = None
            else:
                state.runner_status = RunnerStatus.FAILED
                state.error = str(e)
            cls._save_run_state(state)
            cls._sync_simulation_status(simulation_id, state.runner_status, state.error)
        
        finally:
            # 그래프 메모리 업데이트 중지
            if cls._graph_memory_enabled.get(simulation_id, False):
                try:
                    ZepGraphMemoryManager.stop_updater(simulation_id)
                    logger.info(f"그래프 메모리 업데이트 중지됨: simulation_id={simulation_id}")
                except Exception as e:
                    logger.error(f"그래프 메모리 업데이트 중지 실패: {e}")
                cls._graph_memory_enabled.pop(simulation_id, None)
            
            # 프로세스 리소스 정리
            cls._processes.pop(simulation_id, None)
            cls._action_queues.pop(simulation_id, None)
            
            # 로그 파일 핸들 닫기
            if simulation_id in cls._stdout_files:
                try:
                    cls._stdout_files[simulation_id].close()
                except Exception:
                    pass
                cls._stdout_files.pop(simulation_id, None)
            if simulation_id in cls._stderr_files and cls._stderr_files[simulation_id]:
                try:
                    cls._stderr_files[simulation_id].close()
                except Exception:
                    pass
                cls._stderr_files.pop(simulation_id, None)
    
    @classmethod
    def _read_action_log(
        cls, 
        log_path: str, 
        position: int, 
        state: SimulationRunState,
        platform: str
    ) -> int:
        """
        액션 로그 파일 읽기
        
        Args:
            log_path: 로그 파일 경로
            position: 마지막으로 읽은 위치
            state: 실행 상태 객체
            platform: 플랫폼 이름 (twitter/reddit)
            
        Returns:
            새로운 읽기 위치
        """
        # 그래프 메모리 업데이트가 활성화되었는지 확인
        graph_memory_enabled = cls._graph_memory_enabled.get(state.simulation_id, False)
        graph_updater = None
        if graph_memory_enabled:
            graph_updater = ZepGraphMemoryManager.get_updater(state.simulation_id)
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                f.seek(position)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            action_data = json.loads(line)
                            
                            # 이벤트 유형 항목 처리
                            if "event_type" in action_data:
                                event_type = action_data.get("event_type")
                                
                                # simulation_end 이벤트 감지, 플랫폼 완료로 표시
                                if event_type == "simulation_end":
                                    if platform == "twitter":
                                        state.twitter_completed = True
                                        state.twitter_running = False
                                        logger.info(f"Twitter 시뮬레이션 완료됨: {state.simulation_id}, total_rounds={action_data.get('total_rounds')}, total_actions={action_data.get('total_actions')}")
                                    elif platform == "reddit":
                                        state.reddit_completed = True
                                        state.reddit_running = False
                                        logger.info(f"Reddit 시뮬레이션 완료됨: {state.simulation_id}, total_rounds={action_data.get('total_rounds')}, total_actions={action_data.get('total_actions')}")
                                    
                                    # 모든 활성화된 플랫폼이 완료되었는지 확인
                                    # 하나의 플랫폼만 실행된 경우, 해당 플랫폼만 확인
                                    # 두 개의 플랫폼이 실행된 경우, 둘 다 완료되어야 합니다.
                                    all_completed = cls._check_all_platforms_completed(state)
                                    if all_completed:
                                        state.runner_status = RunnerStatus.COMPLETED
                                        state.completed_at = datetime.now().isoformat()
                                        logger.info(f"모든 플랫폼 시뮬레이션 완료됨: {state.simulation_id}")
                                        cls._ensure_env_reaper(state.simulation_id)
                                
                                # 라운드 정보 업데이트 (round_end 이벤트에서)
                                elif event_type == "round_end":
                                    round_num = action_data.get("round", 0)
                                    simulated_hours = action_data.get("simulated_hours", 0)
                                    
                                    # 각 플랫폼의 독립적인 라운드 및 시간 업데이트
                                    if platform == "twitter":
                                        if round_num > state.twitter_current_round:
                                            state.twitter_current_round = round_num
                                        state.twitter_simulated_hours = simulated_hours
                                    elif platform == "reddit":
                                        if round_num > state.reddit_current_round:
                                            state.reddit_current_round = round_num
                                        state.reddit_simulated_hours = simulated_hours
                                    
                                    # 전체 라운드는 두 플랫폼의 최댓값을 취합니다.
                                    if round_num > state.current_round:
                                        state.current_round = round_num
                                    # 전체 시간은 두 플랫폼의 최댓값을 취합니다.
                                    state.simulated_hours = max(state.twitter_simulated_hours, state.reddit_simulated_hours)
                                
                                continue
                            
                            action = AgentAction(
                                round_num=action_data.get("round", 0),
                                timestamp=action_data.get("timestamp", datetime.now().isoformat()),
                                platform=platform,
                                agent_id=action_data.get("agent_id", 0),
                                agent_name=action_data.get("agent_name", ""),
                                action_type=action_data.get("action_type", ""),
                                action_args=action_data.get("action_args", {}),
                                result=action_data.get("result"),
                                success=action_data.get("success", True),
                            )
                            state.add_action(action)
                            
                            # 라운드 업데이트
                            if action.round_num and action.round_num > state.current_round:
                                state.current_round = action.round_num
                            
                            # 그래프 메모리 업데이트가 활성화된 경우, 활동을 Zep으로 전송
                            if graph_updater:
                                graph_updater.add_activity_from_dict(action_data, platform)
                            
                        except json.JSONDecodeError:
                            pass
                return f.tell()
        except Exception as e:
            logger.warning(f"액션 로그 읽기 실패: {log_path}, error={e}")
            return position
    
    @classmethod
    def _check_all_platforms_completed(cls, state: SimulationRunState) -> bool:
        """
        모든 활성화된 플랫폼이 시뮬레이션을 완료했는지 확인
        
        해당 actions.jsonl 파일의 존재 여부를 통해 플랫폼 활성화 여부를 판단합니다.
        
        Returns:
            모든 활성화된 플랫폼이 완료되었으면 True
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, state.simulation_id)
        twitter_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        reddit_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        
        # 어떤 플랫폼이 활성화되었는지 확인 (파일 존재 여부로 판단)
        twitter_enabled = os.path.exists(twitter_log)
        reddit_enabled = os.path.exists(reddit_log)
        
        # 플랫폼이 활성화되었지만 완료되지 않은 경우, False 반환
        if twitter_enabled and not state.twitter_completed:
            return False
        if reddit_enabled and not state.reddit_completed:
            return False
        
        # 적어도 하나의 플랫폼이 활성화되고 완료됨
        return twitter_enabled or reddit_enabled
    
    @classmethod
    def _terminate_process(cls, process: subprocess.Popen, simulation_id: str, timeout: int = 10):
        """
        플랫폼 간 프로세스 및 자식 프로세스 종료
        
        Args:
            process: 종료할 프로세스
            simulation_id: 시뮬레이션 ID (로그용)
            timeout: 프로세스 종료 대기 시간 초과 (초)
        """
        if IS_WINDOWS:
            # Windows: taskkill 명령을 사용하여 프로세스 트리 종료
            # /F = 강제 종료, /T = 프로세스 트리 종료 (자식 프로세스 포함)
            logger.info(f"프로세스 트리 종료 (Windows): simulation={simulation_id}, pid={process.pid}")
            try:
                # 먼저 정상 종료 시도
                subprocess.run(
                    ['taskkill', '/PID', str(process.pid), '/T'],
                    capture_output=True,
                    timeout=5
                )
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # 강제 종료
                    logger.warning(f"프로세스가 응답하지 않아 강제 종료: {simulation_id}")
                    subprocess.run(
                        ['taskkill', '/F', '/PID', str(process.pid), '/T'],
                        capture_output=True,
                        timeout=5
                    )
                    process.wait(timeout=5)
            except Exception as e:
                logger.warning(f"taskkill 실패, terminate 시도: {e}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        else:
            # Unix: 프로세스 그룹을 사용하여 종료
            # start_new_session=True를 사용했으므로, 프로세스 그룹 ID는 메인 프로세스 PID와 같습니다.
            pgid = os.getpgid(process.pid)
            logger.info(f"프로세스 그룹 종료 (Unix): simulation={simulation_id}, pgid={pgid}")
            
            # 먼저 전체 프로세스 그룹에 SIGTERM 전송
            os.killpg(pgid, signal.SIGTERM)
            
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # 시간 초과 후에도 종료되지 않으면 SIGKILL 강제 전송
                logger.warning(f"프로세스 그룹이 SIGTERM에 응답하지 않아 강제 종료: {simulation_id}")
                os.killpg(pgid, signal.SIGKILL)
                process.wait(timeout=5)
    
    @classmethod
    def stop_simulation(cls, simulation_id: str) -> SimulationRunState:
        """시뮬레이션 중지"""
        state = cls.get_run_state(simulation_id)
        if not state:
            raise ValueError(f"시뮬레이션이 존재하지 않습니다: {simulation_id}")
        
        if state.runner_status not in [RunnerStatus.RUNNING, RunnerStatus.PAUSED]:
            raise ValueError(f"시뮬레이션이 실행 중이 아닙니다: {simulation_id}, status={state.runner_status}")
        
        state.runner_status = RunnerStatus.STOPPING
        cls._save_run_state(state)
        
        # 프로세스 종료
        process = cls._processes.get(simulation_id)
        if process and process.poll() is None:
            try:
                cls._terminate_process(process, simulation_id)
            except ProcessLookupError:
                # 프로세스가 이미 존재하지 않음
                pass
            except Exception as e:
                logger.error(f"프로세스 그룹 종료 실패: {simulation_id}, error={e}")
                # 프로세스 직접 종료로 폴백
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    process.kill()
        
        state.runner_status = RunnerStatus.STOPPED
        state.twitter_running = False
        state.reddit_running = False
        state.completed_at = datetime.now().isoformat()
        cls._save_run_state(state)
        
        # 그래프 메모리 업데이트 중지
        if cls._graph_memory_enabled.get(simulation_id, False):
            try:
                ZepGraphMemoryManager.stop_updater(simulation_id)
                logger.info(f"그래프 메모리 업데이트 중지됨: simulation_id={simulation_id}")
            except Exception as e:
                logger.error(f"그래프 메모리 업데이트 중지 실패: {e}")
            cls._graph_memory_enabled.pop(simulation_id, None)
        
        logger.info(f"시뮬레이션 중지됨: {simulation_id}")
        return state
    
    @classmethod
    def _read_actions_from_file(
        cls,
        file_path: str,
        default_platform: Optional[str] = None,
        platform_filter: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        단일 액션 파일에서 액션 읽기
        
        Args:
            file_path: 액션 로그 파일 경로
            default_platform: 기본 플랫폼 (액션 기록에 platform 필드가 없을 때 사용)
            platform_filter: 필터링할 플랫폼
            agent_id: 필터링할 Agent ID
            round_num: 필터링할 라운드
        """
        if not os.path.exists(file_path):
            return []
        
        actions = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # 비-액션 기록 건너뛰기 (예: simulation_start, round_start, round_end 등 이벤트)
                    if "event_type" in data:
                        continue
                    
                    # agent_id가 없는 기록 건너뛰기 (Agent 액션 아님)
                    if "agent_id" not in data:
                        continue
                    
                    # 플랫폼 가져오기: 기록의 platform을 우선 사용하고, 없으면 기본 플랫폼 사용
                    record_platform = data.get("platform") or default_platform or ""
                    
                    # 필터링
                    if platform_filter and record_platform != platform_filter:
                        continue
                    if agent_id is not None and data.get("agent_id") != agent_id:
                        continue
                    if round_num is not None and data.get("round") != round_num:
                        continue
                    
                    actions.append(AgentAction(
                        round_num=data.get("round", 0),
                        timestamp=data.get("timestamp", ""),
                        platform=record_platform,
                        agent_id=data.get("agent_id", 0),
                        agent_name=data.get("agent_name", ""),
                        action_type=data.get("action_type", ""),
                        action_args=data.get("action_args", {}),
                        result=data.get("result"),
                        success=data.get("success", True),
                    ))
                    
                except json.JSONDecodeError:
                    continue
        
        return actions
    
    @classmethod
    def get_all_actions(
        cls,
        simulation_id: str,
        platform: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        모든 플랫폼의 전체 액션 기록 가져오기 (페이지네이션 제한 없음)
        
        Args:
            simulation_id: 시뮬레이션 ID
            platform: 필터링할 플랫폼 (twitter/reddit)
            agent_id: 필터링할 Agent
            round_num: 필터링할 라운드
            
        Returns:
            전체 액션 목록 (타임스탬프 기준으로 정렬, 최신이 앞에)
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        actions = []
        
        # Twitter 액션 파일 읽기 (파일 경로에 따라 platform을 twitter로 자동 설정)
        twitter_actions_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        if not platform or platform == "twitter":
            actions.extend(cls._read_actions_from_file(
                twitter_actions_log,
                default_platform="twitter",  # platform 필드 자동 채우기
                platform_filter=platform,
                agent_id=agent_id, 
                round_num=round_num
            ))
        
        # Reddit 액션 파일 읽기 (파일 경로에 따라 platform을 reddit으로 자동 설정)
        reddit_actions_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        if not platform or platform == "reddit":
            actions.extend(cls._read_actions_from_file(
                reddit_actions_log,
                default_platform="reddit",  # platform 필드 자동 채우기
                platform_filter=platform,
                agent_id=agent_id,
                round_num=round_num
            ))
        
        # 플랫폼별 파일이 없는 경우, 이전 단일 파일 형식 읽기 시도
        if not actions:
            actions_log = os.path.join(sim_dir, "actions.jsonl")
            actions = cls._read_actions_from_file(
                actions_log,
                default_platform=None,  # 이전 형식 파일에는 platform 필드가 있어야 합니다.
                platform_filter=platform,
                agent_id=agent_id,
                round_num=round_num
            )
        
        # 타임스탬프 기준으로 정렬 (최신이 앞에)
        actions.sort(key=lambda x: x.timestamp, reverse=True)
        
        return actions
    
    @classmethod
    def get_actions(
        cls,
        simulation_id: str,
        limit: int = 100,
        offset: int = 0,
        platform: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        액션 기록 가져오기 (페이지네이션 포함)
        
        Args:
            simulation_id: 시뮬레이션 ID
            limit: 반환할 개수 제한
            offset: 오프셋
            platform: 필터링할 플랫폼
            agent_id: 필터링할 Agent
            round_num: 필터링할 라운드
            
        Returns:
            액션 목록
        """
        actions = cls.get_all_actions(
            simulation_id=simulation_id,
            platform=platform,
            agent_id=agent_id,
            round_num=round_num
        )
        
        # 페이지네이션
        return actions[offset:offset + limit]
    
    @classmethod
    def get_timeline(
        cls,
        simulation_id: str,
        start_round: int = 0,
        end_round: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        시뮬레이션 타임라인 가져오기 (라운드별 요약)
        
        Args:
            simulation_id: 시뮬레이션 ID
            start_round: 시작 라운드
            end_round: 종료 라운드
            
        Returns:
            각 라운드의 요약 정보
        """
        actions = cls.get_actions(simulation_id, limit=10000)
        
        # 라운드별 그룹화
        rounds: Dict[int, Dict[str, Any]] = {}
        
        for action in actions:
            round_num = action.round_num
            
            if round_num < start_round:
                continue
            if end_round is not None and round_num > end_round:
                continue
            
            if round_num not in rounds:
                rounds[round_num] = {
                    "round_num": round_num,
                    "twitter_actions": 0,
                    "reddit_actions": 0,
                    "active_agents": set(),
                    "action_types": {},
                    "first_action_time": action.timestamp,
                    "last_action_time": action.timestamp,
                }
            
            r = rounds[round_num]
            
            if action.platform == "twitter":
                r["twitter_actions"] += 1
            else:
                r["reddit_actions"] += 1
            
            r["active_agents"].add(action.agent_id)
            r["action_types"][action.action_type] = r["action_types"].get(action.action_type, 0) + 1
            r["last_action_time"] = action.timestamp
        
        # 목록으로 변환
        result = []
        for round_num in sorted(rounds.keys()):
            r = rounds[round_num]
            result.append({
                "round_num": round_num,
                "twitter_actions": r["twitter_actions"],
                "reddit_actions": r["reddit_actions"],
                "total_actions": r["twitter_actions"] + r["reddit_actions"],
                "active_agents_count": len(r["active_agents"]),
                "active_agents": list(r["active_agents"]),
                "action_types": r["action_types"],
                "first_action_time": r["first_action_time"],
                "last_action_time": r["last_action_time"],
            })
        
        return result
    
    @classmethod
    def get_agent_stats(cls, simulation_id: str) -> List[Dict[str, Any]]:
        """
        각 Agent의 통계 정보 가져오기
        
        Returns:
            Agent 통계 목록
        """
        actions = cls.get_actions(simulation_id, limit=10000)
        
        agent_stats: Dict[int, Dict[str, Any]] = {}
        
        for action in actions:
            agent_id = action.agent_id
            
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "agent_id": agent_id,
                    "agent_name": action.agent_name,
                    "total_actions": 0,
                    "twitter_actions": 0,
                    "reddit_actions": 0,
                    "action_types": {},
                    "first_action_time": action.timestamp,
                    "last_action_time": action.timestamp,
                }
            
            stats = agent_stats[agent_id]
            stats["total_actions"] += 1
            
            if action.platform == "twitter":
                stats["twitter_actions"] += 1
            else:
                stats["reddit_actions"] += 1
            
            stats["action_types"][action.action_type] = stats["action_types"].get(action.action_type, 0) + 1
            stats["last_action_time"] = action.timestamp
        
        # 총 액션 수 기준으로 정렬
        result = sorted(agent_stats.values(), key=lambda x: x["total_actions"], reverse=True)
        
        return result
    
    @classmethod
    def cleanup_simulation_logs(cls, simulation_id: str) -> Dict[str, Any]:
        """
        시뮬레이션 실행 로그 정리 (시뮬레이션을 강제로 다시 시작하는 데 사용)
        
        다음 파일을 삭제합니다:
        - run_state.json
        - twitter/actions.jsonl
        - reddit/actions.jsonl
        - simulation.log
        - stdout.log / stderr.log
        - twitter_simulation.db (시뮬레이션 데이터베이스)
        - reddit_simulation.db (시뮬레이션 데이터베이스)
        - env_status.json (환경 상태)
        
        참고: 구성 파일 (simulation_config.json) 및 프로필 파일은 삭제되지 않습니다.
        
        Args:
            simulation_id: 시뮬레이션 ID
            
        Returns:
            정리 결과 정보
        """
        import shutil
        
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        if not os.path.exists(sim_dir):
            return {"success": True, "message": "시뮬레이션 디렉토리가 존재하지 않아 정리할 필요 없음"}
        
        cleaned_files = []
        errors = []
        
        # 삭제할 파일 목록 (데이터베이스 파일 포함)
        files_to_delete = [
            "run_state.json",
            "simulation.log",
            "stdout.log",
            "stderr.log",
            "twitter_simulation.db",  # Twitter 플랫폼 데이터베이스
            "reddit_simulation.db",   # Reddit 플랫폼 데이터베이스
            "env_status.json",        # 환경 상태 파일
        ]
        
        # 삭제할 디렉토리 목록 (액션 로그 포함)
        dirs_to_clean = ["twitter", "reddit"]
        
        # 파일 삭제
        for filename in files_to_delete:
            file_path = os.path.join(sim_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    cleaned_files.append(filename)
                except Exception as e:
                    errors.append(f"{filename} 삭제 실패: {str(e)}")
        
        # 플랫폼 디렉토리의 액션 로그 정리
        for dir_name in dirs_to_clean:
            dir_path = os.path.join(sim_dir, dir_name)
            if os.path.exists(dir_path):
                actions_file = os.path.join(dir_path, "actions.jsonl")
                if os.path.exists(actions_file):
                    try:
                        os.remove(actions_file)
                        cleaned_files.append(f"{dir_name}/actions.jsonl")
                    except Exception as e:
                        errors.append(f"{dir_name}/actions.jsonl 삭제 실패: {str(e)}")
        
        # 메모리의 실행 상태 정리
        if simulation_id in cls._run_states:
            del cls._run_states[simulation_id]
        
        logger.info(f"시뮬레이션 로그 정리 완료: {simulation_id}, 삭제된 파일: {cleaned_files}")
        
        return {
            "success": len(errors) == 0,
            "cleaned_files": cleaned_files,
            "errors": errors if errors else None
        }
    
    # 중복 정리 방지 플래그
    _cleanup_done = False
    
    @classmethod
    def cleanup_all_simulations(cls):
        """
        실행 중인 모든 시뮬레이션 프로세스 정리
        
        서버 종료 시 호출되어 모든 자식 프로세스가 종료되도록 합니다.
        """
        # 중복 정리 방지
        if cls._cleanup_done:
            return
        cls._cleanup_done = True
        
        # 정리할 내용이 있는지 확인합니다 (빈 프로세스의 프로세스가 불필요한 로그를 출력하는 것을 방지).
        has_processes = bool(cls._processes)
        has_updaters = bool(cls._graph_memory_enabled)
        
        if not has_processes and not has_updaters:
            return  # 정리할 내용이 없으므로, 조용히 반환
        
        logger.info("모든 시뮬레이션 프로세스를 정리 중...")
        
        # 먼저 모든 그래프 메모리 업데이트를 중지합니다 (stop_all 내부에서 로그 출력).
        try:
            ZepGraphMemoryManager.stop_all()
        except Exception as e:
            logger.error(f"그래프 메모리 업데이트 중지 실패: {e}")
        cls._graph_memory_enabled.clear()
        
        # 반복 중 수정 방지를 위해 딕셔너리 복사
        processes = list(cls._processes.items())
        
        for simulation_id, process in processes:
            try:
                if process.poll() is None:  # 프로세스가 아직 실행 중
                    logger.info(f"시뮬레이션 프로세스 종료: {simulation_id}, pid={process.pid}")
                    
                    try:
                        # 플랫폼 간 프로세스 종료 방법 사용
                        cls._terminate_process(process, simulation_id, timeout=5)
                    except (ProcessLookupError, OSError):
                        # 프로세스가 이미 존재하지 않을 수 있으므로, 직접 종료 시도
                        try:
                            process.terminate()
                            process.wait(timeout=3)
                        except Exception:
                            process.kill()
                    
                    # run_state.json 업데이트
                    state = cls.get_run_state(simulation_id)
                    if state:
                        state.runner_status = RunnerStatus.STOPPED
                        state.twitter_running = False
                        state.reddit_running = False
                        state.completed_at = datetime.now().isoformat()
                        state.error = "서버 종료, 시뮬레이션 중지됨"
                        cls._save_run_state(state)
                    
                    # 동시에 state.json을 업데이트하여 상태를 stopped로 설정
                    try:
                        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
                        state_file = os.path.join(sim_dir, "state.json")
                        logger.info(f"state.json 업데이트 시도: {state_file}")
                        if os.path.exists(state_file):
                            with open(state_file, 'r', encoding='utf-8') as f:
                                state_data = json.load(f)
                            state_data['status'] = 'stopped'
                            state_data['updated_at'] = datetime.now().isoformat()
                            with open(state_file, 'w', encoding='utf-8') as f:
                                json.dump(state_data, f, indent=2, ensure_ascii=False)
                            logger.info(f"state.json 상태가 stopped로 업데이트됨: {simulation_id}")
                        else:
                            logger.warning(f"state.json이 존재하지 않습니다: {state_file}")
                    except Exception as state_err:
                        logger.warning(f"state.json 업데이트 실패: {simulation_id}, error={state_err}")
                        
            except Exception as e:
                logger.error(f"프로세스 정리 실패: {simulation_id}, error={e}")
        
        # 파일 핸들 정리
        for simulation_id, file_handle in list(cls._stdout_files.items()):
            try:
                if file_handle:
                    file_handle.close()
            except Exception:
                pass
        cls._stdout_files.clear()
        
        for simulation_id, file_handle in list(cls._stderr_files.items()):
            try:
                if file_handle:
                    file_handle.close()
            except Exception:
                pass
        cls._stderr_files.clear()
        
        # 메모리의 상태 정리
        cls._processes.clear()
        cls._action_queues.clear()
        
        logger.info("시뮬레이션 프로세스 정리 완료")
    
    @classmethod
    def register_cleanup(cls):
        """
        정리 함수 등록
        
        Flask 애플리케이션 시작 시 호출되어 서버 종료 시 모든 시뮬레이션 프로세스를 정리하도록 합니다.
        """
        global _cleanup_registered
        
        if _cleanup_registered:
            return
        
        # Flask 디버그 모드에서는 reloader 자식 프로세스에서만 정리 등록 (실제로 애플리케이션을 실행하는 프로세스)
        # WERKZEUG_RUN_MAIN=true는 reloader 자식 프로세스임을 나타냅니다.
        # 디버그 모드가 아닌 경우, 이 환경 변수가 없으므로 등록해야 합니다.
        is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
        is_debug_mode = os.environ.get('FLASK_DEBUG') == '1' or os.environ.get('WERKZEUG_RUN_MAIN') is not None
        
        # 디버그 모드에서는 reloader 자식 프로세스에서만 등록하고, 비-디버그 모드에서는 항상 등록합니다.
        if is_debug_mode and not is_reloader_process:
            _cleanup_registered = True  # 등록됨으로 표시하여 자식 프로세스가 다시 시도하는 것을 방지
            return
        
        # 기존 신호 핸들러 저장
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)
        # SIGHUP은 Unix 시스템 (macOS/Linux)에만 존재하며, Windows에는 없습니다.
        original_sighup = None
        has_sighup = hasattr(signal, 'SIGHUP')
        if has_sighup:
            original_sighup = signal.getsignal(signal.SIGHUP)
        
        def cleanup_handler(signum=None, frame=None):
            """신호 핸들러: 먼저 시뮬레이션 프로세스를 정리하고, 그 다음 원래 핸들러 호출"""
            # 정리할 프로세스가 있을 때만 로그 출력
            if cls._processes or cls._graph_memory_enabled:
                logger.info(f"신호 {signum} 수신, 정리 시작...")
            cls.cleanup_all_simulations()
            
            # 기존 신호 핸들러를 호출하여 Flask가 정상적으로 종료되도록 합니다.
            if signum == signal.SIGINT and callable(original_sigint):
                original_sigint(signum, frame)
            elif signum == signal.SIGTERM and callable(original_sigterm):
                original_sigterm(signum, frame)
            elif has_sighup and signum == signal.SIGHUP:
                # SIGHUP: 터미널 종료 시 전송
                if callable(original_sighup):
                    original_sighup(signum, frame)
                else:
                    # 기본 동작: 정상 종료
                    sys.exit(0)
            else:
                # 원래 핸들러가 호출 불가능한 경우 (예: SIG_DFL), 기본 동작 사용
                raise KeyboardInterrupt
        
        # atexit 핸들러 등록 (대체용)
        atexit.register(cls.cleanup_all_simulations)
        
        # 신호 핸들러 등록 (메인 스레드에서만)
        try:
            # SIGTERM: kill 명령의 기본 신호
            signal.signal(signal.SIGTERM, cleanup_handler)
            # SIGINT: Ctrl+C
            signal.signal(signal.SIGINT, cleanup_handler)
            # SIGHUP: 터미널 종료 (Unix 시스템만 해당)
            if has_sighup:
                signal.signal(signal.SIGHUP, cleanup_handler)
        except ValueError:
            # 메인 스레드가 아니므로, atexit만 사용 가능
            logger.warning("신호 핸들러 등록 불가 (메인 스레드가 아님), atexit만 사용")
        
        _cleanup_registered = True
    
    @classmethod
    def get_running_simulations(cls) -> List[str]:
        """
        실행 중인 모든 시뮬레이션 ID 목록 가져오기
        """
        running = []
        for sim_id, process in cls._processes.items():
            if process.poll() is None:
                running.append(sim_id)
        return running
    
    # ============== 인터뷰 기능 ==============
    
    @classmethod
    def check_env_alive(cls, simulation_id: str) -> bool:
        """
        시뮬레이션 환경이 활성 상태인지 확인합니다 (Interview 명령을 받을 수 있는지).

        Args:
            simulation_id: 시뮬레이션 ID

        Returns:
            환경이 활성 상태이면 True, 환경이 종료되었으면 False
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            return False

        ipc_client = SimulationIPCClient(sim_dir)
        return ipc_client.check_env_alive()

    @classmethod
    def get_env_status_detail(cls, simulation_id: str) -> Dict[str, Any]:
        """
        시뮬레이션 환경의 상세 상태 정보를 가져옵니다.

        Args:
            simulation_id: 시뮬레이션 ID

        Returns:
            상태 상세 딕셔너리, status, twitter_available, reddit_available, timestamp 포함
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        status_file = os.path.join(sim_dir, "env_status.json")
        
        default_status = {
            "status": "stopped",
            "twitter_available": False,
            "reddit_available": False,
            "timestamp": None
        }
        
        if not os.path.exists(status_file):
            return default_status
        
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            return {
                "status": status.get("status", "stopped"),
                "twitter_available": status.get("twitter_available", False),
                "reddit_available": status.get("reddit_available", False),
                "timestamp": status.get("timestamp")
            }
        except (json.JSONDecodeError, OSError):
            return default_status

    @classmethod
    def interview_agent(
        cls,
        simulation_id: str,
        agent_id: int,
        prompt: str,
        platform: str = None,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """
        단일 Agent 인터뷰

        Args:
            simulation_id: 시뮬레이션 ID
            agent_id: Agent ID
            prompt: 인터뷰 질문
            platform: 지정 플랫폼 (선택 사항)
                - "twitter": Twitter 플랫폼만 인터뷰
                - "reddit": Reddit 플랫폼만 인터뷰
                - None: 양 플랫폼 시뮬레이션 시 두 플랫폼 모두 인터뷰하고 통합 결과 반환
            timeout: 시간 초과 (초)

        Returns:
            인터뷰 결과 딕셔너리

        Raises:
            ValueError: 시뮬레이션이 존재하지 않거나 환경이 실행 중이 아님
            TimeoutError: 응답 대기 시간 초과
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"시뮬레이션이 존재하지 않습니다: {simulation_id}")

        ipc_client = SimulationIPCClient(sim_dir)

        if not ipc_client.check_env_alive():
            raise ValueError(f"시뮬레이션 환경이 실행 중이 아니거나 종료되어 Interview를 실행할 수 없습니다: {simulation_id}")

        logger.info(f"Interview 명령 전송: simulation_id={simulation_id}, agent_id={agent_id}, platform={platform}")

        response = ipc_client.send_interview(
            agent_id=agent_id,
            prompt=prompt,
            platform=platform,
            timeout=timeout
        )

        if response.status.value == "completed":
            return {
                "success": True,
                "agent_id": agent_id,
                "prompt": prompt,
                "result": response.result,
                "timestamp": response.timestamp
            }
        else:
            return {
                "success": False,
                "agent_id": agent_id,
                "prompt": prompt,
                "error": response.error,
                "timestamp": response.timestamp
            }
    
    @classmethod
    def interview_agents_batch(
        cls,
        simulation_id: str,
        interviews: List[Dict[str, Any]],
        platform: str = None,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        여러 Agent 일괄 인터뷰

        Args:
            simulation_id: 시뮬레이션 ID
            interviews: 인터뷰 목록, 각 요소는 {"agent_id": int, "prompt": str, "platform": str(선택 사항)} 포함
            platform: 기본 플랫폼 (선택 사항, 각 인터뷰 항목의 platform으로 덮어쓰여짐)
                - "twitter": 기본적으로 Twitter 플랫폼만 인터뷰
                - "reddit": 기본적으로 Reddit 플랫폼만 인터뷰
                - None: 양 플랫폼 시뮬레이션 시 각 Agent가 두 플랫폼 모두 인터뷰
            timeout: 시간 초과 (초)

        Returns:
            일괄 인터뷰 결과 딕셔너리

        Raises:
            ValueError: 시뮬레이션이 존재하지 않거나 환경이 실행 중이 아님
            TimeoutError: 응답 대기 시간 초과
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"시뮬레이션이 존재하지 않습니다: {simulation_id}")

        ipc_client = SimulationIPCClient(sim_dir)

        if not ipc_client.check_env_alive():
            raise ValueError(f"시뮬레이션 환경이 실행 중이 아니거나 종료되어 Interview를 실행할 수 없습니다: {simulation_id}")

        logger.info(f"일괄 Interview 명령 전송: simulation_id={simulation_id}, count={len(interviews)}, platform={platform}")

        response = ipc_client.send_batch_interview(
            interviews=interviews,
            platform=platform,
            timeout=timeout
        )

        if response.status.value == "completed":
            return {
                "success": True,
                "interviews_count": len(interviews),
                "result": response.result,
                "timestamp": response.timestamp
            }
        else:
            return {
                "success": False,
                "interviews_count": len(interviews),
                "error": response.error,
                "timestamp": response.timestamp
            }
    
    @classmethod
    def interview_all_agents(
        cls,
        simulation_id: str,
        prompt: str,
        platform: str = None,
        timeout: float = 180.0
    ) -> Dict[str, Any]:
        """
        모든 Agent 인터뷰 (전역 인터뷰)

        동일한 질문으로 시뮬레이션의 모든 Agent를 인터뷰합니다.

        Args:
            simulation_id: 시뮬레이션 ID
            prompt: 인터뷰 질문 (모든 Agent가 동일한 질문 사용)
            platform: 지정 플랫폼 (선택 사항)
                - "twitter": Twitter 플랫폼만 인터뷰
                - "reddit": Reddit 플랫폼만 인터뷰
                - None: 양 플랫폼 시뮬레이션 시 각 Agent가 두 플랫폼 모두 인터뷰
            timeout: 시간 초과 (초)

        Returns:
            전역 인터뷰 결과 딕셔너리
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"시뮬레이션이 존재하지 않습니다: {simulation_id}")

        # 구성 파일에서 모든 Agent 정보 가져오기
        config_path = os.path.join(sim_dir, "simulation_config.json")
        if not os.path.exists(config_path):
            raise ValueError(f"시뮬레이션 구성이 존재하지 않습니다: {simulation_id}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        agent_configs = config.get("agent_configs", [])
        if not agent_configs:
            raise ValueError(f"시뮬레이션 구성에 Agent가 없습니다: {simulation_id}")

        # 일괄 인터뷰 목록 구축
        interviews = []
        for agent_config in agent_configs:
            agent_id = agent_config.get("agent_id")
            if agent_id is not None:
                interviews.append({
                    "agent_id": agent_id,
                    "prompt": prompt
                })

        logger.info(f"전역 Interview 명령 전송: simulation_id={simulation_id}, agent_count={len(interviews)}, platform={platform}")

        return cls.interview_agents_batch(
            simulation_id=simulation_id,
            interviews=interviews,
            platform=platform,
            timeout=timeout
        )
    
    @classmethod
    def close_simulation_env(
        cls,
        simulation_id: str,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        시뮬레이션 환경 종료 (시뮬레이션 프로세스 중지가 아님)
        
        시뮬레이션에 환경 종료 명령을 보내 명령 대기 모드에서 정상적으로 종료되도록 합니다.
        
        Args:
            simulation_id: 시뮬레이션 ID
            timeout: 시간 초과 (초)
            
        Returns:
            작업 결과 딕셔너리
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"시뮬레이션이 존재하지 않습니다: {simulation_id}")
        
        ipc_client = SimulationIPCClient(sim_dir)
        
        if not ipc_client.check_env_alive():
            return {
                "success": True,
                "message": "환경이 이미 종료됨"
            }
        
        logger.info(f"환경 종료 명령 전송: simulation_id={simulation_id}")
        
        try:
            response = ipc_client.send_close_env(timeout=timeout)
            
            return {
                "success": response.status.value == "completed",
                "message": "환경 종료 명령 전송됨",
                "result": response.result,
                "timestamp": response.timestamp
            }
        except TimeoutError:
            # 시간 초과는 환경이 종료 중이기 때문일 수 있습니다.
            return {
                "success": True,
                "message": "환경 종료 명령 전송됨 (응답 대기 시간 초과, 환경이 종료 중일 수 있음)"
            }
    
    @classmethod
    def _get_interview_history_from_db(
        cls,
        db_path: str,
        platform_name: str,
        agent_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """단일 데이터베이스에서 인터뷰 기록 가져오기"""
        import sqlite3
        
        if not os.path.exists(db_path):
            return []
        
        results = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if agent_id is not None:
                cursor.execute("""
                    SELECT user_id, info, created_at
                    FROM trace
                    WHERE action = 'interview' AND user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (agent_id, limit))
            else:
                cursor.execute("""
                    SELECT user_id, info, created_at
                    FROM trace
                    WHERE action = 'interview'
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
            
            for user_id, info_json, created_at in cursor.fetchall():
                try:
                    info = json.loads(info_json) if info_json else {}
                except json.JSONDecodeError:
                    info = {"raw": info_json}
                
                results.append({
                    "agent_id": user_id,
                    "response": info.get("response", info),
                    "prompt": info.get("prompt", ""),
                    "timestamp": created_at,
                    "platform": platform_name
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"인터뷰 기록 읽기 실패 ({platform_name}): {e}")
        
        return results

    @classmethod
    def get_interview_history(
        cls,
        simulation_id: str,
        platform: str = None,
        agent_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        인터뷰 기록 가져오기 (데이터베이스에서 읽기)
        
        Args:
            simulation_id: 시뮬레이션 ID
            platform: 플랫폼 유형 (reddit/twitter/None)
                - "reddit": Reddit 플랫폼 기록만 가져오기
                - "twitter": Twitter 플랫폼 기록만 가져오기
                - None: 두 플랫폼의 모든 기록 가져오기
            agent_id: 지정 Agent ID (선택 사항, 해당 Agent의 기록만 가져오기)
            limit: 각 플랫폼에서 반환할 개수 제한
            
        Returns:
            인터뷰 기록 목록
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        results = []
        
        # 조회할 플랫폼 결정
        if platform in ("reddit", "twitter"):
            platforms = [platform]
        else:
            # platform을 지정하지 않으면 두 플랫폼을 조회
            platforms = ["twitter", "reddit"]
        
        for p in platforms:
            db_path = os.path.join(sim_dir, f"{p}_simulation.db")
            platform_results = cls._get_interview_history_from_db(
                db_path=db_path,
                platform_name=p,
                agent_id=agent_id,
                limit=limit
            )
            results.extend(platform_results)
        
        # 시간 내림차순으로 정렬
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # 여러 플랫폼을 조회한 경우, 총 개수 제한
        if len(platforms) > 1 and len(results) > limit:
            results = results[:limit]
        
        return results
