"""
견적 전 경량 사전분석 서비스

결제 전에 전체 그래프를 만들지 않고,
실제 업로드 파일을 짧게 읽어 문서 규모/복잡도/이해관계자 밀도를 추정합니다.
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.file_parser import FileParser
from ..utils.llm_client import LLMClient


PREANALYSIS_TEXT_BUDGET = 12000
PREANALYSIS_FILE_SAMPLE_LIMIT = 4
PREANALYSIS_SECTION_SAMPLE = 1200


@dataclass
class FileSummary:
    name: str
    file_type: str
    pages: int
    characters: int
    sample: str


class PreanalysisService:
    """실제 업로드 파일 기반 경량 사전분석."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def analyze_uploaded_files(
        self,
        uploaded_files: List[Any],
        requirement: str = "",
    ) -> Dict[str, Any]:
        file_summaries = self._summarize_files(uploaded_files)
        total_pages = sum(item.pages for item in file_summaries)
        total_characters = sum(item.characters for item in file_summaries)

        heuristic = self._build_heuristic_guess(file_summaries, requirement)
        llm_result = self._run_llm_preanalysis(file_summaries, requirement, heuristic)

        complexity = self._normalize_bucket(llm_result.get("complexity"), heuristic["complexity"])
        actor_density = self._normalize_bucket(llm_result.get("actor_density"), heuristic["actor_density"])
        recommended_plan_id = self._normalize_plan_id(
            llm_result.get("recommended_plan_id"),
            self._recommend_plan_from_signals(total_pages, complexity, actor_density),
        )

        return {
            "actual_pages": total_pages,
            "total_characters": total_characters,
            "file_count": len(file_summaries),
            "complexity": complexity,
            "actor_density": actor_density,
            "complexity_multiplier": self._complexity_multiplier(complexity),
            "actor_density_multiplier": self._actor_density_multiplier(actor_density),
            "recommended_plan_id": recommended_plan_id,
            "document_type": llm_result.get("document_type") or heuristic["document_type"],
            "rationale": (llm_result.get("rationale") or heuristic["rationale"]).strip(),
            "confidence": self._coerce_confidence(llm_result.get("confidence")),
            "files": [
                {
                    "name": item.name,
                    "file_type": item.file_type,
                    "pages": item.pages,
                    "characters": item.characters,
                }
                for item in file_summaries
            ],
        }

    def _summarize_files(self, uploaded_files: List[Any]) -> List[FileSummary]:
        summaries: List[FileSummary] = []
        for uploaded_file in uploaded_files[:PREANALYSIS_FILE_SAMPLE_LIMIT]:
            suffix = Path(uploaded_file.filename or "").suffix.lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".tmp") as temp_file:
                uploaded_file.save(temp_file.name)
                temp_path = temp_file.name

            try:
                text = FileParser.extract_text(temp_path)
                clean_text = self._clean_text(text)
                characters = len(clean_text)
                pages = self._estimate_pages(temp_path, suffix, clean_text)
                summaries.append(
                    FileSummary(
                        name=uploaded_file.filename or Path(temp_path).name,
                        file_type=suffix.lstrip(".") or "bin",
                        pages=max(1, pages),
                        characters=characters,
                        sample=self._build_text_sample(clean_text),
                    )
                )
            finally:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

        return summaries

    def _run_llm_preanalysis(
        self,
        file_summaries: List[FileSummary],
        requirement: str,
        heuristic: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not file_summaries:
            return {}

        payload = [
            {
                "name": item.name,
                "file_type": item.file_type,
                "pages": item.pages,
                "characters": item.characters,
                "sample": item.sample,
            }
            for item in file_summaries
        ]

        system_prompt = """당신은 결제 전 경량 견적 사전분석기입니다.
그래프를 실제로 만들지 않고, 업로드 문서 일부만 보고 문서 복잡도와 이해관계자 밀도를 추정합니다.

반드시 JSON만 반환하십시오.
필드:
- complexity: low | medium | high
- actor_density: low | medium | high
- recommended_plan_id: quick | standard | deep
- document_type: 문서 유형 한 줄
- rationale: 100자 이내 한국어 요약
- confidence: 0~1"""

        user_prompt = (
            f"분석 질문:\n{requirement or '(없음)'}\n\n"
            f"현재 휴리스틱 초안:\n{heuristic}\n\n"
            f"파일 요약 샘플:\n{payload}"
        )

        try:
            return self.llm.chat_json(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=320,
            )
        except Exception:
            return {}

    def _build_heuristic_guess(self, file_summaries: List[FileSummary], requirement: str) -> Dict[str, Any]:
        total_pages = sum(item.pages for item in file_summaries)
        total_characters = sum(item.characters for item in file_summaries)
        joined_sample = "\n".join(item.sample for item in file_summaries if item.sample)

        keyword_hits = 0
        density_keywords = [
            "정부", "국회", "지자체", "정당", "기업", "협회", "기관", "노조", "언론",
            "시장", "업계", "플랫폼", "브랜드", "규제", "투자", "정책", "여론", "선거",
        ]
        lower_joined = joined_sample.lower()
        for keyword in density_keywords:
            if keyword.lower() in lower_joined:
                keyword_hits += 1

        requirement_bonus = 1 if len((requirement or "").strip()) >= 20 else 0
        complexity_score = total_pages + keyword_hits * 4 + requirement_bonus * 6
        actor_score = keyword_hits + min(total_pages // 12, 5)

        complexity = "low"
        if complexity_score >= 90:
            complexity = "high"
        elif complexity_score >= 35:
            complexity = "medium"

        actor_density = "low"
        if actor_score >= 12:
            actor_density = "high"
        elif actor_score >= 6:
            actor_density = "medium"

        return {
            "complexity": complexity,
            "actor_density": actor_density,
            "document_type": self._guess_document_type(joined_sample),
            "rationale": f"총 {total_pages}페이지, 약 {total_characters}자 기준의 경량 사전분석 결과입니다.",
        }

    def _recommend_plan_from_signals(self, total_pages: int, complexity: str, actor_density: str) -> str:
        score = total_pages
        if complexity == "medium":
            score += 20
        elif complexity == "high":
            score += 45

        if actor_density == "medium":
            score += 12
        elif actor_density == "high":
            score += 25

        if score <= 24:
            return "quick"
        if score <= 95:
            return "standard"
        return "deep"

    @staticmethod
    def _complexity_multiplier(bucket: str) -> float:
        return {
            "low": 0.88,
            "medium": 1.0,
            "high": 1.15,
        }.get(bucket, 1.0)

    @staticmethod
    def _actor_density_multiplier(bucket: str) -> float:
        return {
            "low": 0.9,
            "medium": 1.0,
            "high": 1.18,
        }.get(bucket, 1.0)

    @staticmethod
    def _normalize_bucket(value: Any, fallback: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized in {"low", "medium", "high"}:
            return normalized
        return fallback

    @staticmethod
    def _normalize_plan_id(value: Any, fallback: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized in {"quick", "standard", "deep"}:
            return normalized
        return fallback

    @staticmethod
    def _coerce_confidence(value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.6
        return max(0.0, min(number, 1.0))

    @staticmethod
    def _guess_document_type(sample: str) -> str:
        if not sample.strip():
            return "일반 문서"
        checks = [
            ("정책 보고서", ["정책", "시행령", "법안", "정부", "위원회"]),
            ("시장 분석 자료", ["시장", "산업", "매출", "점유율", "경쟁사"]),
            ("여론·커뮤니케이션 자료", ["여론", "SNS", "커뮤니티", "이슈", "반응"]),
            ("사업 전략 문서", ["전략", "사업", "로드맵", "투자", "목표"]),
        ]
        lowered = sample.lower()
        for label, keywords in checks:
            if sum(1 for keyword in keywords if keyword.lower() in lowered) >= 2:
                return label
        return "일반 문서"

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    @classmethod
    def _build_text_sample(cls, text: str) -> str:
        if not text:
            return ""

        sections: List[str] = []
        length = len(text)
        head = text[:PREANALYSIS_SECTION_SAMPLE]
        sections.append(head)

        if length > PREANALYSIS_SECTION_SAMPLE * 2:
            middle_start = max((length // 2) - (PREANALYSIS_SECTION_SAMPLE // 2), 0)
            sections.append(text[middle_start:middle_start + PREANALYSIS_SECTION_SAMPLE])

        if length > PREANALYSIS_SECTION_SAMPLE * 3:
            sections.append(text[-PREANALYSIS_SECTION_SAMPLE:])

        merged = "\n...\n".join(section.strip() for section in sections if section.strip())
        return merged[:PREANALYSIS_TEXT_BUDGET]

    @staticmethod
    def _estimate_pages(file_path: str, suffix: str, clean_text: str) -> int:
        if suffix == ".pdf":
            try:
                import fitz
                with fitz.open(file_path) as doc:
                    return max(1, len(doc))
            except Exception:
                pass

        chars = len(clean_text)
        if suffix == ".csv":
            return max(1, chars // 2000 + 1)
        return max(1, chars // 1500 + 1)
