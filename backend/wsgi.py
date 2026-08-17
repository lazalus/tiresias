"""
Gunicorn WSGI 진입점
"""

from app import create_app
from app.config import Config


def create_validated_app():
    errors = Config.validate()
    if errors:
        raise RuntimeError("설정 오류: " + "; ".join(errors))
    return create_app()


app = create_validated_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=Config.DEBUG, threaded=True)
