"""Opus 4.6 adapter using the Anthropic Messages API."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from inference_atlas.llm.base import LLMAdapter
from inference_atlas.llm.schema import WorkloadSpec

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-opus-4-6"
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}

PARSE_SYSTEM_PROMPT = (
    "Extract workload fields from user text. Return only valid JSON object with keys: "
    "tokens_per_day (number), pattern (steady|business_hours|bursty), model_key (string), "
    "latency_requirement_ms (number or null)."
)


class Opus46Adapter(LLMAdapter):
    """Opus 4.6 adapter implementation."""

    provider_name = "opus_4_6"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_sec: int = 30,
        max_retries: int = 2,
        backoff_base_sec: float = 0.5,
    ) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries
        self.backoff_base_sec = backoff_base_sec
        if self.timeout_sec <= 0:
            raise ValueError("timeout_sec must be > 0.")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0.")
        if self.backoff_base_sec < 0:
            raise ValueError("backoff_base_sec must be >= 0.")

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured.")

    def _generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """Send a prompt to the Anthropic Messages API and return text output."""
        self._ensure_api_key()
        body = {
            "model": self.model,
            "max_tokens": 500,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        request = Request(
            ANTHROPIC_API_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        payload: dict[str, Any]
        for attempt in range(self.max_retries + 1):
            try:
                with urlopen(request, timeout=self.timeout_sec) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as exc:
                status_code = getattr(exc, "code", None)
                is_retryable = status_code in RETRYABLE_STATUS_CODES
                if is_retryable and attempt < self.max_retries:
                    time.sleep(self.backoff_base_sec * (2**attempt))
                    continue
                raise RuntimeError(
                    f"Anthropic request failed with status {status_code}."
                ) from exc
            except URLError as exc:
                if attempt < self.max_retries:
                    time.sleep(self.backoff_base_sec * (2**attempt))
                    continue
                raise RuntimeError("Anthropic connection failed.") from exc

        content = payload.get("content", [])
        for item in content:
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
        raise RuntimeError("Anthropic response did not contain text output.")

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any]:
        """Extract a JSON object from model output text."""
        candidate = text.strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = candidate.find("{")
        end = candidate.rfind("}")
        if start >= 0 and end > start:
            snippet = candidate[start : end + 1]
            parsed = json.loads(snippet)
            if isinstance(parsed, dict):
                return parsed
        raise RuntimeError("Opus parse response was not valid JSON object.")

    def parse_workload(self, user_text: str) -> dict[str, Any]:
        text = self._generate_text(PARSE_SYSTEM_PROMPT, user_text)
        return self._extract_json_object(text)

    def explain(self, recommendation_summary: str, workload: WorkloadSpec) -> str:
        prompt = (
            "Explain the deterministic recommendation in 4-6 concise bullet points. "
            "Do not fabricate metrics. Use these inputs and summary.\n\n"
            f"Workload: {workload}\n"
            f"Summary:\n{recommendation_summary}"
        )
        return self._generate_text(
            "You are an infra assistant. Keep explanations precise and grounded.", prompt
        )
