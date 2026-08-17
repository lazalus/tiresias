"""
파일 구문 분석 도구
PDF, Markdown, TXT, CSV 파일의 텍스트 추출을 지원합니다.
"""

import os
import platform
import tempfile
from pathlib import Path
from typing import List

from .logger import get_logger


logger = get_logger("tiresias.file_parser")


def _read_text_with_fallback(file_path: str) -> str:
    """
    텍스트 파일을 읽고, UTF-8 실패 시 자동으로 인코딩을 감지합니다.
    
    다단계 대체 전략을 사용합니다:
    1. 먼저 UTF-8 디코딩을 시도합니다.
    2. charset_normalizer를 사용하여 인코딩을 감지합니다.
    3. chardet으로 대체하여 인코딩을 감지합니다.
    4. 최종적으로 UTF-8 + errors='replace'를 사용하여 처리합니다.
    
    Args:
        file_path: 파일 경로
        
    Returns:
        디코딩된 텍스트 내용
    """
    data = Path(file_path).read_bytes()
    
    # 먼저 UTF-8을 시도합니다.
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        pass
    
    # charset_normalizer를 사용하여 인코딩 감지를 시도합니다.
    encoding = None
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data).best()
        if best and best.encoding:
            encoding = best.encoding
    except Exception:
        pass
    
    # chardet으로 대체합니다.
    if not encoding:
        try:
            import chardet
            result = chardet.detect(data)
            encoding = result.get('encoding') if result else None
        except Exception:
            pass
    
    # 최종 처리: UTF-8 + replace 사용
    if not encoding:
        encoding = 'utf-8'
    
    return data.decode(encoding, errors='replace')


class FileParser:
    """파일 구문 분석기"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.md', '.markdown', '.txt', '.csv'}
    PDF_OCR_MIN_TEXT = 200
    PDF_OCR_TEXT_PER_PAGE = 80
    PDF_OCR_PAGE_TEXT_THRESHOLD = 40
    PDF_OCR_EMPTY_PAGE_RATIO = 0.6
    PDF_MIN_USABLE_TEXT = 120
    PDF_OCR_RENDER_ZOOM = 2.0
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """
        파일에서 텍스트 추출
        
        Args:
            file_path: 파일 경로
            
        Returns:
            추출된 텍스트 내용
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"지원되지 않는 파일 형식: {suffix}")
        
        if suffix == '.pdf':
            return cls._extract_from_pdf(file_path)
        elif suffix in {'.md', '.markdown'}:
            return cls._extract_from_md(file_path)
        elif suffix == '.txt':
            return cls._extract_from_txt(file_path)
        elif suffix == '.csv':
            return cls._extract_from_csv(file_path)
        
        raise ValueError(f"처리할 수 없는 파일 형식: {suffix}")
    
    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """PDF에서 텍스트 추출"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF 설치가 필요합니다: pip install PyMuPDF")

        page_texts: List[str] = []
        page_image_counts: List[int] = []

        with fitz.open(file_path) as doc:
            for page in doc:
                text = (page.get_text("text") or "").strip()
                page_texts.append(text)
                page_image_counts.append(len(page.get_images(full=True)))

            combined_text = "\n\n".join(text for text in page_texts if text).strip()

            if not FileParser._should_run_pdf_ocr(page_texts, page_image_counts):
                return combined_text

            logger.info(
                "PDF OCR 대체 경로 실행: file=%s, pages=%s, native_text=%s",
                file_path,
                len(page_texts),
                len(combined_text),
            )

            ocr_page_indexes = [
                page_index
                for page_index, (text, image_count) in enumerate(zip(page_texts, page_image_counts))
                if len(text) < FileParser.PDF_OCR_PAGE_TEXT_THRESHOLD or image_count > 0
            ]

            if not ocr_page_indexes:
                ocr_page_indexes = list(range(len(page_texts)))

            ocr_page_texts = FileParser._extract_pdf_text_with_ocr(doc, ocr_page_indexes)
            merged_texts = []

            for page_index, native_text in enumerate(page_texts):
                ocr_text = ocr_page_texts.get(page_index, "").strip()
                chosen_text = native_text if len(native_text) >= len(ocr_text) else ocr_text
                if chosen_text:
                    merged_texts.append(chosen_text)

            combined_text = "\n\n".join(merged_texts).strip()

        if len(combined_text) < FileParser.PDF_MIN_USABLE_TEXT:
            raise ValueError(
                "PDF에서 읽을 수 있는 텍스트가 거의 없습니다. "
                "스캔본 또는 이미지형 PDF일 수 있습니다. OCR이 적용됐지만 본문을 충분히 읽지 못했습니다. "
                "텍스트가 포함된 PDF나 해상도가 더 높은 파일을 업로드해주세요."
            )

        return combined_text

    @staticmethod
    def _should_run_pdf_ocr(page_texts: List[str], page_image_counts: List[int]) -> bool:
        """기본 텍스트 추출 결과가 빈약하면 OCR 대체 경로를 활성화합니다."""
        if not page_texts:
            return False

        page_count = len(page_texts)
        total_text_length = sum(len(text) for text in page_texts)
        empty_or_short_pages = sum(
            1 for text in page_texts if len(text) < FileParser.PDF_OCR_PAGE_TEXT_THRESHOLD
        )
        image_pages = sum(1 for image_count in page_image_counts if image_count > 0)
        minimum_expected_text = max(
            FileParser.PDF_OCR_MIN_TEXT,
            page_count * FileParser.PDF_OCR_TEXT_PER_PAGE,
        )

        return (
            total_text_length < minimum_expected_text
            and (
                empty_or_short_pages / page_count >= FileParser.PDF_OCR_EMPTY_PAGE_RATIO
                or image_pages / page_count >= FileParser.PDF_OCR_EMPTY_PAGE_RATIO
            )
        )

    @staticmethod
    def _extract_pdf_text_with_ocr(doc, page_indexes: List[int]) -> dict[int, str]:
        """텍스트가 거의 없는 PDF 페이지를 macOS OCR로 읽어옵니다."""
        if platform.system() != "Darwin":
            raise ValueError(
                "PDF에서 읽을 수 있는 텍스트가 거의 없습니다. "
                "현재 서버에서는 이미지형 PDF OCR을 지원하지 않습니다."
            )

        try:
            from ocrmac.ocrmac import text_from_image
        except ImportError as exc:
            raise ValueError(
                "PDF에서 읽을 수 있는 텍스트가 거의 없습니다. "
                "현재 서버에 이미지형 PDF OCR 구성이 없습니다."
            ) from exc

        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise ImportError("PyMuPDF 설치가 필요합니다: pip install PyMuPDF") from exc

        ocr_results: dict[int, str] = {}

        with tempfile.TemporaryDirectory(prefix="tiresias-pdf-ocr-") as temp_dir:
            for page_index in page_indexes:
                try:
                    page = doc.load_page(page_index)
                    image_path = os.path.join(temp_dir, f"page-{page_index + 1}.png")
                    pixmap = page.get_pixmap(
                        matrix=fitz.Matrix(FileParser.PDF_OCR_RENDER_ZOOM, FileParser.PDF_OCR_RENDER_ZOOM),
                        alpha=False,
                    )
                    pixmap.save(image_path)

                    raw_result = text_from_image(
                        image_path,
                        recognition_level="accurate",
                        language_preference=["ko-KR", "en-US"],
                        confidence_threshold=0.2,
                        detail=False,
                    ) or []

                    lines = []
                    for item in raw_result:
                        if isinstance(item, tuple):
                            text = str(item[0]).strip()
                        else:
                            text = str(item).strip()
                        if text:
                            lines.append(text)

                    ocr_results[page_index] = "\n".join(lines).strip()
                except Exception as page_error:
                    logger.warning(
                        "PDF OCR 페이지 처리 실패: file_page=%s, error=%s",
                        page_index + 1,
                        page_error,
                    )
                    ocr_results[page_index] = ""

        return ocr_results
    
    @staticmethod
    def _extract_from_md(file_path: str) -> str:
        """Markdown에서 텍스트 추출, 자동 인코딩 감지 지원"""
        return _read_text_with_fallback(file_path)
    
    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """TXT에서 텍스트 추출, 자동 인코딩 감지 지원"""
        return _read_text_with_fallback(file_path)

    @staticmethod
    def _extract_from_csv(file_path: str) -> str:
        """CSV에서 텍스트 추출, 헤더 및 행 내용 유지"""
        return _read_text_with_fallback(file_path)
    
    @classmethod
    def extract_from_multiple(cls, file_paths: List[str]) -> str:
        """
        여러 파일에서 텍스트 추출 및 병합
        
        Args:
            file_paths: 파일 경로 목록
            
        Returns:
            병합된 텍스트
        """
        all_texts = []
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                text = cls.extract_text(file_path)
                filename = Path(file_path).name
                all_texts.append(f"=== 문서 {i}: {filename} ===\n{text}")
            except Exception as e:
                all_texts.append(f"=== 문서 {i}: {file_path} (추출 실패: {str(e)}) ===")
        
        return "\n\n".join(all_texts)


def split_text_into_chunks(
    text: str, 
    chunk_size: int = 500, 
    overlap: int = 50
) -> List[str]:
    """
    텍스트를 작은 덩어리로 분할
    
    Args:
        text: 원본 텍스트
        chunk_size: 각 덩어리의 문자 수
        overlap: 중복 문자 수
        
    Returns:
        텍스트 덩어리 목록
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # 문장 경계에서 분할 시도
        if end < len(text):
            # 가장 가까운 문장 종료 문자 찾기
            for sep in ['.\n', '!\n', '?\n', '\n\n', '. ', '! ', '? ']:
                last_sep = text[start:end].rfind(sep)
                if last_sep != -1 and last_sep > chunk_size * 0.3:
                    end = start + last_sep + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # 다음 덩어리는 중복 위치에서 시작
        start = end - overlap if end < len(text) else len(text)
    
    return chunks
