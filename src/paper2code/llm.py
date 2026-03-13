from __future__ import annotations

import json
import threading
import time
from typing import Any

from openai import OpenAI
from openai import RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential

from paper2code.config import Settings


class GroqLLM:
    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise ValueError("PAPER2CODE_GROQ_API_KEY is required for LLM-backed stages.")
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self._request_lock = threading.Lock()
        self._last_request_timestamp = 0.0

    def _respect_rate_limit(self) -> None:
        with self._request_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_timestamp
            wait_for = self.settings.min_llm_request_interval_seconds - elapsed
            if wait_for > 0:
                time.sleep(wait_for)
            self._last_request_timestamp = time.monotonic()

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def complete_text(self, prompt: str, *, temperature: float = 0.0) -> str:
        self._respect_rate_limit()
        response = self.client.chat.completions.create(
            model=self.settings.text_model,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from text model")
        return content

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def complete_vision(self, *, base64_image: str, image_ext: str, prompt: str) -> str:
        self._respect_rate_limit()
        response = self.client.chat.completions.create(
            model=self.settings.vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_ext};base64,{base64_image}"
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from vision model")
        return content

    def complete_json_list(self, prompt: str) -> list[dict[str, Any]]:
        raw = self.complete_text(prompt)
        return json.loads(raw)

    @staticmethod
    def is_token_cap_error(exc: Exception) -> bool:
        if not isinstance(exc, RateLimitError):
            return False
        message = str(exc).lower()
        return "tokens per day" in message or "tpd" in message or "rate_limit_exceeded" in message
