"""LLM client supporting Gemini Flash (free tier) with Groq/OpenRouter fallback, JSON validation, 1x retry, and disk caching."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Optional, Type, TypeVar

from dotenv import load_dotenv
import httpx
from pydantic import BaseModel, ValidationError

load_dotenv()

T = TypeVar("T", bound=BaseModel)

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "llm"

FORBIDDEN_MODELS = ("gemini-4-argon", "argon", "gpt-4-32k", "claude-3-opus")

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "google/gemini-2.0-flash-exp:free",
}

GEMINI_FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
]


def _get_secret(key: str, default: str = "") -> str:
    """Read secret from environment variables or Streamlit secrets (if running in Streamlit)."""
    val = os.environ.get(key, "").strip()
    if val:
        return val
    try:
        import streamlit as st

        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default


def _extract_json_string(raw_text: str) -> str:
    """Extract JSON object from raw LLM response text (strips markdown fences if present)."""
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1]
    return text


class LLMQuotaOrKeyError(RuntimeError):
    """Raised when no valid API key is configured or free-tier quota is exhausted."""


class LLMClient:
    """Pure-Python LLM client enforcing <= 8 calls per run, JSON schema validation, 1x retry, and disk cache."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_calls: int = 8,
        use_cache: bool = True,
        timeout: float = 35.0,
    ) -> None:
        self.provider = (
            provider or _get_secret("LLM_PROVIDER", "gemini")
        ).lower().strip()
        if self.provider not in DEFAULT_MODELS:
            self.provider = "gemini"

        self.model = (
            model or _get_secret("LLM_MODEL", DEFAULT_MODELS[self.provider])
        ).strip()

        if any(bad in self.model.lower() for bad in FORBIDDEN_MODELS):
            raise ValueError(
                f"Model '{self.model}' bị cấm sử dụng trong code sản phẩm theo quy tắc free-tier."
            )

        self.max_calls = max_calls
        self.calls_count = 0
        self.use_cache = use_cache
        self.timeout = timeout
        if self.use_cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def has_any_api_key(self) -> bool:
        """Check whether at least one supported LLM API key is configured (without exposing keys)."""
        return any(
            bool(_get_secret(k))
            for k in (
                "GEMINI_API_KEY",
                "GOOGLE_API_KEY",
                "GROQ_API_KEY",
                "OPENROUTER_API_KEY",
            )
        )

    def _cache_key(
        self, system_prompt: str, user_prompt: str, schema_name: str
    ) -> Path:
        payload = json.dumps(
            {
                "provider": self.provider,
                "model": self.model,
                "schema": schema_name,
                "system": system_prompt,
                "user": user_prompt,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{schema_name}_{digest[:24]}.json"

    def _call_gemini(self, system_prompt: str, user_prompt: str, model_name: str) -> str:
        api_key = _get_secret("GEMINI_API_KEY") or _get_secret("GOOGLE_API_KEY")
        if not api_key:
            raise LLMQuotaOrKeyError(
                "Thiếu GEMINI_API_KEY trong file .env hoặc Streamlit Secrets."
            )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, params={"key": api_key}, json=body)
            if resp.status_code == 429:
                raise LLMQuotaOrKeyError(
                    f"Gemini model '{model_name}' chạm giới hạn quota (HTTP 429)."
                )
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates") or []
            if not candidates:
                raise RuntimeError("Gemini trả về danh sách candidates rỗng.")
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)

    def _call_openai_compatible(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": model_name,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=body)
            if resp.status_code == 429:
                raise LLMQuotaOrKeyError(
                    f"Provider '{base_url}' chạm giới hạn quota (HTTP 429)."
                )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _raw_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Execute LLM API call with automatic free-tier fallback on 429/missing key."""
        if self.calls_count >= self.max_calls:
            raise RuntimeError(
                f"Đã chạm trần số lần gọi LLM tối đa ({self.max_calls} lần/câu hỏi)."
            )
        self.calls_count += 1

        errors: list[str] = []

        # 1. Try primary provider
        if self.provider == "gemini" and (
            _get_secret("GEMINI_API_KEY") or _get_secret("GOOGLE_API_KEY")
        ):
            models_to_try = [self.model] + [
                m for m in GEMINI_FALLBACK_MODELS if m != self.model
            ]
            for m in models_to_try:
                try:
                    return self._call_gemini(system_prompt, user_prompt, m)
                except Exception as exc:
                    errors.append(f"gemini/{m}: {type(exc).__name__}")
                    time.sleep(0.5)

        # 2. Try Groq fallback
        groq_key = _get_secret("GROQ_API_KEY")
        if groq_key:
            groq_model = (
                self.model
                if self.provider == "groq"
                else DEFAULT_MODELS["groq"]
            )
            try:
                return self._call_openai_compatible(
                    "https://api.groq.com/openai/v1",
                    groq_key,
                    groq_model,
                    system_prompt,
                    user_prompt,
                )
            except Exception as exc:
                errors.append(f"groq/{groq_model}: {type(exc).__name__}")

        # 3. Try OpenRouter fallback
        or_key = _get_secret("OPENROUTER_API_KEY")
        if or_key:
            or_model = (
                self.model
                if self.provider == "openrouter"
                else DEFAULT_MODELS["openrouter"]
            )
            try:
                return self._call_openai_compatible(
                    "https://openrouter.ai/api/v1",
                    or_key,
                    or_model,
                    system_prompt,
                    user_prompt,
                )
            except Exception as exc:
                errors.append(f"openrouter/{or_model}: {type(exc).__name__}")

        raise LLMQuotaOrKeyError(
            "Không thể gọi LLM (thiếu API key hoặc hết quota free-tier). "
            f"Chi tiết thử nghiệm: {', '.join(errors) if errors else 'Chưa cấu hình GEMINI_API_KEY / GROQ_API_KEY'}."
        )

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        step_name: str = "llm_step",
    ) -> T:
        """Call LLM and validate output against `response_model` with 1x automatic retry."""
        schema_json = json.dumps(
            response_model.model_json_schema(), ensure_ascii=False, indent=2
        )
        full_system = (
            f"{system_prompt.strip()}\n\n"
            "You MUST respond with a single valid JSON object matching this exact JSON Schema "
            "(do not wrap in markdown, do not add extra commentary):\n"
            f"{schema_json}"
        )

        cache_path = self._cache_key(full_system, user_prompt, response_model.__name__)
        if self.use_cache and cache_path.exists():
            try:
                cached_data = json.loads(cache_path.read_text(encoding="utf-8"))
                return response_model.model_validate(cached_data)
            except Exception:
                pass

        raw_text = self._raw_completion(full_system, user_prompt)
        json_str = _extract_json_string(raw_text)

        try:
            parsed = json.loads(json_str)
            validated = response_model.model_validate(parsed)
            if self.use_cache:
                cache_path.write_text(
                    json.dumps(validated.model_dump(), ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            return validated
        except (json.JSONDecodeError, ValidationError) as first_err:
            # Retry once as specified in BRIEF section 4.3 ("validate, retry 1 lần")
            if self.calls_count >= self.max_calls:
                raise RuntimeError(
                    f"Lỗi validate JSON ở bước '{step_name}' và đã hết quota số lần gọi LLM: {first_err}"
                ) from first_err

            retry_prompt = (
                f"{user_prompt}\n\n"
                "PREVIOUS OUTPUT FAILED VALIDATION WITH ERROR:\n"
                f"{first_err}\n"
                "Please fix the JSON and return ONLY a valid JSON object matching the required schema."
            )
            raw_retry = self._raw_completion(full_system, retry_prompt)
            json_retry_str = _extract_json_string(raw_retry)
            parsed_retry = json.loads(json_retry_str)
            validated_retry = response_model.model_validate(parsed_retry)
            if self.use_cache:
                cache_path.write_text(
                    json.dumps(validated_retry.model_dump(), ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            return validated_retry
