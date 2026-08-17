"""
LLM 클라이언트 캡슐화
OpenAI 형식으로 통일하여 호출
"""

import json
import re
import time
from typing import Optional, Dict, Any, List
from openai import OpenAI, RateLimitError

from ..config import Config


class LLMClient:
    """LLM 클라이언트"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY가 구성되지 않았습니다")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    @staticmethod
    def _parse_retry_delay_seconds(error: Exception, attempt: int) -> float:
        message = str(error)
        ms_match = re.search(r"try again in\s+(\d+)ms", message, flags=re.IGNORECASE)
        if ms_match:
            return max(float(ms_match.group(1)) / 1000.0, 0.5)

        sec_match = re.search(r"try again in\s+(\d+(?:\.\d+)?)s", message, flags=re.IGNORECASE)
        if sec_match:
            return max(float(sec_match.group(1)), 0.5)

        return min(2 ** attempt, 8)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        채팅 요청 전송
        
        Args:
            messages: 메시지 목록
            temperature: 온도 매개변수
            max_tokens: 최대 토큰 수
            response_format: 응답 형식 (예: JSON 모드)
            
        Returns:
            모델 응답 텍스트
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        # GPT-5 시리즈는 max_completion_tokens를 사용하고, 이전 모델은 여전히 max_tokens를 사용합니다.
        if str(self.model).startswith("gpt-5"):
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens
        
        if response_format:
            kwargs["response_format"] = response_format
        
        last_error: Optional[Exception] = None
        for attempt in range(Config.LLM_MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                # 일부 모델(예: MiniMax M2.5)은 content에 <think> 사고 내용을 포함하므로 제거해야 합니다.
                content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
                return content
            except RateLimitError as error:
                last_error = error
                if attempt >= Config.LLM_MAX_RETRIES - 1:
                    break
                time.sleep(self._parse_retry_delay_seconds(error, attempt))

        if last_error is not None:
            raise last_error

        raise RuntimeError("LLM 응답을 가져오지 못했습니다")
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        채팅 요청을 보내고 JSON 반환
        
        Args:
            messages: 메시지 목록
            temperature: 온도 매개변수
            max_tokens: 최대 토큰 수
            
        Returns:
            파싱된 JSON 객체
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        # 마크다운 코드 블록 태그 정리
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"LLM이 반환한 JSON 형식이 유효하지 않습니다: {cleaned_response}")
