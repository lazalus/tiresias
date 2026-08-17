"""
보고서 PDF 렌더링 서비스
Worker가 전달한 정제 보고서 문서를 공용 템플릿으로 PDF로 변환합니다.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict


class ReportPdfRenderer:
    """Node + Playwright 기반 PDF 렌더러"""

    @classmethod
    def _repo_root(cls) -> Path:
        return Path(__file__).resolve().parents[3]

    @classmethod
    def _script_path(cls) -> Path:
        return cls._repo_root() / "backend" / "scripts" / "render_report_pdf.mjs"

    @classmethod
    def _node_path(cls) -> str:
        configured = os.environ.get("NODE_BINARY")
        candidates = [
            configured,
            shutil.which("node"),
            "/opt/homebrew/bin/node",
            "/usr/local/bin/node",
            "/opt/local/bin/node",
        ]

        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return candidate

        raise RuntimeError("node 실행 파일을 찾을 수 없습니다. PDF 렌더러를 사용하려면 Node.js가 필요합니다.")

    @classmethod
    def _playwright_browsers_path(cls) -> Path:
        configured = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        if configured:
            return Path(configured).expanduser()
        return cls._repo_root() / ".playwright-browsers"

    @classmethod
    def render_pdf(cls, report_document: Dict[str, Any]) -> bytes:
        script_path = cls._script_path()
        if not script_path.exists():
            raise RuntimeError(f"PDF 렌더링 스크립트를 찾을 수 없습니다: {script_path}")

        node_path = cls._node_path()
        playwright_browsers_path = cls._playwright_browsers_path()
        playwright_browsers_path.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["PLAYWRIGHT_BROWSERS_PATH"] = str(playwright_browsers_path)
        env["PATH"] = f"{Path(node_path).parent}:{env.get('PATH', '')}".rstrip(":")

        with tempfile.TemporaryDirectory(prefix="tiresias-report-pdf-") as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_path = temp_dir_path / "report.json"
            output_path = temp_dir_path / "report.pdf"

            with input_path.open("w", encoding="utf-8") as file:
                json.dump(report_document, file, ensure_ascii=False)

            result = subprocess.run(
                [
                    node_path,
                    str(script_path),
                    str(input_path),
                    str(output_path),
                ],
                cwd=str(cls._repo_root()),
                capture_output=True,
                text=True,
                timeout=180,
                env=env,
            )

            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                stdout = (result.stdout or "").strip()
                detail = stderr or stdout or "알 수 없는 오류"
                raise RuntimeError(f"PDF 렌더링 실패: {detail}")

            if not output_path.exists():
                raise RuntimeError("PDF 렌더링은 완료되었지만 출력 파일이 생성되지 않았습니다.")

            return output_path.read_bytes()
