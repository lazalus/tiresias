"""
API 响应辅助工具
"""

import traceback
from flask import current_app


def error_traceback_payload() -> dict:
    """
    仅在显式开启时返回 traceback，避免默认泄露服务端内部信息。
    """
    if current_app and current_app.config.get('EXPOSE_TRACEBACKS', False):
        return {"traceback": traceback.format_exc()}
    return {}
