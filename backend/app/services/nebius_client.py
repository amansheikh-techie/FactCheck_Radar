"""OpenAI-compatible client factory for switchable LLM providers (NVIDIA or Nebius)."""

from __future__ import annotations

import asyncio
import difflib
import json
import logging
from typing import TypeVar

from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from pydantic import BaseModel, ValidationError

from backend.app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _clean_json_str(text: str) -> str:
    """Robustly extract and clean JSON object from LLM response."""
    if not text:
        return "{}"
    cleaned = text.strip()
    # Strip code fences if present
    if "```json" in cleaned:
        parts = cleaned.split("```json", 1)[1].split("```", 1)
        cleaned = parts[0].strip()
    elif "```" in cleaned:
        parts = cleaned.split("```", 1)[1].split("```", 1)
        cleaned = parts[0].strip()

    # Extract outermost JSON object
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return cleaned.strip()


def _is_placeholder(val: str | None) -> bool:
    """Check if an environment variable value is unset or a placeholder."""
    if not val:
        return True
    s = val.strip().lower()
    return (
        s.startswith("your_")
        or s.startswith("your-")
        or "placeholder" in s
        or "<" in s
        or len(s) < 8
    )


class LLMClient:
    """OpenAI-compatible unified client for NVIDIA NIM and Nebius Token Factory."""

    def __init__(self) -> None:
        self.provider: str = (settings.llm_provider or "nvidia").strip().lower()
        if self.provider == "nebius":
            self.base_url: str = settings.nebius_base_url
            self.api_key: str = settings.nebius_api_key
            self._default_fast: str = settings.nebius_model_fast
            self._default_reasoning: str = settings.nebius_model_reasoning
            self._key_env_var: str = "NEBIUS_API_KEY"
            self._url_env_var: str = "NEBIUS_BASE_URL"
        else:
            self.provider = "nvidia"
            self.base_url = settings.nvidia_base_url
            self.api_key = settings.nvidia_api_key
            self._default_fast = settings.nvidia_model_fast
            self._default_reasoning = settings.nvidia_model_reasoning
            self._key_env_var: str = "NVIDIA_API_KEY"
            self._url_env_var: str = "NVIDIA_BASE_URL"

        self._client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key or "placeholder",
            timeout=float(settings.llm_request_timeout),
        )
        self._available_models: set[str] = set()
        self._nemotron_models: list[str] = []
        self._resolved_fast: str | None = None
        self._resolved_reasoning: str | None = None
        self.fast_fallback_triggered: bool = False
        self.reasoning_fallback_triggered: bool = False

    def validate_configuration(self) -> None:
        """Fail fast if the active provider's key, base URL, or model is missing/placeholder."""
        if _is_placeholder(self.api_key):
            raise RuntimeError(
                f"Active LLM provider is '{self.provider}', but {self._key_env_var} "
                f"is missing or still a placeholder. Please configure a valid key in .env or environment."
            )
        if not self.base_url or not self.base_url.startswith("http"):
            raise RuntimeError(
                f"Active LLM provider is '{self.provider}', but {self._url_env_var} "
                f"is missing or invalid ('{self.base_url}')."
            )
        fast_candidate = settings.model_fast or self._default_fast
        reasoning_candidate = settings.model_reasoning or self._default_reasoning
        if not fast_candidate or not reasoning_candidate:
            raise RuntimeError(
                f"Active LLM provider is '{self.provider}', but fast or reasoning model is not configured."
            )

    @property
    def has_api_key(self) -> bool:
        return not _is_placeholder(self.api_key)

    # ── Model discovery ──────────────────────────────────

    async def discover_models(self) -> None:
        """Call /v1/models for active provider, list Nemotron models, and pick valid IDs."""
        primary_fast = settings.model_fast or self._default_fast
        primary_reasoning = settings.model_reasoning or self._default_reasoning

        try:
            response = await asyncio.to_thread(self._client.models.list)
            self._available_models = {m.id for m in response.data}
            self._nemotron_models = sorted(
                [m_id for m_id in self._available_models if "nemotron" in m_id.lower()]
            )
            logger.info(
                "Discovered %d models on %s (%d Nemotron models): %s",
                len(self._available_models),
                self.provider,
                len(self._nemotron_models),
                self._nemotron_models,
            )
        except Exception as exc:
            logger.warning(
                "Could not list models from provider '%s' (%s): %s",
                self.provider, self.base_url, exc,
            )
            self._available_models = {primary_fast, primary_reasoning}
            self._nemotron_models = [primary_fast, primary_reasoning]

        self._resolved_fast = self._resolve_model(
            primary_fast, settings.model_fast_fallbacks, "fast"
        )
        self._resolved_reasoning = self._resolve_model(
            primary_reasoning, settings.model_reasoning_fallbacks, "reasoning"
        )

    def _resolve_model(self, desired: str, fallbacks: list[str], role: str) -> str:
        """Pick desired model if available; else fallbacks; else closest Nemotron model."""
        # 1. Exact match
        if desired in self._available_models:
            logger.info("Using %s model on %s: %s", role, self.provider, desired)
            return desired

        # 1b. Case-insensitive match
        for m in self._available_models:
            if m.lower() == desired.lower():
                logger.info(
                    "Matched %s model '%s' (casing: '%s') on %s",
                    role, desired, m, self.provider,
                )
                return m

        # 2. Check candidate fallbacks
        for fb in fallbacks:
            if fb in self._available_models:
                logger.warning(
                    "Configured %s model '%s' unavailable on %s — falling back to '%s'",
                    role, desired, self.provider, fb,
                )
                if role == "fast":
                    self.fast_fallback_triggered = True
                elif role == "reasoning":
                    self.reasoning_fallback_triggered = True
                return fb

        # 3. Find closest available Nemotron model
        if self._nemotron_models:
            closest = self._find_closest_nemotron(desired, role, self._nemotron_models)
            logger.warning(
                "Configured %s model '%s' not found on %s. Using closest Nemotron model: '%s'",
                role, desired, self.provider, closest,
            )
            if role == "fast":
                self.fast_fallback_triggered = True
            elif role == "reasoning":
                self.reasoning_fallback_triggered = True
            return closest

        logger.warning(
            "No Nemotron models found on %s; keeping desired model '%s'",
            self.provider, desired,
        )
        return desired

    def _find_closest_nemotron(self, target: str, role: str, nemotrons: list[str]) -> str:
        """Find the closest Nemotron model using role keywords and fuzzy match."""
        if role == "fast":
            keywords = ["lightning", "nano", "bolt", "30b", "51b", "70b"]
        else:
            keywords = ["ultra", "550b", "super", "340b", "reasoning"]

        for kw in keywords:
            for m in nemotrons:
                if kw in m.lower():
                    return m

        matches = difflib.get_close_matches(target, nemotrons, n=1, cutoff=0.0)
        if matches:
            return matches[0]
        return nemotrons[0]

    @property
    def fast_model(self) -> str:
        return self._resolved_fast or settings.model_fast or self._default_fast

    @property
    def reasoning_model(self) -> str:
        return self._resolved_reasoning or settings.model_reasoning or self._default_reasoning

    @property
    def models_used(self) -> dict[str, str]:
        return {
            "fast": self.fast_model,
            "reasoning": self.reasoning_model,
        }

    # ── Chat completion with JSON parsing ────────────────

    async def chat_json(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[T],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> T:
        """
        Send a chat completion request expecting JSON output.
        Parse with pydantic. Retry up to 2x on API errors with backoff.
        On malformed JSON/schema, do one in-band fix-prompt retry.
        """
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                return await self._chat_json_inner(
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    output_schema=output_schema,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except APITimeoutError as exc:
                last_exc = exc
                logger.error(
                    "LLM request timed out on %s (%s) after %.1fs: %s",
                    self.provider, model, settings.llm_request_timeout, exc,
                )
                raise RuntimeError(
                    f"Inference request to {self.provider.upper()} Nemotron timed out "
                    f"after {int(settings.llm_request_timeout)}s. The inference cluster is under high load. "
                    f"Please retry your fact-check in a few moments."
                ) from exc
            except (APIError, RateLimitError) as exc:
                last_exc = exc
                if attempt < 2:
                    delay = min(1.0 * (2 ** attempt), 10.0)
                    logger.warning(
                        "API error attempt %d/3 on %s (%s): %s — retrying in %.1fs",
                        attempt + 1, self.provider, model, exc, delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error("All 3 API attempts failed on %s (%s): %s", self.provider, model, exc)
        raise last_exc  # type: ignore[misc]

    async def _chat_json_inner(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[T],
        temperature: float,
        max_tokens: int,
    ) -> T:
        """Inner call: completion -> parse -> validate -> optional JSON-fix retry."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await asyncio.to_thread(
            self._client.chat.completions.create,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content or ""
        logger.debug("Raw LLM response (%s on %s): %.300s", model, self.provider, raw)

        try:
            parsed = json.loads(_clean_json_str(raw))
            return output_schema.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as first_err:
            logger.warning(
                "JSON parse/validation failed on first attempt (%s): %s — retrying with clean prompt",
                model, first_err,
            )
            # Re-prompt cleanly without sending corrupted assistant text
            retry_messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"{user_prompt}\n\n"
                        f"IMPORTANT: Output ONLY a single valid JSON object strictly matching the required schema. "
                        f"Do not include any preamble, markdown code blocks, or extra text."
                    ),
                },
            ]

            response2 = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=model,
                messages=retry_messages,
                temperature=0.1,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )

            raw2 = response2.choices[0].message.content or ""
            parsed2 = json.loads(_clean_json_str(raw2))
            return output_schema.model_validate(parsed2)


def get_llm_client() -> LLMClient:
    """Factory creating configured LLMClient singleton."""
    return LLMClient()


# Singleton instance and backwards-compatible aliases
nebius_client: LLMClient = get_llm_client()
llm_client: LLMClient = nebius_client
NebiusClient = LLMClient
