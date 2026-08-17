"""
그래프 관련 API 라우트
프로젝트 컨텍스트 메커니즘을 사용하여 서버 측 상태를 영구화합니다.
"""

import os
import traceback
import threading
from flask import request, jsonify

from . import graph_bp
from ..config import Config
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilderService
from ..services.preanalysis_service import PreanalysisService
from ..services.capacity_guard import CapacityGuard, CapacityExceededError
from ..services.text_processor import TextProcessor
from ..services.runtime_recovery import reconcile_graph_project_state
from ..utils.file_parser import FileParser
from ..utils.api_response import error_traceback_payload
from ..utils.logger import get_logger
from ..models.task import TaskManager, TaskStatus
from ..models.project import ProjectManager, ProjectStatus

# 로거 가져오기
logger = get_logger('tiresias.api')


def _capacity_error_response(error: CapacityExceededError):
    response = jsonify(error.to_payload())
    response.status_code = 429
    response.headers['Retry-After'] = str(Config.CAPACITY_RETRY_AFTER_SECONDS)
    return response


def allowed_file(filename: str) -> bool:
    """파일 확장자가 허용되는지 확인"""
    if not filename or '.' not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    return ext in Config.ALLOWED_EXTENSIONS


# ============== 프로젝트 관리 인터페이스 ==============

@graph_bp.route('/preanalysis', methods=['POST'])
def preanalyze_uploads():
    """견적 전 경량 사전분석."""
    files = request.files.getlist('files')
    requirement = str(request.form.get('simulation_requirement') or '').strip()

    valid_files = [file for file in files if file and allowed_file(file.filename)]
    if not valid_files:
        return jsonify({
            "success": False,
            "error": "분석할 파일이 없습니다.",
        }), 400

    try:
        service = PreanalysisService()
        result = service.analyze_uploaded_files(valid_files, requirement=requirement)
        return jsonify({
            "success": True,
            "data": result,
        })
    except Exception as error:
        logger.exception("사전분석 실패: %s", error)
        payload = {
            "success": False,
            "error": f"사전분석 실패: {error}",
        }
        if Config.EXPOSE_TRACEBACKS:
            payload["traceback"] = traceback.format_exc()
        return jsonify(payload), 500

@graph_bp.route('/project/<project_id>', methods=['GET'])
def get_project(project_id: str):
    """
    프로젝트 상세 정보 가져오기
    """
    project = reconcile_graph_project_state(ProjectManager.get_project(project_id))
    
    if not project:
        return jsonify({
            "success": False,
            "error": f"프로젝트가 존재하지 않습니다: {project_id}"
        }), 404
    
    return jsonify({
        "success": True,
        "data": project.to_dict()
    })


@graph_bp.route('/project/list', methods=['GET'])
def list_projects():
    """
    모든 프로젝트 나열
    """
    limit = request.args.get('limit', 50, type=int)
    projects = ProjectManager.list_projects(limit=limit)
    
    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in projects],
        "count": len(projects)
    })


@graph_bp.route('/project/<project_id>', methods=['DELETE'])
def delete_project(project_id: str):
    """
    프로젝트 삭제
    """
    success = ProjectManager.delete_project(project_id)
    
    if not success:
        return jsonify({
            "success": False,
            "error": f"프로젝트가 존재하지 않거나 삭제에 실패했습니다: {project_id}"
        }), 404
    
    return jsonify({
        "success": True,
        "message": f"프로젝트가 삭제되었습니다: {project_id}"
    })


@graph_bp.route('/project/<project_id>/reset', methods=['POST'])
def reset_project(project_id: str):
    """
    프로젝트 상태 재설정 (그래프 재구축용)
    """
    project = ProjectManager.get_project(project_id)
    
    if not project:
        return jsonify({
            "success": False,
            "error": f"프로젝트가 존재하지 않습니다: {project_id}"
        }), 404
    
    # 온톨로지 생성 완료 상태로 재설정
    if project.ontology:
        project.status = ProjectStatus.ONTOLOGY_GENERATED
    else:
        project.status = ProjectStatus.CREATED
    
    project.graph_id = None
    project.graph_build_task_id = None
    project.error = None
    ProjectManager.save_project(project)
    
    return jsonify({
        "success": True,
        "message": f"프로젝트가 재설정되었습니다: {project_id}",
        "data": project.to_dict()
    })


# ============== 인터페이스 1: 파일 업로드 및 온톨로지 생성 ==============

@graph_bp.route('/ontology/generate', methods=['POST'])
def generate_ontology():
    """
    인터페이스 1: 파일을 업로드하고 온톨로지 정의를 분석하여 생성
    
    요청 방식: multipart/form-data
    
    매개변수:
        files: 업로드할 파일 (PDF/MD/TXT), 여러 개 가능
        simulation_requirement: 시뮬레이션 요구사항 설명 (필수)
        project_name: 프로젝트 이름 (선택 사항)
        additional_context: 추가 설명 (선택 사항)
        
    반환:
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "ontology": {
                    "entity_types": [...],
                    "edge_types": [...],
                    "analysis_summary": "..."
                },
                "files": [...],
                "total_text_length": 12345
            }
        }
    """
    try:
        logger.info("=== 온톨로지 정의 생성 시작 ===")
        
        # 매개변수 가져오기
        simulation_requirement = request.form.get('simulation_requirement', '')
        project_name = request.form.get('project_name', 'Unnamed Project')
        additional_context = request.form.get('additional_context', '')
        
        logger.debug(f"프로젝트 이름: {project_name}")
        logger.debug(f"시뮬레이션 요구사항: {simulation_requirement[:100]}...")
        
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "시뮬레이션 요구사항 설명 (simulation_requirement)을 제공해주세요"
            }), 400
        
        # 업로드된 파일 가져오기
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or all(not f.filename for f in uploaded_files):
            return jsonify({
                "success": False,
                "error": "적어도 하나의 문서 파일을 업로드해주세요"
            }), 400
        
        # 프로젝트 생성
        project = ProjectManager.create_project(name=project_name)
        project.simulation_requirement = simulation_requirement
        logger.info(f"프로젝트 생성: {project.project_id}")
        
        # 파일 저장 및 텍스트 추출
        document_texts = []
        all_text = ""
        
        file_errors = []

        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                # 프로젝트 디렉토리에 파일 저장
                file_info = ProjectManager.save_file_to_project(
                    project.project_id, 
                    file, 
                    file.filename
                )
                project.files.append({
                    "filename": file_info["original_filename"],
                    "size": file_info["size"]
                })
                
                try:
                    # 텍스트 추출
                    text = FileParser.extract_text(file_info["path"])
                    text = TextProcessor.preprocess_text(text)
                except Exception as extraction_error:
                    logger.warning(
                        "파일 텍스트 추출 실패: file=%s, error=%s",
                        file_info["original_filename"],
                        extraction_error,
                    )
                    file_errors.append(
                        f"{file_info['original_filename']}: {str(extraction_error)}"
                    )
                    continue

                document_texts.append(text)
                all_text += f"\n\n=== {file_info['original_filename']} ===\n{text}"
        
        if not document_texts:
            ProjectManager.delete_project(project.project_id)
            return jsonify({
                "success": False,
                "error": "어떤 문서도 성공적으로 처리되지 않았습니다. 파일 형식 또는 PDF 텍스트 추출 가능 여부를 확인해주세요.",
                "details": file_errors,
            }), 400
        
        # 추출된 텍스트 저장
        project.total_text_length = len(all_text)
        ProjectManager.save_extracted_text(project.project_id, all_text)
        logger.info(f"텍스트 추출 완료, 총 {len(all_text)} 문자")
        
        # 온톨로지 생성
        logger.info("LLM을 호출하여 온톨로지 정의 생성...")
        generator = OntologyGenerator()
        ontology = generator.generate(
            document_texts=document_texts,
            simulation_requirement=simulation_requirement,
            additional_context=additional_context if additional_context else None
        )
        
        # 온톨로지를 프로젝트에 저장
        entity_count = len(ontology.get("entity_types", []))
        edge_count = len(ontology.get("edge_types", []))
        logger.info(f"온톨로지 생성 완료: {entity_count} 개의 엔티티 타입, {edge_count} 개의 관계 타입")
        
        project.ontology = {
            "entity_types": ontology.get("entity_types", []),
            "edge_types": ontology.get("edge_types", [])
        }
        project.analysis_summary = ontology.get("analysis_summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        ProjectManager.save_project(project)
        logger.info(f"=== 온톨로지 생성 완료 === 프로젝트 ID: {project.project_id}")
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project.project_id,
                "project_name": project.name,
                "ontology": project.ontology,
                "analysis_summary": project.analysis_summary,
                "files": project.files,
                "total_text_length": project.total_text_length
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


# ============== 인터페이스 2: 그래프 구축 ==============

@graph_bp.route('/build', methods=['POST'])
def build_graph():
    """
    인터페이스 2: project_id에 따라 그래프 구축
    
    요청 (JSON):
        {
            "project_id": "proj_xxxx",  // 필수, 인터페이스 1에서 가져옴
            "graph_name": "그래프 이름",    // 선택 사항
            "chunk_size": 500,          // 선택 사항, 기본값 500
            "chunk_overlap": 50         // 선택 사항, 기본값 50
        }
        
    반환:
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "task_id": "task_xxxx",
                "message": "그래프 구축 작업이 시작되었습니다"
            }
        }
    """
    try:
        logger.info("=== 그래프 구축 시작 ===")
        
        # 구성 확인
        errors = []
        errors.extend(Config.validate_graph_backend())
        if errors:
            logger.error(f"구성 오류: {errors}")
            return jsonify({
                "success": False,
                "error": "구성 오류: " + "; ".join(errors)
            }), 500
        
        # 요청 파싱
        data = request.get_json() or {}
        project_id = data.get('project_id')
        logger.debug(f"요청 매개변수: project_id={project_id}")
        
        if not project_id:
            return jsonify({
                "success": False,
                "error": "project_id를 제공해주세요"
            }), 400
        
        # 프로젝트 가져오기
        project = reconcile_graph_project_state(ProjectManager.get_project(project_id))
        if not project:
            return jsonify({
                "success": False,
                "error": f"프로젝트가 존재하지 않습니다: {project_id}"
            }), 404
        
        # 프로젝트 상태 확인
        force = data.get('force', False)  # 강제 재구축
        
        if project.status == ProjectStatus.CREATED:
            return jsonify({
                "success": False,
                "error": "프로젝트가 아직 온톨로지를 생성하지 않았습니다. 먼저 /ontology/generate를 호출해주세요"
            }), 400
        
        if project.status == ProjectStatus.GRAPH_BUILDING and not force:
            return jsonify({
                "success": False,
                "error": "그래프가 구축 중입니다. 중복 제출하지 마세요. 강제 재구축이 필요한 경우 force: true를 추가해주세요",
                "task_id": project.graph_build_task_id
            }), 400
        
        # 강제 재구축인 경우, 상태 재설정
        if force and project.status in [ProjectStatus.GRAPH_BUILDING, ProjectStatus.FAILED, ProjectStatus.GRAPH_COMPLETED]:
            project.status = ProjectStatus.ONTOLOGY_GENERATED
            project.graph_id = None
            project.graph_build_task_id = None
            project.error = None

        try:
            CapacityGuard.ensure_graph_build_capacity()
        except CapacityExceededError as capacity_error:
            return _capacity_error_response(capacity_error)
        
        # 구성 가져오기
        graph_name = data.get('graph_name', project.name or 'Tiresias Graph')
        chunk_size = data.get('chunk_size', project.chunk_size or Config.DEFAULT_CHUNK_SIZE)
        chunk_overlap = data.get('chunk_overlap', project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP)
        
        # 프로젝트 구성 업데이트
        project.chunk_size = chunk_size
        project.chunk_overlap = chunk_overlap
        
        # 추출된 텍스트 가져오기
        text = ProjectManager.get_extracted_text(project_id)
        if not text or len(text.strip()) < FileParser.PDF_OCR_MIN_TEXT:
            project_file_paths = ProjectManager.get_project_files(project_id)
            refreshed_sections = []

            for project_file_path in project_file_paths:
                try:
                    refreshed_text = TextProcessor.preprocess_text(
                        FileParser.extract_text(project_file_path)
                    )
                except Exception as extraction_error:
                    logger.warning(
                        "그래프 구축 전 텍스트 재추출 실패: project_id=%s, file=%s, error=%s",
                        project_id,
                        project_file_path,
                        extraction_error,
                    )
                    continue

                if refreshed_text:
                    refreshed_sections.append(
                        f"\n\n=== {os.path.basename(project_file_path)} ===\n{refreshed_text}"
                    )

            if refreshed_sections:
                text = "".join(refreshed_sections).strip()
                project.total_text_length = len(text)
                ProjectManager.save_extracted_text(project_id, text)
                ProjectManager.save_project(project)
                logger.info(
                    "그래프 구축 전 텍스트 재추출 완료: project_id=%s, total_text=%s",
                    project_id,
                    len(text),
                )

        if not text:
            return jsonify({
                "success": False,
                "error": "추출된 텍스트 내용을 찾을 수 없습니다"
            }), 400
        
        # 온톨로지 가져오기
        ontology = project.ontology
        if not ontology:
            return jsonify({
                "success": False,
                "error": "온톨로지 정의를 찾을 수 없습니다"
            }), 400
        
        # 비동기 작업 생성
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="graph_build",
            metadata={
                "project_id": project_id,
                "graph_name": graph_name,
            },
        )
        logger.info(f"그래프 구축 작업 생성: task_id={task_id}, project_id={project_id}")
        
        # 프로젝트 상태 업데이트
        project.status = ProjectStatus.GRAPH_BUILDING
        project.graph_build_task_id = task_id
        ProjectManager.save_project(project)
        
        # 백그라운드 작업 시작
        def build_task():
            build_logger = get_logger('tiresias.build')
            try:
                build_logger.info(f"[{task_id}] 그래프 구축 시작...")
                task_manager.update_task(
                    task_id, 
                    status=TaskStatus.PROCESSING,
                    message="그래프 구축 서비스 초기화..."
                )
                
                # 그래프 구축 서비스 생성
                builder = GraphBuilderService()
                
                # 청크 분할
                task_manager.update_task(
                    task_id,
                    message="텍스트 청크 분할 중...",
                    progress=5
                )
                chunks = TextProcessor.split_text(
                    text, 
                    chunk_size=chunk_size, 
                    overlap=chunk_overlap
                )
                total_chunks = len(chunks)
                
                # 그래프 생성
                task_manager.update_task(
                    task_id,
                    message="로컬 그래프 생성...",
                    progress=10
                )
                graph_id = builder.create_graph(name=graph_name)
                
                # 프로젝트의 graph_id 업데이트
                project.graph_id = graph_id
                ProjectManager.save_project(project)
                
                # 온톨로지 설정
                task_manager.update_task(
                    task_id,
                    message="온톨로지 정의 설정...",
                    progress=15
                )
                builder.set_ontology(graph_id, ontology)
                
                # 텍스트 추가 (progress_callback 서명은 (msg, progress_ratio)입니다)
                def add_progress_callback(msg, progress_ratio):
                    progress = 15 + int(progress_ratio * 40)  # 15% - 55%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )
                
                task_manager.update_task(
                    task_id,
                    message=f"추가 시작 {total_chunks} 개의 텍스트 청크...",
                    progress=15
                )
                
                chunk_refs = builder.add_text_batches(
                    graph_id, 
                    chunks,
                    batch_size=3,
                    progress_callback=add_progress_callback
                )
                
                # Neo4j 쓰기는 동기적으로 완료되지만, 여기서는 진행률 표시를 위한 호환성 단계를 유지합니다
                task_manager.update_task(
                    task_id,
                    message="그래프 데이터 저장소에 저장 대기 중...",
                    progress=55
                )
                
                def wait_progress_callback(msg, progress_ratio):
                    progress = 55 + int(progress_ratio * 35)  # 55% - 90%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )
                
                builder._wait_for_episodes(chunk_refs, wait_progress_callback)

                # 그래프 데이터 가져오기
                task_manager.update_task(
                    task_id,
                    message="그래프 데이터 가져오는 중...",
                    progress=95
                )
                graph_data = builder.get_graph_data(graph_id)
                node_count = graph_data.get("node_count", 0)
                edge_count = graph_data.get("edge_count", 0)

                if node_count == 0 and edge_count == 0:
                    raise ValueError(
                        "그래프에서 추출된 엔티티가 없습니다. "
                        "문서 본문 텍스트를 충분히 읽지 못했을 수 있습니다. "
                        "스캔본 PDF라면 OCR 가능한 파일인지 확인해주세요."
                    )

                # 프로젝트 상태 업데이트
                project.status = ProjectStatus.GRAPH_COMPLETED
                project.error = None
                ProjectManager.save_project(project)

                build_logger.info(f"[{task_id}] 그래프 구축 완료: graph_id={graph_id}, 노드={node_count}, 엣지={edge_count}")
                
                # 완료
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    message="그래프 구축 완료",
                    progress=100,
                    result={
                        "project_id": project_id,
                        "graph_id": graph_id,
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "chunk_count": total_chunks,
                        "stats_delayed": False
                    }
                )
                
            except Exception as e:
                # 프로젝트 상태를 실패로 업데이트
                build_logger.error(f"[{task_id}] 그래프 구축 실패: {str(e)}")
                build_logger.debug(traceback.format_exc())
                
                project.status = ProjectStatus.FAILED
                project.error = str(e)
                ProjectManager.save_project(project)
                
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message=f"구축 실패: {str(e)}",
                    error=traceback.format_exc()
                )
        
        # 백그라운드 스레드 시작
        thread = threading.Thread(target=build_task, daemon=True)
        thread.start()
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "task_id": task_id,
                "message": "그래프 구축 작업이 시작되었습니다. /task/{task_id}를 통해 진행 상황을 조회해주세요"
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


# ============== 작업 조회 인터페이스 ==============

@graph_bp.route('/task/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """
    작업 상태 조회
    """
    task = TaskManager().get_task(task_id)
    
    if not task:
        return jsonify({
            "success": False,
            "error": f"작업이 존재하지 않습니다: {task_id}"
        }), 404
    
    return jsonify({
        "success": True,
        "data": task.to_dict()
    })


@graph_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """
    모든 작업 나열
    """
    tasks = TaskManager().list_tasks()
    
    return jsonify({
        "success": True,
        "data": tasks,
        "count": len(tasks)
    })


# ============== 그래프 데이터 인터페이스 ==============

@graph_bp.route('/data/<graph_id>', methods=['GET'])
def get_graph_data(graph_id: str):
    """
    그래프 데이터 가져오기 (노드 및 엣지)
    """
    try:
        if Config.validate_graph_backend():
            return jsonify({
                "success": False,
                "error": "; ".join(Config.validate_graph_backend())
            }), 500
        
        builder = GraphBuilderService()
        graph_data = builder.get_graph_data(graph_id)
        
        return jsonify({
            "success": True,
            "data": graph_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500


@graph_bp.route('/delete/<graph_id>', methods=['DELETE'])
def delete_graph(graph_id: str):
    """
    로컬 그래프 삭제
    """
    try:
        if Config.validate_graph_backend():
            return jsonify({
                "success": False,
                "error": "; ".join(Config.validate_graph_backend())
            }), 500
        
        builder = GraphBuilderService()
        builder.delete_graph(graph_id)
        
        return jsonify({
            "success": True,
            "message": f"그래프가 삭제되었습니다: {graph_id}"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            **error_traceback_payload()
        }), 500
