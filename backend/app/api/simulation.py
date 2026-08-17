"""
시뮬레이션 관련 API 라우트
Step2: Zep 엔티티 읽기 및 필터링, OASIS 시뮬레이션 준비 및 실행 (전체 자동화)
"""

import os
from flask import request, jsonify, send_file

from . import simulation_bp
from ..config import Config
from ..services.zep_entity_reader import ZepEntityReader
from ..services.oasis_profile_generator import OasisProfileGenerator
from ..services.capacity_guard import CapacityGuard, CapacityExceededError
from ..services.simulation_manager import SimulationManager, SimulationStatus
from ..services.simulation_runner import SimulationRunner, RunnerStatus
from ..utils.api_response import error_traceback_payload
from ..utils.logger import get_logger
from ..models.task import TaskManager, TaskStatus
from ..models.project import ProjectManager

logger = get_logger('tiresias.api.simulation')


def _capacity_error_response(error: CapacityExceededError):
    response = jsonify(error.to_payload())
    response.status_code = 429
    response.headers['Retry-After'] = str(Config.CAPACITY_RETRY_AFTER_SECONDS)
    return response


# 인터뷰 프롬프트 접두사 최적화
# 이 접두사를 추가하면 에이전트가 도구를 호출하는 것을 방지하고 텍스트로 직접 응답할 수 있습니다.
INTERVIEW_PROMPT_PREFIX = "당신의 페르소나, 모든 과거 기억과 행동을 결합하여 어떤 도구도 호출하지 않고 텍스트로 직접 저에게 답변해주세요:"


def optimize_interview_prompt(prompt: str) -> str:
    """
    인터뷰 질문 최적화, 에이전트가 도구를 호출하는 것을 방지하기 위해 접두사 추가
    
    Args:
        prompt: 원래 질문
        
    Returns:
        최적화된 질문
    """
    if not prompt:
        return prompt
    # 중복 접두사 추가 방지
    if prompt.startswith(INTERVIEW_PROMPT_PREFIX):
        return prompt
    return f"{INTERVIEW_PROMPT_PREFIX}{prompt}"


# ============== 엔티티 읽기 API ==============

@simulation_bp.route('/entities/<graph_id>', methods=['GET'])
def get_graph_entities(graph_id: str):
    """
    그래프의 모든 엔티티 가져오기 (필터링됨)
    
    사전 정의된 엔티티 유형과 일치하는 노드만 반환합니다 (레이블이 Entity만 있는 노드가 아님).
    
    쿼리 매개변수:
        entity_types: 쉼표로 구분된 엔티티 유형 목록 (선택 사항, 추가 필터링에 사용)
        enrich: 관련 엣지 정보를 가져올지 여부 (기본값 true)
    """
    try:
        if Config.validate_graph_backend():
            return jsonify({
                "success": False,
                "error": "; ".join(Config.validate_graph_backend())
            }), 500
        
        entity_types_str = request.args.get('entity_types', '')
        entity_types = [t.strip() for t in entity_types_str.split(',') if t.strip()] if entity_types_str else None
        enrich = request.args.get('enrich', 'true').lower() == 'true'
        
        logger.info(f"그래프 엔티티 가져오기: graph_id={graph_id}, entity_types={entity_types}, enrich={enrich}")
        
        reader = ZepEntityReader()
        result = reader.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=entity_types,
            enrich_with_edges=enrich
        )
        
        return jsonify({
            "success": True,
            "data": result.to_dict()
        })
        
    except Exception as e:
        logger.error(f"그래프 엔티티 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/entities/<graph_id>/<entity_uuid>', methods=['GET'])
def get_entity_detail(graph_id: str, entity_uuid: str):
    """단일 엔티티의 상세 정보 가져오기"""
    try:
        if Config.validate_graph_backend():
            return jsonify({
                "success": False,
                "error": "; ".join(Config.validate_graph_backend())
            }), 500
        
        reader = ZepEntityReader()
        entity = reader.get_entity_with_context(graph_id, entity_uuid)
        
        if not entity:
            return jsonify({
                "success": False,
                "error": f"엔티티가 존재하지 않음: {entity_uuid}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": entity.to_dict()
        })
        
    except Exception as e:
        logger.error(f"엔티티 상세 정보 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/entities/<graph_id>/by-type/<entity_type>', methods=['GET'])
def get_entities_by_type(graph_id: str, entity_type: str):
    """지정된 유형의 모든 엔티티 가져오기"""
    try:
        if Config.validate_graph_backend():
            return jsonify({
                "success": False,
                "error": "; ".join(Config.validate_graph_backend())
            }), 500
        
        enrich = request.args.get('enrich', 'true').lower() == 'true'
        
        reader = ZepEntityReader()
        entities = reader.get_entities_by_type(
            graph_id=graph_id,
            entity_type=entity_type,
            enrich_with_edges=enrich
        )
        
        return jsonify({
            "success": True,
            "data": {
                "entity_type": entity_type,
                "count": len(entities),
                "entities": [e.to_dict() for e in entities]
            }
        })
        
    except Exception as e:
        logger.error(f"엔티티 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


# ============== 시뮬레이션 관리 API ==============

@simulation_bp.route('/create', methods=['POST'])
def create_simulation():
    """
    새 시뮬레이션 생성
    
    참고: max_rounds 등의 매개변수는 LLM에 의해 지능적으로 생성되므로 수동으로 설정할 필요가 없습니다.
    
    요청 (JSON):
        {
            "project_id": "proj_xxxx",      // 필수
            "graph_id": "tiresias_xxxx",    // 선택 사항, 제공되지 않으면 프로젝트에서 가져옴
            "enable_twitter": true,          // 선택 사항, 기본값 true
            "enable_reddit": true            // 선택 사항, 기본값 true
        }
    
    반환:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "project_id": "proj_xxxx",
                "graph_id": "tiresias_xxxx",
                "status": "created",
                "enable_twitter": true,
                "enable_reddit": true,
                "created_at": "2025-12-01T10:00:00"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({
                "success": False,
                "error": "project_id를 제공해주세요"
            }), 400
        
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"프로젝트가 존재하지 않음: {project_id}"
            }), 404
        
        graph_id = data.get('graph_id') or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "프로젝트가 아직 그래프를 구축하지 않았습니다. 먼저 /api/graph/build를 호출해주세요"
            }), 400
        
        manager = SimulationManager()
        state = manager.create_simulation(
            project_id=project_id,
            graph_id=graph_id,
            enable_twitter=data.get('enable_twitter', True),
            enable_reddit=data.get('enable_reddit', True),
        )
        
        return jsonify({
            "success": True,
            "data": state.to_dict()
        })
        
    except Exception as e:
        logger.error(f"시뮬레이션 생성 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


def _check_simulation_prepared(simulation_id: str) -> tuple:
    """
    시뮬레이션 준비 완료 여부 확인
    
    확인 조건:
    1. state.json이 존재하고 status가 "ready"임
    2. 필수 파일 존재: reddit_profiles.json, twitter_profiles.csv, simulation_config.json
    
    참고: 실행 스크립트(run_*.py)는 backend/scripts/ 디렉토리에 유지되며 시뮬레이션 디렉토리로 더 이상 복사되지 않습니다.
    
    Args:
        simulation_id: 시뮬레이션 ID
        
    Returns:
        (is_prepared: bool, info: dict)
    """
    import os
    from ..config import Config
    
    simulation_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)
    
    # 디렉토리 존재 여부 확인
    if not os.path.exists(simulation_dir):
        return False, {"reason": "시뮬레이션 디렉토리가 존재하지 않음"}
    
    state_file = os.path.join(simulation_dir, "state.json")
    try:
        import json
        with open(state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)

        required_files = ["state.json", "simulation_config.json"]
        if state_data.get("enable_reddit", True):
            required_files.append("reddit_profiles.json")
        if state_data.get("enable_twitter", True):
            required_files.append("twitter_profiles.csv")

        existing_files = []
        missing_files = []
        for filename in required_files:
            file_path = os.path.join(simulation_dir, filename)
            if os.path.exists(file_path):
                existing_files.append(filename)
            else:
                missing_files.append(filename)

        if missing_files:
            return False, {
                "reason": "필수 파일 누락",
                "missing_files": missing_files,
                "existing_files": existing_files
            }
        
        status = state_data.get("status", "")
        config_generated = state_data.get("config_generated", False)
        
        # 상세 로그
        logger.debug(f"시뮬레이션 준비 상태 감지: {simulation_id}, status={status}, config_generated={config_generated}")
        
        # config_generated=True이고 파일이 존재하면 준비 완료로 간주합니다.
        # 다음 상태는 준비 작업이 완료되었음을 나타냅니다.
        # - ready: 준비 완료, 실행 가능
        # - preparing: config_generated=True이면 완료된 것임
        # - running: 실행 중, 준비가 이미 완료되었음을 의미
        # - completed: 실행 완료, 준비가 이미 완료되었음을 의미
        # - stopped: 중지됨, 준비가 이미 완료되었음을 의미
        # - failed: 실행 실패 (하지만 준비는 완료됨)
        prepared_statuses = ["ready", "preparing", "running", "completed", "stopped", "paused", "failed"]
        if status in prepared_statuses and config_generated:
            profiles_count = 0
            reddit_profiles_file = os.path.join(simulation_dir, "reddit_profiles.json")
            twitter_profiles_file = os.path.join(simulation_dir, "twitter_profiles.csv")

            if os.path.exists(reddit_profiles_file):
                with open(reddit_profiles_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
                    if isinstance(profiles_data, list):
                        profiles_count = max(profiles_count, len(profiles_data))

            if os.path.exists(twitter_profiles_file):
                import csv
                with open(twitter_profiles_file, 'r', encoding='utf-8', newline='') as f:
                    profiles_count = max(profiles_count, sum(1 for _ in csv.DictReader(f)))
            
            # 상태가 preparing이지만 파일이 완료되면 상태를 자동으로 ready로 업데이트합니다.
            if status == "preparing":
                try:
                    state_data["status"] = "ready"
                    from datetime import datetime
                    state_data["updated_at"] = datetime.now().isoformat()
                    with open(state_file, 'w', encoding='utf-8') as f:
                        json.dump(state_data, f, ensure_ascii=False, indent=2)
                    logger.info(f"시뮬레이션 상태 자동 업데이트: {simulation_id} preparing -> ready")
                    status = "ready"
                except Exception as e:
                    logger.warning(f"상태 자동 업데이트 실패: {e}")
            
            logger.info(f"시뮬레이션 {simulation_id} 감지 결과: 준비 완료 (status={status}, config_generated={config_generated})")
            return True, {
                "status": status,
                "entities_count": state_data.get("entities_count", 0),
                "profiles_count": profiles_count,
                "entity_types": state_data.get("entity_types", []),
                "config_generated": config_generated,
                "created_at": state_data.get("created_at"),
                "updated_at": state_data.get("updated_at"),
                "existing_files": existing_files
            }
        else:
            logger.warning(f"시뮬레이션 {simulation_id} 감지 결과: 준비 미완료 (status={status}, config_generated={config_generated})")
            return False, {
                "reason": f"상태가 준비 완료 목록에 없거나 config_generated가 false임: status={status}, config_generated={config_generated}",
                "status": status,
                "config_generated": config_generated
            }
            
    except Exception as e:
        return False, {"reason": f"상태 파일 읽기 실패: {str(e)}"}


def _count_generated_profiles(simulation_dir: str, enable_reddit: bool = True) -> int:
    """실시간 생성 중인 프로필 파일 개수를 최대한 안전하게 읽습니다."""
    import csv
    import json

    profile_files = []
    if enable_reddit:
        profile_files.append(("json", os.path.join(simulation_dir, "reddit_profiles.json")))
    profile_files.append(("csv", os.path.join(simulation_dir, "twitter_profiles.csv")))

    for file_type, file_path in profile_files:
        if not os.path.exists(file_path):
            continue
        try:
            if file_type == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                if isinstance(profiles, list):
                    return len(profiles)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return sum(1 for _ in csv.DictReader(f))
        except Exception:
            continue
    return 0


def _infer_prepare_status_from_state(simulation_id: str, state) -> dict:
    """TaskManager 작업이 사라진 경우 state/file 기반으로 준비 진행률을 추론합니다."""
    simulation_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)
    total_entities = max(int(getattr(state, "entities_count", 0) or 0), 0)
    generated_profiles = _count_generated_profiles(
        simulation_dir,
        enable_reddit=getattr(state, "enable_reddit", True)
    )
    config_exists = os.path.exists(os.path.join(simulation_dir, "simulation_config.json"))
    config_generated = bool(getattr(state, "config_generated", False) or config_exists)

    if state.status == SimulationStatus.FAILED:
        return {
            "simulation_id": simulation_id,
            "status": "failed",
            "progress": 0,
            "message": state.error or "준비 실패",
            "already_prepared": False
        }

    if state.status != SimulationStatus.PREPARING:
        return {
            "simulation_id": simulation_id,
            "status": "processing",
            "progress": 0,
            "message": "준비 중",
            "already_prepared": False
        }

    if config_generated:
        return {
            "simulation_id": simulation_id,
            "status": "processing",
            "progress": 85,
            "message": "시뮬레이션 구성 생성 마무리 중...",
            "already_prepared": False,
            "progress_detail": {
                "current_stage": "generating_config",
                "current_stage_name": "시뮬레이션 구성 생성",
                "stage_index": 3,
                "total_stages": 4,
                "stage_progress": 75,
                "current_item": 2,
                "total_items": 3,
                "item_description": "시뮬레이션 구성 생성 마무리 중..."
            }
        }

    if total_entities > 0:
        stage_progress = min(99, int((generated_profiles / total_entities) * 100))
        overall_progress = 20 + int(50 * stage_progress / 100)
        message = (
            f"에이전트 페르소나 생성 중... {generated_profiles}/{total_entities}"
            if generated_profiles > 0
            else "에이전트 페르소나 생성 시작..."
        )
        return {
            "simulation_id": simulation_id,
            "status": "processing",
            "progress": overall_progress,
            "message": message,
            "already_prepared": False,
            "progress_detail": {
                "current_stage": "generating_profiles",
                "current_stage_name": "에이전트 페르소나 생성",
                "stage_index": 2,
                "total_stages": 4,
                "stage_progress": stage_progress,
                "current_item": generated_profiles,
                "total_items": total_entities,
                "item_description": message
            }
        }

    return {
        "simulation_id": simulation_id,
        "status": "processing",
        "progress": 10,
        "message": "그래프 엔티티 읽는 중...",
        "already_prepared": False,
        "progress_detail": {
            "current_stage": "reading",
            "current_stage_name": "그래프 엔티티 읽기",
            "stage_index": 1,
            "total_stages": 4,
            "stage_progress": 50,
            "current_item": 0,
            "total_items": 0,
            "item_description": "그래프 엔티티 읽는 중..."
        }
    }


@simulation_bp.route('/prepare', methods=['POST'])
def prepare_simulation():
    """
    시뮬레이션 환경 준비 (비동기 작업, LLM이 모든 매개변수 지능적으로 생성)
    
    이것은 시간이 많이 소요되는 작업이며, 인터페이스는 즉시 task_id를 반환합니다.
    GET /api/simulation/prepare/status를 사용하여 진행 상황을 조회합니다.
    
    특징:
    - 완료된 준비 작업을 자동으로 감지하여 중복 생성을 방지합니다.
    - 이미 준비가 완료된 경우, 기존 결과를 직접 반환합니다.
    - 강제 재생성 지원 (force_regenerate=true)
    
    단계:
    1. 완료된 준비 작업이 있는지 확인
    2. Zep 그래프에서 엔티티를 읽고 필터링
    3. 각 엔티티에 대해 OASIS 에이전트 프로필 생성 (재시도 메커니즘 포함)
    4. LLM이 시뮬레이션 구성 지능적으로 생성 (재시도 메커니즘 포함)
    5. 구성 파일 및 사전 설정 스크립트 저장
    
    요청 (JSON):
        {
            "simulation_id": "sim_xxxx",                   // 필수, 시뮬레이션 ID
            "entity_types": ["Student", "PublicFigure"],  // 선택 사항, 엔티티 유형 지정
            "use_llm_for_profiles": true,                 // 선택 사항, LLM을 사용하여 페르소나를 생성할지 여부
            "parallel_profile_count": 5,                  // 선택 사항, 병렬 페르소나 생성 수, 기본값 5
            "force_regenerate": false                     // 선택 사항, 강제 재생성, 기본값 false
        }
    
    반환:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "task_id": "task_xxxx",           // 새 작업 시 반환
                "status": "preparing|ready",
                "message": "준비 작업이 시작됨|이미 완료된 준비 작업이 있음",
                "already_prepared": true|false    // 준비 완료 여부
            }
        }
    """
    import threading
    import os
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id를 제공해주세요"
            }), 400
        
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        
        if not state:
            return jsonify({
                "success": False,
                "error": f"시뮬레이션이 존재하지 않음: {simulation_id}"
            }), 404
        
        # 강제 재생성 여부 확인
        force_regenerate = data.get('force_regenerate', False)
        logger.info(f"/prepare 요청 처리 시작: simulation_id={simulation_id}, force_regenerate={force_regenerate}")
        
        # 이미 준비 완료되었는지 확인 (중복 생성 방지)
        if not force_regenerate:
            logger.debug(f"시뮬레이션 {simulation_id} 준비 완료 여부 확인...")
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
            logger.debug(f"확인 결과: is_prepared={is_prepared}, prepare_info={prepare_info}")
            if is_prepared:
                logger.info(f"시뮬레이션 {simulation_id} 준비 완료, 중복 생성 건너뛰기")
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "ready",
                        "message": "이미 완료된 준비 작업이 있으므로 중복 생성할 필요 없음",
                        "already_prepared": True,
                        "prepare_info": prepare_info
                    }
                })
            else:
                logger.info(f"시뮬레이션 {simulation_id} 준비 미완료, 준비 작업 시작 예정")

            task_manager = TaskManager()
            existing_task = task_manager.find_active_task(
                task_type="simulation_prepare",
                metadata_match={"simulation_id": simulation_id},
            )
            if existing_task:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "task_id": existing_task.task_id,
                        "status": "preparing",
                        "message": "이미 진행 중인 준비 작업이 있습니다.",
                        "already_prepared": False,
                        "already_running": True,
                    }
                })
        else:
            task_manager = TaskManager()
        
        # 프로젝트에서 필요 정보 가져오기
        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"프로젝트가 존재하지 않음: {state.project_id}"
            }), 404
        
        # 시뮬레이션 요구 사항 가져오기
        simulation_requirement = project.simulation_requirement or ""
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "프로젝트에 시뮬레이션 요구 사항 설명이 누락됨 (simulation_requirement)"
            }), 400
        
        # 문서 텍스트 가져오기
        document_text = ProjectManager.get_extracted_text(state.project_id) or ""
        
        entity_types_list = data.get('entity_types')
        use_llm_for_profiles = data.get('use_llm_for_profiles', True)
        parallel_profile_count = data.get('parallel_profile_count', 5)
        simulation_mode = data.get('simulation_mode')
        target_agent_count = data.get('target_agent_count')

        if target_agent_count is not None:
            try:
                target_agent_count = int(target_agent_count)
                if target_agent_count <= 0:
                    target_agent_count = None
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "error": "target_agent_count는 유효한 양의 정수여야 합니다"
                }), 400

        try:
            CapacityGuard.ensure_prepare_capacity()
        except CapacityExceededError as capacity_error:
            return _capacity_error_response(capacity_error)
        
        # ========== 백그라운드 작업 시작 전 엔티티 수 동기적으로 가져오기 ==========
        # 이렇게 하면 프런트엔드에서 prepare를 호출한 후 즉시 예상 에이전트 총수를 가져올 수 있습니다.
        try:
            logger.info(f"엔티티 수 동기적으로 가져오기: graph_id={state.graph_id}")
            reader = ZepEntityReader()
            # 엔티티 빠르게 읽기 (엣지 정보 필요 없음, 수량만 통계)
            filtered_preview = reader.filter_defined_entities(
                graph_id=state.graph_id,
                defined_entity_types=entity_types_list,
                enrich_with_edges=False  # 엣지 정보 가져오지 않음, 속도 향상
            )
            if target_agent_count and filtered_preview.filtered_count > target_agent_count:
                filtered_preview.entities = filtered_preview.entities[:target_agent_count]
                filtered_preview.filtered_count = len(filtered_preview.entities)
            # 엔티티 수를 상태에 저장 (프런트엔드에서 즉시 가져올 수 있도록)
            state.entities_count = filtered_preview.filtered_count
            state.entity_types = list(filtered_preview.entity_types)
            logger.info(f"예상 엔티티 수: {filtered_preview.filtered_count}, 유형: {filtered_preview.entity_types}")
        except Exception as e:
            logger.warning(f"엔티티 수 동기적으로 가져오기 실패 (백그라운드 작업에서 재시도 예정): {e}")
            # 실패해도 후속 프로세스에 영향을 미치지 않으며, 백그라운드 작업이 다시 가져올 것입니다.
        
        # 비동기 작업 생성
        task_id = task_manager.create_task(
            task_type="simulation_prepare",
            metadata={
                "simulation_id": simulation_id,
                "project_id": state.project_id
            }
        )
        
        # 시뮬레이션 상태 업데이트 (미리 가져온 엔티티 수 포함)
        state.status = SimulationStatus.PREPARING
        manager._save_simulation_state(state)
        
        # 백그라운드 작업 정의
        def run_prepare():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=0,
                    message="시뮬레이션 환경 준비 시작..."
                )
                
                # 시뮬레이션 준비 (진행률 콜백 포함)
                # 단계별 진행률 상세 정보 저장
                stage_details = {}
                
                def progress_callback(stage, progress, message, **kwargs):
                    # 총 진행률 계산
                    stage_weights = {
                        "reading": (0, 20),           # 0-20%
                        "generating_profiles": (20, 70),  # 20-70%
                        "generating_config": (70, 90),    # 70-90%
                        "copying_scripts": (90, 100)       # 90-100%
                    }
                    
                    start, end = stage_weights.get(stage, (0, 100))
                    current_progress = int(start + (end - start) * progress / 100)
                    
                    # 상세 진행률 정보 구축
                    stage_names = {
                        "reading": "그래프 엔티티 읽기",
                        "generating_profiles": "에이전트 페르소나 생성",
                        "generating_config": "시뮬레이션 구성 생성",
                        "copying_scripts": "시뮬레이션 스크립트 준비"
                    }
                    
                    stage_index = list(stage_weights.keys()).index(stage) + 1 if stage in stage_weights else 1
                    total_stages = len(stage_weights)
                    
                    # 단계 상세 정보 업데이트
                    stage_details[stage] = {
                        "stage_name": stage_names.get(stage, stage),
                        "stage_progress": progress,
                        "current": kwargs.get("current", 0),
                        "total": kwargs.get("total", 0),
                        "item_name": kwargs.get("item_name", "")
                    }
                    
                    # 상세 진행률 정보 구축
                    detail = stage_details[stage]
                    progress_detail_data = {
                        "current_stage": stage,
                        "current_stage_name": stage_names.get(stage, stage),
                        "stage_index": stage_index,
                        "total_stages": total_stages,
                        "stage_progress": progress,
                        "current_item": detail["current"],
                        "total_items": detail["total"],
                        "item_description": message
                    }
                    
                    # 간결한 메시지 구축
                    if detail["total"] > 0:
                        detailed_message = (
                            f"[{stage_index}/{total_stages}] {stage_names.get(stage, stage)}: "
                            f"{detail['current']}/{detail['total']} - {message}"
                        )
                    else:
                        detailed_message = f"[{stage_index}/{total_stages}] {stage_names.get(stage, stage)}: {message}"
                    
                    task_manager.update_task(
                        task_id,
                        progress=current_progress,
                        message=detailed_message,
                        progress_detail=progress_detail_data
                    )
                
                result_state = manager.prepare_simulation(
                    simulation_id=simulation_id,
                    simulation_requirement=simulation_requirement,
                    document_text=document_text,
                    defined_entity_types=entity_types_list,
                    use_llm_for_profiles=use_llm_for_profiles,
                    simulation_mode=simulation_mode,
                    target_agent_count=target_agent_count,
                    progress_callback=progress_callback,
                    parallel_profile_count=parallel_profile_count
                )
                
                # 작업 완료
                task_manager.complete_task(
                    task_id,
                    result=result_state.to_simple_dict()
                )
                
            except Exception as e:
                logger.error(f"시뮬레이션 준비 실패: {str(e)}")
                task_manager.fail_task(task_id, str(e))
                
                # 시뮬레이션 상태를 실패로 업데이트
                state = manager.get_simulation(simulation_id)
                if state:
                    state.status = SimulationStatus.FAILED
                    state.error = str(e)
                    manager._save_simulation_state(state)
        
        # 백그라운드 스레드 시작
        thread = threading.Thread(target=run_prepare, daemon=True)
        thread.start()
        
        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "task_id": task_id,
                "status": "preparing",
                "message": "준비 작업이 시작되었습니다. /api/simulation/prepare/status를 통해 진행 상황을 조회해주세요.",
                "already_prepared": False,
                "expected_entities_count": state.entities_count,  # 예상 에이전트 총수
                "entity_types": state.entity_types  # 엔티티 유형 목록
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"준비 작업 시작 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/prepare/status', methods=['POST'])
def get_prepare_status():
    """
    준비 작업 진행 상황 조회
    
    두 가지 조회 방식 지원:
    1. task_id를 통해 진행 중인 작업 진행 상황 조회
    2. simulation_id를 통해 완료된 준비 작업이 있는지 확인
    
    요청 (JSON):
        {
            "task_id": "task_xxxx",          // 선택 사항, prepare가 반환한 task_id
            "simulation_id": "sim_xxxx"      // 선택 사항, 시뮬레이션 ID (완료된 준비 확인용)
        }
    
    반환:
        {
            "success": true,
            "data": {
                "task_id": "task_xxxx",
                "status": "processing|completed|ready",
                "progress": 45,
                "message": "...",
                "already_prepared": true|false,  // 완료된 준비 작업이 있는지 여부
                "prepare_info": {...}            // 준비 완료 시 상세 정보
            }
        }
    """
    from ..models.task import TaskManager
    
    try:
        data = request.get_json() or {}
        
        task_id = data.get('task_id')
        simulation_id = data.get('simulation_id')
        
        # simulation_id가 제공되면, 먼저 준비 완료 여부 확인
        if simulation_id:
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
            if is_prepared:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "ready",
                        "progress": 100,
                        "message": "이미 완료된 준비 작업이 있음",
                        "already_prepared": True,
                        "prepare_info": prepare_info
                    }
                })

            manager = SimulationManager()
            state = manager.get_simulation(simulation_id)
            if state and state.status in [SimulationStatus.PREPARING, SimulationStatus.FAILED]:
                return jsonify({
                    "success": True,
                    "data": _infer_prepare_status_from_state(simulation_id, state)
                })
        
        # task_id가 없으면 오류 반환
        if not task_id:
            if simulation_id:
                # simulation_id는 있지만 준비 미완료
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "not_started",
                        "progress": 0,
                        "message": "아직 준비를 시작하지 않았습니다. /api/simulation/prepare를 호출하여 시작해주세요.",
                        "already_prepared": False
                    }
                })
            return jsonify({
                "success": False,
                "error": "task_id 또는 simulation_id를 제공해주세요"
            }), 400
        
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        
        if not task:
            # 작업이 존재하지 않지만, simulation_id가 있으면 준비 완료 여부 확인
            if simulation_id:
                is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
                if is_prepared:
                    return jsonify({
                        "success": True,
                        "data": {
                            "simulation_id": simulation_id,
                            "task_id": task_id,
                            "status": "ready",
                            "progress": 100,
                            "message": "작업 완료 (준비 작업이 이미 존재함)",
                            "already_prepared": True,
                            "prepare_info": prepare_info
                        }
                    })

                manager = SimulationManager()
                state = manager.get_simulation(simulation_id)
                if state and state.status in [SimulationStatus.PREPARING, SimulationStatus.FAILED]:
                    return jsonify({
                        "success": True,
                        "data": {
                            **_infer_prepare_status_from_state(simulation_id, state),
                            "task_id": task_id
                        }
                    })
            
            return jsonify({
                "success": False,
                "error": f"작업이 존재하지 않음: {task_id}"
            }), 404
        
        task_dict = task.to_dict()
        task_dict["already_prepared"] = False
        
        return jsonify({
            "success": True,
            "data": task_dict
        })
        
    except Exception as e:
        logger.error(f"작업 상태 조회 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>', methods=['GET'])
def get_simulation(simulation_id: str):
    """시뮬레이션 상태 가져오기"""
    try:
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        
        if not state:
            return jsonify({
                "success": False,
                "error": f"시뮬레이션이 존재하지 않음: {simulation_id}"
            }), 404
        
        result = state.to_dict()
        
        # 시뮬레이션이 준비되면 실행 지침을 첨부합니다.
        if state.status == SimulationStatus.READY:
            result["run_instructions"] = manager.get_run_instructions(simulation_id)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"시뮬레이션 상태 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/list', methods=['GET'])
def list_simulations():
    """
    모든 시뮬레이션 나열
    
    쿼리 매개변수:
        project_id: 프로젝트 ID로 필터링 (선택 사항)
    """
    try:
        project_id = request.args.get('project_id')
        
        manager = SimulationManager()
        simulations = manager.list_simulations(project_id=project_id)
        
        return jsonify({
            "success": True,
            "data": [s.to_dict() for s in simulations],
            "count": len(simulations)
        })
        
    except Exception as e:
        logger.error(f"시뮬레이션 나열 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


def _get_report_id_for_simulation(simulation_id: str) -> str:
    """
    시뮬레이션에 해당하는 최신 report_id 가져오기
    
    reports 디렉토리를 순회하며 simulation_id와 일치하는 보고서를 찾습니다.
    여러 개가 있으면 최신 것을 반환합니다 (created_at 기준으로 정렬).
    
    Args:
        simulation_id: 시뮬레이션 ID
        
    Returns:
        report_id 또는 None
    """
    import json
    from datetime import datetime
    
    # reports 디렉토리 경로: backend/uploads/reports
    # __file__은 app/api/simulation.py이므로, backend/로 두 단계 위로 이동해야 합니다.
    reports_dir = os.path.join(os.path.dirname(__file__), '../../uploads/reports')
    if not os.path.exists(reports_dir):
        return None
    
    matching_reports = []
    
    try:
        for report_folder in os.listdir(reports_dir):
            report_path = os.path.join(reports_dir, report_folder)
            if not os.path.isdir(report_path):
                continue
            
            meta_file = os.path.join(report_path, "meta.json")
            if not os.path.exists(meta_file):
                continue
            
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                
                if meta.get("simulation_id") == simulation_id:
                    matching_reports.append({
                        "report_id": meta.get("report_id"),
                        "created_at": meta.get("created_at", ""),
                        "status": meta.get("status", "")
                    })
            except Exception:
                continue
        
        if not matching_reports:
            return None
        
        # 생성 시간 역순으로 정렬하여 최신 것을 반환
        matching_reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return matching_reports[0].get("report_id")
        
    except Exception as e:
        logger.warning(f"시뮬레이션 {simulation_id} 보고서 찾기 실패: {e}")
        return None


@simulation_bp.route('/history', methods=['GET'])
def get_simulation_history():
    """
    과거 시뮬레이션 목록 가져오기 (프로젝트 상세 정보 포함)
    
    홈페이지 과거 프로젝트 표시에 사용되며, 프로젝트 이름, 설명 등 풍부한 정보를 포함하는 시뮬레이션 목록을 반환합니다.
    
    쿼리 매개변수:
        limit: 반환 수량 제한 (기본값 20)
    
    반환:
        {
            "success": true,
            "data": [
                {
                    "simulation_id": "sim_xxxx",
                    "project_id": "proj_xxxx",
                    "project_name": "우한대 여론 분석",
                    "simulation_requirement": "만약 우한대학교가 발표한다면...",
                    "status": "completed",
                    "entities_count": 68,
                    "profiles_count": 68,
                    "entity_types": ["Student", "Professor", ...],
                    "created_at": "2024-12-10",
                    "updated_at": "2024-12-10",
                    "total_rounds": 120,
                    "current_round": 120,
                    "report_id": "report_xxxx",
                    "version": "v1.0.2"
                },
                ...
            ],
            "count": 7
        }
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        
        manager = SimulationManager()
        simulations = manager.list_simulations()[:limit]
        
        # 시뮬레이션 데이터 강화, Simulation 파일에서만 읽기
        enriched_simulations = []
        for sim in simulations:
            sim_dict = sim.to_dict()
            
            # 시뮬레이션 구성 정보 가져오기 (simulation_config.json에서 simulation_requirement 읽기)
            config = manager.get_simulation_config(sim.simulation_id)
            if config:
                sim_dict["simulation_requirement"] = config.get("simulation_requirement", "")
                time_config = config.get("time_config", {})
                sim_dict["total_simulation_hours"] = time_config.get("total_simulation_hours", 0)
                # 권장 라운드 수 (예비 값)
                recommended_rounds = int(
                    time_config.get("total_simulation_hours", 0) * 60 / 
                    max(time_config.get("minutes_per_round", 60), 1)
                )
            else:
                sim_dict["simulation_requirement"] = ""
                sim_dict["total_simulation_hours"] = 0
                recommended_rounds = 0
            
            # 실행 상태 가져오기 (run_state.json에서 사용자가 설정한 실제 라운드 수 읽기)
            run_state = SimulationRunner.get_run_state(sim.simulation_id)
            if run_state:
                sim_dict["current_round"] = run_state.current_round
                sim_dict["runner_status"] = run_state.runner_status.value
                # 사용자가 설정한 total_rounds를 사용하고, 없으면 권장 라운드 수를 사용합니다.
                sim_dict["total_rounds"] = run_state.total_rounds if run_state.total_rounds > 0 else recommended_rounds
            else:
                sim_dict["current_round"] = 0
                sim_dict["runner_status"] = "idle"
                sim_dict["total_rounds"] = recommended_rounds
            
            # 연결된 프로젝트의 파일 목록 가져오기 (최대3개)
            project = ProjectManager.get_project(sim.project_id)
            if project and hasattr(project, 'files') and project.files:
                sim_dict["files"] = [
                    {"filename": f.get("filename", "알 수 없는 파일")} 
                    for f in project.files[:3]
                ]
            else:
                sim_dict["files"] = []
            
            # 연결된 report_id 가져오기 (해당 시뮬레이션의 최신 보고서 찾기)
            sim_dict["report_id"] = _get_report_id_for_simulation(sim.simulation_id)
            
            # 버전 번호 추가
            sim_dict["version"] = "v1.0.2"
            
            # 날짜 형식 지정
            try:
                created_date = sim_dict.get("created_at", "")[:10]
                sim_dict["created_date"] = created_date
            except:
                sim_dict["created_date"] = ""
            
            enriched_simulations.append(sim_dict)
        
        return jsonify({
            "success": True,
            "data": enriched_simulations,
            "count": len(enriched_simulations)
        })
        
    except Exception as e:
        logger.error(f"과거 시뮬레이션 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/<simulation_id>/profiles', methods=['GET'])
def get_simulation_profiles(simulation_id: str):
    """
    시뮬레이션 에이전트 프로필 가져오기
    
    쿼리 매개변수:
        platform: 플랫폼 유형 (reddit/twitter, 기본값 reddit)
    """
    try:
        platform = request.args.get('platform', 'reddit')
        
        manager = SimulationManager()
        profiles = manager.get_profiles(simulation_id, platform=platform)
        
        return jsonify({
            "success": True,
            "data": {
                "platform": platform,
                "count": len(profiles),
                "profiles": profiles
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"프로필 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/<simulation_id>/profiles/realtime', methods=['GET'])
def get_simulation_profiles_realtime(simulation_id: str):
    """
    시뮬레이션 에이전트 프로필 실시간 가져오기 (생성 과정 중 실시간 진행 상황 확인용)
    
    /profiles 인터페이스와의 차이점:
    - 파일을 직접 읽고 SimulationManager를 거치지 않음
    - 생성 과정 중 실시간 보기에 적합
    - 추가 메타데이터 반환 (예: 파일 수정 시간, 생성 중 여부 등)
    
    쿼리 매개변수:
        platform: 플랫폼 유형 (reddit/twitter, 기본값 reddit)
    
    반환:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "platform": "reddit",
                "count": 15,
                "total_expected": 93,  // 예상 총수 (있는 경우)
                "is_generating": true,  // 생성 중 여부
                "file_exists": true,
                "file_modified_at": "2025-12-04T18:20:00",
                "profiles": [...]
            }
        }
    """
    import json
    import csv
    from datetime import datetime
    
    try:
        platform = request.args.get('platform', 'reddit')
        
        # 시뮬레이션 디렉토리 가져오기
        sim_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)
        
        if not os.path.exists(sim_dir):
            return jsonify({
                "success": False,
                "error": f"시뮬레이션이 존재하지 않음: {simulation_id}"
            }), 404
        
        # 파일 경로 결정
        if platform == "reddit":
            profiles_file = os.path.join(sim_dir, "reddit_profiles.json")
        else:
            profiles_file = os.path.join(sim_dir, "twitter_profiles.csv")
        
        # 파일 존재 여부 확인
        file_exists = os.path.exists(profiles_file)
        profiles = []
        file_modified_at = None
        
        if file_exists:
            # 파일 수정 시간 가져오기
            file_stat = os.stat(profiles_file)
            file_modified_at = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            try:
                if platform == "reddit":
                    with open(profiles_file, 'r', encoding='utf-8') as f:
                        profiles = json.load(f)
                else:
                    with open(profiles_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        profiles = list(reader)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"프로필 파일 읽기 실패 (쓰기 중일 수 있음): {e}")
                profiles = []
        
        # 생성 중 여부 확인 (state.json을 통해 판단)
        is_generating = False
        total_expected = None
        
        state_file = os.path.join(sim_dir, "state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    status = state_data.get("status", "")
                    is_generating = status == "preparing"
                    total_expected = state_data.get("entities_count")
            except Exception:
                pass
        
        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "platform": platform,
                "count": len(profiles),
                "total_expected": total_expected,
                "is_generating": is_generating,
                "file_exists": file_exists,
                "file_modified_at": file_modified_at,
                "profiles": profiles
            }
        })
        
    except Exception as e:
        logger.error(f"실시간 프로필 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/<simulation_id>/config/realtime', methods=['GET'])
def get_simulation_config_realtime(simulation_id: str):
    """
    시뮬레이션 구성 실시간 가져오기 (생성 과정 중 실시간 진행 상황 확인용)
    
    /config 인터페이스와의 차이점:
    - 파일을 직접 읽고 SimulationManager를 거치지 않음
    - 생성 과정 중 실시간 보기에 적합
    - 추가 메타데이터 반환 (예: 파일 수정 시간, 생성 중 여부 등)
    - 구성이 아직 완전히 생성되지 않았더라도 일부 정보를 반환할 수 있음
    
    반환:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "file_exists": true,
                "file_modified_at": "2025-12-04T18:20:00",
                "is_generating": true,  // 생성 중 여부
                "generation_stage": "generating_config",  // 현재 생성 단계
                "config": {...}  // 구성 내용 (존재하는 경우)
            }
        }
    """
    import json
    from datetime import datetime
    
    try:
        # 시뮬레이션 디렉토리 가져오기
        sim_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)
        
        if not os.path.exists(sim_dir):
            return jsonify({
                "success": False,
                "error": f"시뮬레이션이 존재하지 않음: {simulation_id}"
            }), 404
        
        # 구성 파일 경로
        config_file = os.path.join(sim_dir, "simulation_config.json")
        
        # 파일 존재 여부 확인
        file_exists = os.path.exists(config_file)
        config = None
        file_modified_at = None
        
        if file_exists:
            # 파일 수정 시간 가져오기
            file_stat = os.stat(config_file)
            file_modified_at = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"구성 파일 읽기 실패 (쓰기 중일 수 있음): {e}")
                config = None
        
        # 생성 중 여부 확인 (state.json을 통해 판단)
        is_generating = False
        generation_stage = None
        config_generated = False
        
        state_file = os.path.join(sim_dir, "state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    status = state_data.get("status", "")
                    is_generating = status == "preparing"
                    config_generated = state_data.get("config_generated", False)

                    reddit_profiles_file = os.path.join(sim_dir, "reddit_profiles.json")
                    twitter_profiles_file = os.path.join(sim_dir, "twitter_profiles.csv")
                    has_profiles = os.path.exists(reddit_profiles_file) or os.path.exists(twitter_profiles_file)

                    if is_generating:
                        if has_profiles or file_exists or config_generated:
                            generation_stage = "generating_config"
                        else:
                            generation_stage = "generating_profiles"
                    elif status == "ready":
                        generation_stage = "completed"
            except Exception:
                pass
        
        # 반환 데이터 구축
        response_data = {
            "simulation_id": simulation_id,
            "file_exists": file_exists,
            "file_modified_at": file_modified_at,
            "is_generating": is_generating,
            "generation_stage": generation_stage,
            "config_generated": config_generated,
            "config": config
        }
        
        # 구성이 존재하면 일부 주요 통계 정보 추출
        if config:
            response_data["summary"] = {
                "total_agents": len(config.get("agent_configs", [])),
                "simulation_hours": config.get("time_config", {}).get("total_simulation_hours"),
                "initial_posts_count": len(config.get("event_config", {}).get("initial_posts", [])),
                "hot_topics_count": len(config.get("event_config", {}).get("hot_topics", [])),
                "has_twitter_config": "twitter_config" in config,
                "has_reddit_config": "reddit_config" in config,
                "generated_at": config.get("generated_at"),
                "llm_model": config.get("llm_model")
            }
        
        return jsonify({
            "success": True,
            "data": response_data
        })
        
    except Exception as e:
        logger.error(f"실시간 구성 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/<simulation_id>/config', methods=['GET'])
def get_simulation_config(simulation_id: str):
    """
    시뮬레이션 구성 가져오기 (LLM이 지능적으로 생성한 전체 구성)
    
    포함된 내용 반환:
        - time_config: 시간 구성 (시뮬레이션 기간, 라운드, 피크/비피크 시간)
        - agent_configs: 각 에이전트의 활동 구성 (활동성, 발언 빈도, 입장 등)
        - event_config: 이벤트 구성 (초기 게시물, 인기 토픽)
        - platform_configs: 플랫폼 구성
        - generation_reasoning: LLM의 구성 추론 설명
    """
    try:
        manager = SimulationManager()
        config = manager.get_simulation_config(simulation_id)
        
        if not config:
            return jsonify({
                "success": False,
                "error": f"시뮬레이션 구성이 존재하지 않습니다. 먼저 /prepare 인터페이스를 호출해주세요."
            }), 404
        
        return jsonify({
            "success": True,
            "data": config
        })
        
    except Exception as e:
        logger.error(f"구성 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/<simulation_id>/config/download', methods=['GET'])
def download_simulation_config(simulation_id: str):
    """시뮬레이션 구성 파일 다운로드"""
    try:
        manager = SimulationManager()
        sim_dir = manager._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            return jsonify({
                "success": False,
                "error": "구성 파일이 존재하지 않습니다. 먼저 /prepare 인터페이스를 호출해주세요."
            }), 404
        
        return send_file(
            config_path,
            as_attachment=True,
            download_name="simulation_config.json"
        )
        
    except Exception as e:
        logger.error(f"구성 다운로드 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/script/<script_name>/download', methods=['GET'])
def download_simulation_script(script_name: str):
    """
    시뮬레이션 실행 스크립트 파일 다운로드 (일반 스크립트, backend/scripts/에 위치)
    
    script_name 선택 가능한 값:
        - run_twitter_simulation.py
        - run_reddit_simulation.py
        - run_parallel_simulation.py
        - action_logger.py
    """
    try:
        # 스크립트는 backend/scripts/ 디렉토리에 있습니다.
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts'))
        
        # 스크립트 이름 확인
        allowed_scripts = [
            "run_twitter_simulation.py",
            "run_reddit_simulation.py", 
            "run_parallel_simulation.py",
            "action_logger.py"
        ]
        
        if script_name not in allowed_scripts:
            return jsonify({
                "success": False,
                "error": f"알 수 없는 스크립트입니다: {script_name}. 사용 가능한 값: {allowed_scripts}"
            }), 400
        
        script_path = os.path.join(scripts_dir, script_name)
        
        if not os.path.exists(script_path):
            return jsonify({
                "success": False,
                "error": f"스크립트 파일이 존재하지 않음: {script_name}"
            }), 404
        
        return send_file(
            script_path,
            as_attachment=True,
            download_name=script_name
        )
        
    except Exception as e:
        logger.error(f"스크립트 다운로드 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


# ============== 프로필 생성 API (독립 사용) ==============

@simulation_bp.route('/generate-profiles', methods=['POST'])
def generate_profiles():
    """
    그래프에서 OASIS 에이전트 프로필 직접 생성 (시뮬레이션 생성 안 함)
    
    요청 (JSON):
        {
            "graph_id": "tiresias_xxxx",     // 필수
            "entity_types": ["Student"],      // 선택 사항
            "use_llm": true,                  // 선택 사항
            "platform": "reddit"              // 선택 사항
        }
    """
    try:
        data = request.get_json() or {}
        
        graph_id = data.get('graph_id')
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "graph_id를 제공해주세요"
            }), 400
        
        entity_types = data.get('entity_types')
        use_llm = data.get('use_llm', True)
        platform = data.get('platform', 'reddit')
        
        reader = ZepEntityReader()
        filtered = reader.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=entity_types,
            enrich_with_edges=True
        )
        
        if filtered.filtered_count == 0:
            return jsonify({
                "success": False,
                "error": "조건에 맞는 엔티티를 찾을 수 없습니다"
            }), 400
        
        generator = OasisProfileGenerator()
        profiles = generator.generate_profiles_from_entities(
            entities=filtered.entities,
            use_llm=use_llm
        )
        
        if platform == "reddit":
            profiles_data = [p.to_reddit_format() for p in profiles]
        elif platform == "twitter":
            profiles_data = [p.to_twitter_format() for p in profiles]
        else:
            profiles_data = [p.to_dict() for p in profiles]
        
        return jsonify({
            "success": True,
            "data": {
                "platform": platform,
                "entity_types": list(filtered.entity_types),
                "count": len(profiles_data),
                "profiles": profiles_data
            }
        })
        
    except Exception as e:
        logger.error(f"프로필 생성 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


# ============== 시뮬레이션 실행 제어 API ==============

@simulation_bp.route('/start', methods=['POST'])
def start_simulation():
    """
    시뮬레이션 실행 시작

    요청 (JSON):
        {
            "simulation_id": "sim_xxxx",          // 필수, 시뮬레이션 ID
            "platform": "parallel",                // 선택 사항: twitter / reddit / parallel (기본값)
            "max_rounds": 60,                      // 선택 사항: 최대 시뮬레이션 라운드 수, 10~60 범위에서 잘라내는 데 사용
            "enable_graph_memory_update": false,   // 선택 사항: 에이전트 활동을 Zep 그래프 메모리에 동적으로 업데이트할지 여부
            "force": false                         // 선택 사항: 강제 재시작 (실행 중인 시뮬레이션을 중지하고 로그를 정리함)
        }

    force 매개변수에 대하여:
        - 활성화되면 시뮬레이션이 실행 중이거나 완료된 경우, 먼저 중지하고 실행 로그를 정리합니다.
        - 정리되는 내용은 run_state.json, actions.jsonl, simulation.log 등입니다.
        - 구성 파일 (simulation_config.json) 및 프로필 파일은 정리되지 않습니다.
        - 시뮬레이션을 다시 실행해야 하는 시나리오에 적합합니다.

    enable_graph_memory_update에 대하여:
        - 활성화되면 시뮬레이션의 모든 에이전트 활동 (게시물 작성, 댓글, 좋아요 등)이 Zep 그래프에 실시간으로 업데이트됩니다.
        - 이를 통해 그래프가 시뮬레이션 과정을 "기억"하여 후속 분석 또는 AI 대화에 사용할 수 있습니다.
        - 시뮬레이션과 연결된 프로젝트에 유효한 graph_id가 필요합니다.
        - API 호출 횟수를 줄이기 위해 배치 업데이트 메커니즘을 사용합니다.

    반환:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "process_pid": 12345,
                "twitter_running": true,
                "reddit_running": true,
                "started_at": "2025-12-01T10:00:00",
                "graph_memory_update_enabled": true,  // 그래프 메모리 업데이트 활성화 여부
                "force_restarted": true               // 강제 재시작 여부
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id를 제공해주세요"
            }), 400

        platform = data.get('platform', 'parallel')
        max_rounds = data.get('max_rounds')  # 선택 사항: 최대 시뮬레이션 라운드 수
        enable_graph_memory_update = data.get('enable_graph_memory_update', False)  # 선택 사항: 그래프 메모리 업데이트 활성화 여부
        force = data.get('force', False)  # 선택 사항: 강제 재시작

        # max_rounds 매개변수 확인
        if max_rounds is not None:
            try:
                max_rounds = int(max_rounds)
                if max_rounds <= 0:
                    return jsonify({
                        "success": False,
                        "error": "max_rounds는 양의 정수여야 합니다"
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "error": "max_rounds는 유효한 정수여야 합니다"
                }), 400

        if max_rounds is None:
            max_rounds = Config.OASIS_MAX_ROUNDS
        else:
            max_rounds = max(10, min(max_rounds, Config.OASIS_MAX_ROUNDS))

        if platform not in ['twitter', 'reddit', 'parallel']:
            return jsonify({
                "success": False,
                "error": f"유효하지 않은 플랫폼 유형입니다: {platform}. 사용 가능한 값: twitter/reddit/parallel"
            }), 400

        # 시뮬레이션 준비 여부 확인
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"시뮬레이션이 존재하지 않음: {simulation_id}"
            }), 404

        enabled_platforms = []
        if state.enable_twitter:
            enabled_platforms.append('twitter')
        if state.enable_reddit:
            enabled_platforms.append('reddit')

        if not enabled_platforms:
            return jsonify({
                "success": False,
                "error": "시뮬레이션이 어떤 플랫폼도 활성화하지 않았습니다"
            }), 400

        if platform == 'parallel' and len(enabled_platforms) == 1:
            platform = enabled_platforms[0]
        elif platform != 'parallel' and platform not in enabled_platforms:
            return jsonify({
                "success": False,
                "error": f"플랫폼 {platform}이(가) 이 시뮬레이션에서 활성화되지 않음"
            }), 400

        force_restarted = False
        
        # 상태 지능적으로 처리: 준비 작업이 완료되면 재시작 허용
        if state.status != SimulationStatus.READY:
            # 준비 작업 완료 여부 확인
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)

            if is_prepared:
                # 준비 작업 완료, 실행 중인 프로세스 확인
                if state.status == SimulationStatus.RUNNING:
                    # 시뮬레이션 프로세스가 실제로 실행 중인지 확인
                    run_state = SimulationRunner.get_run_state(simulation_id)
                    if run_state and run_state.runner_status.value == "running":
                        # 프로세스가 실제로 실행 중임
                        if force:
                            # 강제 모드: 실행 중인 시뮬레이션 중지
                            logger.info(f"강제 모드: 실행 중인 시뮬레이션 {simulation_id} 중지")
                            try:
                                SimulationRunner.stop_simulation(simulation_id)
                            except Exception as e:
                                logger.warning(f"시뮬레이션 중지 시 경고 발생: {str(e)}")
                        else:
                            return jsonify({
                                "success": False,
                                "error": f"시뮬레이션이 실행 중입니다. 먼저 /stop 인터페이스를 호출하여 중지하거나 force=true를 사용하여 강제로 다시 시작해주세요."
                            }), 400

                # 강제 모드인 경우, 실행 로그 정리
                if force:
                    logger.info(f"강제 모드: 시뮬레이션 {simulation_id} 로그 정리")
                    cleanup_result = SimulationRunner.cleanup_simulation_logs(simulation_id)
                    if not cleanup_result.get("success"):
                        logger.warning(f"로그 정리 시 경고 발생: {cleanup_result.get('errors')}")
                    force_restarted = True

                # 프로세스가 존재하지 않거나 종료됨, 상태를 ready로 재설정
                logger.info(f"시뮬레이션 {simulation_id} 준비 작업 완료, 상태를 ready로 재설정 (원래 상태: {state.status.value})")
                state.status = SimulationStatus.READY
                manager._save_simulation_state(state)
            else:
                # 준비 작업 미완료
                return jsonify({
                    "success": False,
                    "error": f"시뮬레이션 준비가 아직 완료되지 않았습니다. 현재 상태: {state.status.value}. 먼저 /prepare 인터페이스를 호출해주세요."
                }), 400
        
        # 그래프 ID 가져오기 (그래프 메모리 업데이트용)
        graph_id = None
        if enable_graph_memory_update:
            # 시뮬레이션 상태 또는 프로젝트에서 graph_id 가져오기
            graph_id = state.graph_id
            if not graph_id:
                # 프로젝트에서 가져오기 시도
                project = ProjectManager.get_project(state.project_id)
                if project:
                    graph_id = project.graph_id
            
            if not graph_id:
                return jsonify({
                    "success": False,
                    "error": "그래프 메모리 업데이트를 활성화하려면 유효한 graph_id가 필요합니다. 프로젝트가 그래프를 구축했는지 확인해주세요."
                }), 400
            
            logger.info(f"그래프 메모리 업데이트 활성화: simulation_id={simulation_id}, graph_id={graph_id}")

        try:
            CapacityGuard.ensure_simulation_start_capacity()
        except CapacityExceededError as capacity_error:
            return _capacity_error_response(capacity_error)
        
        # 시뮬레이션 시작
        run_state = SimulationRunner.start_simulation(
            simulation_id=simulation_id,
            platform=platform,
            max_rounds=max_rounds,
            enable_graph_memory_update=enable_graph_memory_update,
            graph_id=graph_id
        )
        
        # 시뮬레이션 상태 업데이트
        state.status = SimulationStatus.RUNNING
        manager._save_simulation_state(state)
        
        response_data = run_state.to_dict()
        if max_rounds:
            response_data['max_rounds_applied'] = max_rounds
        response_data['graph_memory_update_enabled'] = enable_graph_memory_update
        response_data['force_restarted'] = force_restarted
        if enable_graph_memory_update:
            response_data['graph_id'] = graph_id
        
        return jsonify({
            "success": True,
            "data": response_data
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"시뮬레이션 시작 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/stop', methods=['POST'])
def stop_simulation():
    """
    시뮬레이션 중지
    
    요청 (JSON):
        {
            "simulation_id": "sim_xxxx"  // 필수, 시뮬레이션 ID
        }
    
    반환:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "stopped",
                "completed_at": "2025-12-01T12:00:00"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id를 제공해주세요"
            }), 400
        
        run_state = SimulationRunner.stop_simulation(simulation_id)
        
        # 시뮬레이션 상태 업데이트
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if state:
            state.status = SimulationStatus.STOPPED
            manager._save_simulation_state(state)
        
        return jsonify({
            "success": True,
            "data": run_state.to_dict()
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"시뮬레이션 중지 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


# ============== 실시간 상태 모니터링 API ==============

@simulation_bp.route('/<simulation_id>/run-status', methods=['GET'])
def get_run_status(simulation_id: str):
    """
    시뮬레이션 실행 실시간 상태 가져오기 (프런트엔드 폴링용)
    
    반환:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "current_round": 5,
                "total_rounds": 144,
                "progress_percent": 3.5,
                "simulated_hours": 2,
                "total_simulation_hours": 72,
                "twitter_running": true,
                "reddit_running": true,
                "twitter_actions_count": 150,
                "reddit_actions_count": 200,
                "total_actions_count": 350,
                "started_at": "2025-12-01T10:00:00",
                "updated_at": "2025-12-01T10:30:00"
            }
        }
    """
    try:
        run_state = SimulationRunner.get_run_state(simulation_id)
        
        if not run_state:
            return jsonify({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "runner_status": "idle",
                    "current_round": 0,
                    "total_rounds": 0,
                    "progress_percent": 0,
                    "twitter_actions_count": 0,
                    "reddit_actions_count": 0,
                    "total_actions_count": 0,
                }
            })
        
        return jsonify({
            "success": True,
            "data": run_state.to_dict()
        })
        
    except Exception as e:
        logger.error(f"실행 상태 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/<simulation_id>/run-status/detail', methods=['GET'])
def get_run_status_detail(simulation_id: str):
    """
    시뮬레이션 실행 상세 상태 가져오기 (모든 동작 포함)
    
    프런트엔드 실시간 동적 표시용
    
    쿼리 매개변수:
        platform: 플랫폼 필터링 (twitter/reddit, 선택 사항)
    
    반환:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "current_round": 5,
                ...
                "all_actions": [
                    {
                        "round_num": 5,
                        "timestamp": "2025-12-01T10:30:00",
                        "platform": "twitter",
                        "agent_id": 3,
                        "agent_name": "Agent Name",
                        "action_type": "CREATE_POST",
                        "action_args": {"content": "..."},
                        "result": null,
                        "success": true
                    },
                    ...
                ],
                "twitter_actions": [...],  # Twitter 플랫폼의 모든 동작
                "reddit_actions": [...]    # Reddit 플랫폼의 모든 동작
            }
        }
    """
    try:
        run_state = SimulationRunner.get_run_state(simulation_id)
        platform_filter = request.args.get('platform')
        
        if not run_state:
            return jsonify({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "runner_status": "idle",
                    "all_actions": [],
                    "twitter_actions": [],
                    "reddit_actions": []
                }
            })
        
        # 전체 동작 목록 가져오기
        all_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform=platform_filter
        )
        
        # 플랫폼별 동작 가져오기
        twitter_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform="twitter"
        ) if not platform_filter or platform_filter == "twitter" else []
        
        reddit_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform="reddit"
        ) if not platform_filter or platform_filter == "reddit" else []
        
        # 현재 라운드 동작 가져오기 (recent_actions는 최신 라운드만 표시)
        current_round = run_state.current_round
        recent_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform=platform_filter,
            round_num=current_round
        ) if current_round > 0 else []
        
        # 기본 상태 정보 가져오기
        result = run_state.to_dict()
        result["all_actions"] = [a.to_dict() for a in all_actions]
        result["twitter_actions"] = [a.to_dict() for a in twitter_actions]
        result["reddit_actions"] = [a.to_dict() for a in reddit_actions]
        result["rounds_count"] = len(run_state.rounds)
        # recent_actions는 현재 최신 라운드의 두 플랫폼 콘텐츠만 표시
        result["recent_actions"] = [a.to_dict() for a in recent_actions]
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"상세 상태 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/<simulation_id>/actions', methods=['GET'])
def get_simulation_actions(simulation_id: str):
    """
    시뮬레이션 에이전트 동작 기록 가져오기
    
    쿼리 매개변수:
        limit: 반환 수량 (기본값 100)
        offset: 오프셋 (기본값 0)
        platform: 플랫폼 필터링 (twitter/reddit)
        agent_id: 에이전트 ID 필터링
        round_num: 라운드 필터링
    
    반환:
        {
            "success": true,
            "data": {
                "count": 100,
                "actions": [...]
            }
        }
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        platform = request.args.get('platform')
        agent_id = request.args.get('agent_id', type=int)
        round_num = request.args.get('round_num', type=int)
        
        actions = SimulationRunner.get_actions(
            simulation_id=simulation_id,
            limit=limit,
            offset=offset,
            platform=platform,
            agent_id=agent_id,
            round_num=round_num
        )
        
        return jsonify({
            "success": True,
            "data": {
                "count": len(actions),
                "actions": [a.to_dict() for a in actions]
            }
        })
        
    except Exception as e:
        logger.error(f"동작 기록 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/<simulation_id>/timeline', methods=['GET'])
def get_simulation_timeline(simulation_id: str):
    """
    시뮬레이션 타임라인 가져오기 (라운드별 요약)
    
    프런트엔드 진행률 표시줄 및 타임라인 뷰 표시용
    
    쿼리 매개변수:
        start_round: 시작 라운드 (기본값 0)
        end_round: 종료 라운드 (기본값 전체)
    
    각 라운드의 요약 정보 반환
    """
    try:
        start_round = request.args.get('start_round', 0, type=int)
        end_round = request.args.get('end_round', type=int)
        
        timeline = SimulationRunner.get_timeline(
            simulation_id=simulation_id,
            start_round=start_round,
            end_round=end_round
        )
        
        return jsonify({
            "success": True,
            "data": {
                "rounds_count": len(timeline),
                "timeline": timeline
            }
        })
        
    except Exception as e:
        logger.error(f"타임라인 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/<simulation_id>/agent-stats', methods=['GET'])
def get_agent_stats(simulation_id: str):
    """
    각 에이전트의 통계 정보 가져오기
    
    프런트엔드 에이전트 활동 순위, 동작 분포 등을 표시하는 데 사용
    """
    try:
        stats = SimulationRunner.get_agent_stats(simulation_id)
        
        return jsonify({
            "success": True,
            "data": {
                "agents_count": len(stats),
                "stats": stats
            }
        })
        
    except Exception as e:
        logger.error(f"에이전트 통계 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


# ============== 데이터베이스 조회 API ==============

@simulation_bp.route('/<simulation_id>/posts', methods=['GET'])
def get_simulation_posts(simulation_id: str):
    """
    시뮬레이션 게시물 가져오기
    
    쿼리 매개변수:
        platform: 플랫폼 유형 (twitter/reddit)
        limit: 반환 수량 (기본값 50)
        offset: 오프셋
    
    게시물 목록 반환 (SQLite 데이터베이스에서 읽음)
    """
    try:
        platform = request.args.get('platform', 'reddit')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        sim_dir = os.path.join(
            os.path.dirname(__file__),
            f'../../uploads/simulations/{simulation_id}'
        )
        
        db_file = f"{platform}_simulation.db"
        db_path = os.path.join(sim_dir, db_file)
        
        if not os.path.exists(db_path):
            return jsonify({
                "success": True,
                "data": {
                    "platform": platform,
                    "count": 0,
                    "posts": [],
                    "message": "데이터베이스가 존재하지 않습니다. 시뮬레이션이 아직 실행되지 않았을 수 있습니다."
                }
            })
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM post 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            posts = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT COUNT(*) FROM post")
            total = cursor.fetchone()[0]
            
        except sqlite3.OperationalError:
            posts = []
            total = 0
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "platform": platform,
                "total": total,
                "count": len(posts),
                "posts": posts
            }
        })
        
    except Exception as e:
        logger.error(f"게시물 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/<simulation_id>/comments', methods=['GET'])
def get_simulation_comments(simulation_id: str):
    """
    시뮬레이션 댓글 가져오기 (Reddit만 해당)
    
    쿼리 매개변수:
        post_id: 게시물 ID 필터링 (선택 사항)
        limit: 반환 수량
        offset: 오프셋
    """
    try:
        post_id = request.args.get('post_id')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        sim_dir = os.path.join(
            os.path.dirname(__file__),
            f'../../uploads/simulations/{simulation_id}'
        )
        
        db_path = os.path.join(sim_dir, "reddit_simulation.db")
        
        if not os.path.exists(db_path):
            return jsonify({
                "success": True,
                "data": {
                    "count": 0,
                    "comments": []
                }
            })
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if post_id:
                cursor.execute("""
                    SELECT * FROM comment 
                    WHERE post_id = ?
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (post_id, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM comment 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            comments = [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.OperationalError:
            comments = []
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "count": len(comments),
                "comments": comments
            }
        })
        
    except Exception as e:
        logger.error(f"댓글 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


# ============== 인터뷰 API ==============

@simulation_bp.route('/interview', methods=['POST'])
def interview_agent():
    """
    단일 에이전트 인터뷰

    참고: 이 기능은 시뮬레이션 환경이 실행 중인 상태여야 합니다 (시뮬레이션 루프 완료 후 명령 대기 모드 진입).

    요청 (JSON):
        {
            "simulation_id": "sim_xxxx",       // 필수, 시뮬레이션 ID
            "agent_id": 0,                     // 필수, 에이전트 ID
            "prompt": "이 일에 대해 어떻게 생각하세요?",  // 필수, 인터뷰 질문
            "platform": "twitter",             // 선택 사항, 플랫폼 지정 (twitter/reddit)
                                               // 지정하지 않을 경우: 두 플랫폼 시뮬레이션에서 동시에 두 플랫폼을 인터뷰
            "timeout": 60                      // 선택 사항, 타임아웃 시간 (초), 기본값 60
        }

    반환 (platform 지정 안 함, 두 플랫폼 모드):
        {
            "success": true,
            "data": {
                "agent_id": 0,
                "prompt": "이 일에 대해 어떻게 생각하세요?",
                "result": {
                    "agent_id": 0,
                    "prompt": "...",
                    "platforms": {
                        "twitter": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit": {"agent_id": 0, "response": "...", "platform": "reddit"}
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }

    반환 (platform 지정):
        {
            "success": true,
            "data": {
                "agent_id": 0,
                "prompt": "이 일에 대해 어떻게 생각하세요?",
                "result": {
                    "agent_id": 0,
                    "response": "저는 ...라고 생각합니다.",
                    "platform": "twitter",
                    "timestamp": "2025-12-08T10:00:00"
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        agent_id = data.get('agent_id')
        prompt = data.get('prompt')
        platform = data.get('platform')  # 선택 사항: twitter/reddit/None
        timeout = data.get('timeout', 60)
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id를 제공해주세요"
            }), 400
        
        if agent_id is None:
            return jsonify({
                "success": False,
                "error": "agent_id를 제공해주세요"
            }), 400
        
        if not prompt:
            return jsonify({
                "success": False,
                "error": "prompt (인터뷰 질문)를 제공해주세요"
            }), 400
        
        # platform 매개변수 확인
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": "platform 매개변수는 'twitter' 또는 'reddit'만 가능합니다"
            }), 400
        
        # 환경 상태 확인
        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": "시뮬레이션 환경이 실행 중이 아니거나 종료되었습니다. 시뮬레이션이 완료되고 명령 대기 모드에 진입했는지 확인해주세요."
            }), 400
        
        # prompt 최적화, 에이전트가 도구를 호출하는 것을 방지하기 위해 접두사 추가
        optimized_prompt = optimize_interview_prompt(prompt)
        
        result = SimulationRunner.interview_agent(
            simulation_id=simulation_id,
            agent_id=agent_id,
            prompt=optimized_prompt,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": f"인터뷰 응답 대기 시간 초과: {str(e)}"
        }), 504
        
    except Exception as e:
        logger.error(f"인터뷰 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/interview/batch', methods=['POST'])
def interview_agents_batch():
    """
    여러 에이전트 일괄 인터뷰

    참고: 이 기능은 시뮬레이션 환경이 실행 중인 상태여야 합니다.

    요청 (JSON):
        {
            "simulation_id": "sim_xxxx",       // 필수, 시뮬레이션 ID
            "interviews": [                    // 필수, 인터뷰 목록
                {
                    "agent_id": 0,
                    "prompt": "A에 대해 어떻게 생각하세요?",
                    "platform": "twitter"      // 선택 사항, 해당 에이전트의 인터뷰 플랫폼 지정
                },
                {
                    "agent_id": 1,
                    "prompt": "B에 대해 어떻게 생각하세요?"  // platform을 지정하지 않으면 기본값을 사용합니다.
                }
            ],
            "platform": "reddit",              // 선택 사항, 기본 플랫폼 (각 항목의 platform에 의해 덮어쓰여짐)
                                               // 지정하지 않을 경우: 두 플랫폼 시뮬레이션에서 각 에이전트가 동시에 두 플랫폼을 인터뷰
            "timeout": 120                     // 선택 사항, 타임아웃 시간 (초), 기본값 120
        }

    반환:
        {
            "success": true,
            "data": {
                "interviews_count": 2,
                "result": {
                    "interviews_count": 4,
                    "results": {
                        "twitter_0": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit_0": {"agent_id": 0, "response": "...", "platform": "reddit"},
                        "twitter_1": {"agent_id": 1, "response": "...", "platform": "twitter"},
                        "reddit_1": {"agent_id": 1, "response": "...", "platform": "reddit"}
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        interviews = data.get('interviews')
        platform = data.get('platform')  # 선택 사항: twitter/reddit/None
        timeout = data.get('timeout', 120)

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id를 제공해주세요"
            }), 400

        if not interviews or not isinstance(interviews, list):
            return jsonify({
                "success": False,
                "error": "interviews (인터뷰 목록)를 제공해주세요"
            }), 400

        # platform 매개변수 확인
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": "platform 매개변수는 'twitter' 또는 'reddit'만 가능합니다"
            }), 400

        # 각 인터뷰 항목 확인
        for i, interview in enumerate(interviews):
            if 'agent_id' not in interview:
                return jsonify({
                    "success": False,
                    "error": f"인터뷰 목록 제{i+1}항목에 agent_id 누락"
                }), 400
            if 'prompt' not in interview:
                return jsonify({
                    "success": False,
                    "error": f"인터뷰 목록 제{i+1}항목에 prompt 누락"
                }), 400
            # 각 항목의 platform 확인 (있는 경우)
            item_platform = interview.get('platform')
            if item_platform and item_platform not in ("twitter", "reddit"):
                return jsonify({
                    "success": False,
                    "error": f"인터뷰 목록 제{i+1}항목의 platform은 'twitter' 또는 'reddit'만 가능합니다"
                }), 400

        # 환경 상태 확인
        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": "시뮬레이션 환경이 실행 중이 아니거나 종료되었습니다. 시뮬레이션이 완료되고 명령 대기 모드에 진입했는지 확인해주세요."
            }), 400

        # 각 인터뷰 항목의 prompt 최적화, 에이전트가 도구를 호출하는 것을 방지하기 위해 접두사 추가
        optimized_interviews = []
        for interview in interviews:
            optimized_interview = interview.copy()
            optimized_interview['prompt'] = optimize_interview_prompt(interview.get('prompt', ''))
            optimized_interviews.append(optimized_interview)

        result = SimulationRunner.interview_agents_batch(
            simulation_id=simulation_id,
            interviews=optimized_interviews,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": f"일괄 인터뷰 응답 대기 시간 초과: {str(e)}"
        }), 504

    except Exception as e:
        logger.error(f"일괄 인터뷰 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/interview/all', methods=['POST'])
def interview_all_agents():
    """
    전역 인터뷰 - 동일한 질문으로 모든 에이전트 인터뷰

    참고: 이 기능은 시뮬레이션 환경이 실행 중인 상태여야 합니다.

    요청 (JSON):
        {
            "simulation_id": "sim_xxxx",            // 필수, 시뮬레이션 ID
            "prompt": "이 일 전체에 대해 어떻게 생각하세요?",  // 필수, 인터뷰 질문 (모든 에이전트가 동일한 질문 사용)
            "platform": "reddit",                   // 선택 사항, 플랫폼 지정 (twitter/reddit)
                                                    // 지정하지 않을 경우: 두 플랫폼 시뮬레이션에서 각 에이전트가 동시에 두 플랫폼을 인터뷰
            "timeout": 180                          // 선택 사항, 타임아웃 시간 (초), 기본값 180
        }

    반환:
        {
            "success": true,
            "data": {
                "interviews_count": 50,
                "result": {
                    "interviews_count": 100,
                    "results": {
                        "twitter_0": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit_0": {"agent_id": 0, "response": "...", "platform": "reddit"},
                        ...
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        prompt = data.get('prompt')
        platform = data.get('platform')  # 선택 사항: twitter/reddit/None
        timeout = data.get('timeout', 180)

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id를 제공해주세요"
            }), 400

        if not prompt:
            return jsonify({
                "success": False,
                "error": "prompt (인터뷰 질문)를 제공해주세요"
            }), 400

        # platform 매개변수 확인
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": "platform 매개변수는 'twitter' 또는 'reddit'만 가능합니다"
            }), 400

        # 환경 상태 확인
        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": "시뮬레이션 환경이 실행 중이 아니거나 종료되었습니다. 시뮬레이션이 완료되고 명령 대기 모드에 진입했는지 확인해주세요."
            }), 400

        # prompt 최적화, 에이전트가 도구를 호출하는 것을 방지하기 위해 접두사 추가
        optimized_prompt = optimize_interview_prompt(prompt)

        result = SimulationRunner.interview_all_agents(
            simulation_id=simulation_id,
            prompt=optimized_prompt,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": f"전역 인터뷰 응답 대기 시간 초과: {str(e)}"
        }), 504

    except Exception as e:
        logger.error(f"전역 인터뷰 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/interview/history', methods=['POST'])
def get_interview_history():
    """
    인터뷰 기록 가져오기

    시뮬레이션 데이터베이스에서 모든 인터뷰 기록 읽기

    요청 (JSON):
        {
            "simulation_id": "sim_xxxx",  // 필수, 시뮬레이션 ID
            "platform": "reddit",          // 선택 사항, 플랫폼 유형 (reddit/twitter)
                                           // 지정하지 않으면 두 플랫폼의 모든 기록 반환
            "agent_id": 0,                 // 선택 사항, 해당 에이전트의 인터뷰 기록만 가져옴
            "limit": 100                   // 선택 사항, 반환 수량, 기본값 100
        }

    반환:
        {
            "success": true,
            "data": {
                "count": 10,
                "history": [
                    {
                        "agent_id": 0,
                        "response": "저는 ...라고 생각합니다.",
                        "prompt": "이 일에 대해 어떻게 생각하세요?",
                        "timestamp": "2025-12-08T10:00:00",
                        "platform": "reddit"
                    },
                    ...
                ]
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        platform = data.get('platform')  # 지정하지 않으면 두 플랫폼의 기록 반환
        agent_id = data.get('agent_id')
        limit = data.get('limit', 100)
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id를 제공해주세요"
            }), 400

        history = SimulationRunner.get_interview_history(
            simulation_id=simulation_id,
            platform=platform,
            agent_id=agent_id,
            limit=limit
        )

        return jsonify({
            "success": True,
            "data": {
                "count": len(history),
                "history": history
            }
        })

    except Exception as e:
        logger.error(f"인터뷰 기록 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/env-status', methods=['POST'])
def get_env_status():
    """
    시뮬레이션 환경 상태 가져오기

    시뮬레이션 환경이 활성 상태인지 확인 (인터뷰 명령을 받을 수 있는지)

    요청 (JSON):
        {
            "simulation_id": "sim_xxxx"  // 필수, 시뮬레이션 ID
        }

    반환:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "env_alive": true,
                "twitter_available": true,
                "reddit_available": true,
                "message": "환경이 실행 중이며 인터뷰 명령을 받을 수 있습니다"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id를 제공해주세요"
            }), 400

        env_alive = SimulationRunner.check_env_alive(simulation_id)
        
        # 더 상세한 상태 정보 가져오기
        env_status = SimulationRunner.get_env_status_detail(simulation_id)

        if env_alive:
            message = "환경이 실행 중이며 인터뷰 명령을 받을 수 있습니다"
        else:
            message = "환경이 실행 중이 아니거나 종료되었습니다"

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "env_alive": env_alive,
                "twitter_available": env_status.get("twitter_available", False),
                "reddit_available": env_status.get("reddit_available", False),
                "message": message
            }
        })

    except Exception as e:
        logger.error(f"환경 상태 가져오기 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@simulation_bp.route('/close-env', methods=['POST'])
def close_simulation_env():
    """
    시뮬레이션 환경 종료
    
    시뮬레이션에 환경 종료 명령을 보내 대기 명령 모드를 우아하게 종료하도록 합니다.
    
    참고: 이것은 /stop 인터페이스와 다릅니다. /stop은 프로세스를 강제로 종료하지만,
    이 인터페이스는 시뮬레이션이 환경을 우아하게 종료하고 나가도록 합니다.
    
    요청 (JSON):
        {
            "simulation_id": "sim_xxxx",  // 필수, 시뮬레이션 ID
            "timeout": 30                  // 선택 사항, 타임아웃 시간 (초), 기본값 30
        }
    
    반환:
        {
            "success": true,
            "data": {
                "message": "환경 종료 명령이 전송되었습니다",
                "result": {...},
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        timeout = data.get('timeout', 30)
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id를 제공해주세요"
            }), 400
        
        result = SimulationRunner.close_simulation_env(
            simulation_id=simulation_id,
            timeout=timeout
        )
        
        return jsonify({
            "success": result.get("success", False),
            "data": result
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"환경 종료 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500
