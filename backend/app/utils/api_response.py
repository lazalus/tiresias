"""
API 응답 도우미
"""

import traceback
from flask import current_app


def error_traceback_payload() -> dict:
    """
    명시적으로 활성화된 경우에만 트레이스백을 반환하며, 기본적으로 서버 내부 정보가 유출되는 것을 방지합니다.
    """
    if current_app and current_app.config.get('EXPOSE_TRACEBACKS', False):
        return {"traceback": traceback.format_exc()}
    return {}