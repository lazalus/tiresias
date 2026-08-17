"""
Tiresias Backend - Flask 애플리케이션 팩토리
"""

import os
import warnings

# multiprocessing resource_tracker 경고 억제 (transformers와 같은 서드파티 라이브러리에서 발생)
# 다른 모든 임포트 전에 설정해야 함
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request, jsonify
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask 애플리케이션 팩토리 함수"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # JSON 인코딩 설정: 중국어 직접 표시 보장 (\\uXXXX 형식이 아닌)
    # Flask >= 2.3은 app.json.ensure_ascii를 사용하고, 이전 버전은 JSON_AS_ASCII 설정을 사용
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # 로그 설정
    logger = setup_logger('tiresias')
    
    # reloader 자식 프로세스에서만 시작 정보 출력 (디버그 모드에서 두 번 출력되는 것을 방지)
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info("Tiresias Backend 시작 중...")
        logger.info("=" * 50)
    
    # CORS 활성화, 기본적으로 로컬 개발 주소만 허용; 허용하려면 CORS_ALLOWED_ORIGINS=*로 명시적으로 구성 가능
    cors_allowed_origins = app.config.get('CORS_ALLOWED_ORIGINS', '')
    if cors_allowed_origins.strip() == '*':
        cors_origins = '*'
    else:
        cors_origins = [origin.strip() for origin in cors_allowed_origins.split(',') if origin.strip()]
    CORS(app, resources={r"/api/*": {"origins": cors_origins or ["http://localhost:3000"]}})
    
    # 시뮬레이션 프로세스 정리 함수 등록 (서버 종료 시 모든 시뮬레이션 프로세스 종료 보장)
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("시뮬레이션 프로세스 정리 함수가 등록되었습니다")

    # 이전 프로세스에서 중단된 장시간 작업을 실패 상태로 정리합니다.
    from .services.runtime_recovery import recover_interrupted_runtime_state
    recover_interrupted_runtime_state()
    if should_log_startup:
        logger.info("중단된 그래프/보고서 작업 복구를 완료했습니다")
    
    # 요청 로그 미들웨어
    @app.before_request
    def log_request():
        logger = get_logger('tiresias.request')
        logger.debug(f"요청: {request.method} {request.path}")
        if app.config.get('DEBUG') and request.content_type and 'json' in request.content_type:
            logger.debug(f"요청 본문: {request.get_json(silent=True)}")

        internal_api_key = app.config.get('INTERNAL_API_KEY')
        if request.path.startswith('/api/') and internal_api_key:
            provided_key = request.headers.get('X-Internal-Key')
            if provided_key != internal_api_key:
                logger.warning(f"내부 접근 키가 없거나 유효하지 않습니다: {request.method} {request.path}")
                return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    @app.after_request
    def log_response(response):
        logger = get_logger('tiresias.request')
        logger.debug(f"응답: {response.status_code}")
        return response
    
    # 블루프린트 등록
    from .api import admin_bp, graph_bp, simulation_bp, report_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    
    # 상태 확인
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'Tiresias Backend'}
    
    if should_log_startup:
        logger.info("Tiresias Backend 시작 완료")
    
    return app
