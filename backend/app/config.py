"""
설정 관리
프로젝트 루트 디렉토리의 .env 파일에서 설정을 통합 로드
"""

import os
import secrets
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리의 .env 파일 로드
# 경로: Tiresias/.env (backend/app/config.py 기준)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    # 만약 루트 디렉토리에 .env 파일이 없으면, 환경 변수 로드를 시도합니다 (운영 환경용)
    load_dotenv(override=True)


def _get_bool_env(name: str, default: bool = False) -> bool:
    """부울 환경 변수를 읽습니다."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _get_int_env(name: str, default: int) -> int:
    """정수 환경 변수를 읽습니다."""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return default


class Config:
    """Flask 설정 클래스"""
    
    # Flask 설정
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DEBUG = _get_bool_env('FLASK_DEBUG', False)
    EXPOSE_TRACEBACKS = _get_bool_env('EXPOSE_TRACEBACKS', False)
    INTERNAL_API_KEY = os.environ.get('INTERNAL_API_KEY')
    CORS_ALLOWED_ORIGINS = os.environ.get(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173'
    )
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # JSON 설정 - ASCII 이스케이프 비활성화, 중국어 직접 표시 (\\uXXXX 형식이 아닌)
    JSON_AS_ASCII = False
    
    # LLM 설정 (OpenAI 형식으로 통합)
    LLM_API_KEY = os.environ.get('LLM_API_KEY') or os.environ.get('OPENAI_API_KEY')
    LLM_BASE_URL = (
        os.environ.get('LLM_BASE_URL')
        or os.environ.get('OPENAI_BASE_URL')
        or 'https://api.openai.com/v1'
    )
    LLM_MODEL_NAME = (
        os.environ.get('LLM_MODEL_NAME')
        or os.environ.get('OPENAI_MODEL_NAME')
        or 'gpt-4o-mini'
    )
    OPENAI_ADMIN_KEY = os.environ.get('OPENAI_ADMIN_KEY')
    
    # 그래프 백엔드 설정 (Neo4j)
    GRAPH_BACKEND = os.environ.get('GRAPH_BACKEND', 'neo4j').strip().lower()
    NEO4J_URI = os.environ.get('NEO4J_URI')
    NEO4J_USERNAME = os.environ.get('NEO4J_USERNAME', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')
    NEO4J_DATABASE = os.environ.get('NEO4J_DATABASE', 'neo4j')
    
    # 파일 업로드 설정
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown', 'csv'}
    
    # 텍스트 처리 설정
    DEFAULT_CHUNK_SIZE = 500  # 기본 청크 크기
    DEFAULT_CHUNK_OVERLAP = 50  # 기본 중첩 크기
    
    # OASIS 시뮬레이션 설정
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_MAX_ROUNDS = _get_int_env('OASIS_MAX_ROUNDS', 60)
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')
    
    # OASIS 플랫폼 사용 가능 액션 설정
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]
    
    # 리포트 에이전트 설정
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))
    SIMULATION_MEMORY_SUMMARY_WINDOW = int(os.environ.get('SIMULATION_MEMORY_SUMMARY_WINDOW', '12'))
    MEMORY_SUMMARY_ENABLED = _get_bool_env('MEMORY_SUMMARY_ENABLED', True)
    MEMORY_SUMMARY_USE_LLM = _get_bool_env('MEMORY_SUMMARY_USE_LLM', True)
    MEMORY_SUMMARY_BATCH_SIZE = int(os.environ.get('MEMORY_SUMMARY_BATCH_SIZE', '12'))
    MEMORY_SUMMARY_MAX_RECENT = int(os.environ.get('MEMORY_SUMMARY_MAX_RECENT', '12'))
    MEMORY_SUMMARY_SEARCH_LIMIT = int(os.environ.get('MEMORY_SUMMARY_SEARCH_LIMIT', '4'))

    # 서버 과부하 방지 설정
    CAPACITY_RETRY_AFTER_SECONDS = _get_int_env('CAPACITY_RETRY_AFTER_SECONDS', 60)
    MAX_CONCURRENT_HEAVY_JOBS = _get_int_env('MAX_CONCURRENT_HEAVY_JOBS', 2)
    MAX_CONCURRENT_PREPARES = _get_int_env('MAX_CONCURRENT_PREPARES', 1)
    MAX_CONCURRENT_GRAPH_BUILDS = _get_int_env('MAX_CONCURRENT_GRAPH_BUILDS', 1)
    MAX_CONCURRENT_REPORTS = _get_int_env('MAX_CONCURRENT_REPORTS', 1)
    MAX_CONCURRENT_RUNNING_SIMULATIONS = _get_int_env('MAX_CONCURRENT_RUNNING_SIMULATIONS', 1)
    MAX_CONCURRENT_SIMULATION_ENVS = _get_int_env('MAX_CONCURRENT_SIMULATION_ENVS', 2)
    SIMULATION_ENV_TTL_SECONDS = _get_int_env('SIMULATION_ENV_TTL_SECONDS', 600)
    GRAPH_EXTRACTION_MAX_WORKERS = _get_int_env('GRAPH_EXTRACTION_MAX_WORKERS', 1)
    LLM_MAX_RETRIES = _get_int_env('LLM_MAX_RETRIES', 5)
    
    @classmethod
    def validate(cls):
        """필수 설정 유효성 검사"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY가 설정되지 않았습니다")
        errors.extend(cls.validate_graph_backend())
        return errors

    @classmethod
    def validate_graph_backend(cls):
        """그래프 백엔드 설정 유효성 검사."""
        errors = []

        if cls.GRAPH_BACKEND != 'neo4j':
            errors.append(f"지원되지 않는 GRAPH_BACKEND: {cls.GRAPH_BACKEND}")
            return errors

        if not cls.NEO4J_URI:
            errors.append("NEO4J_URI가 설정되지 않았습니다")
        if not cls.NEO4J_USERNAME:
            errors.append("NEO4J_USERNAME이 설정되지 않았습니다")
        if not cls.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD가 설정되지 않았습니다")

        return errors
