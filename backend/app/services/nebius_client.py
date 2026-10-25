"""OpenAI-compatible client for Nebius Token Factory with model validation and fallback."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TypeVar

from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from pydantic import BaseModel, ValidationError

from backend.app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _clean_json_str(text: str) -> str:
    """Strip markdown code fence blocks if returned by the LLM."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


class NebiusClient:
    """Wrapper around the OpenAI SDK pointing at Nebius Token Factory."""

    def __init__(self) -> None:
        if not settings.nebius_api_key:
            logger.warning("NEBIUS_API_KEY is not set — LLM calls will fail")

        self._client = OpenAI(
            base_url=settings.nebius_base_url,
            api_key=settings.nebius_api_key or "placeholder",
            timeout=60.0,
        )
        self._available_models: set[str] = set()
        self._resolved_fast: str | None = None
        self._resolved_reasoning: str | None = None
        self.fast_fallback_triggered: bool = False
        self.reasoning_fallback_triggered: bool = False

    # ── Model discovery ──────────────────────────────────

    async def discover_models(self) -> None:
        """Call /v1/models to discover which Nemotron models are available."""
        try:
            # Run sync SDK call in thread to avoid blocking the event loop
            response = await asyncio.to_thread(self._client.models.list)
            self._available_models = {m.id for m in response.data}
            logger.info("Available models on Token Factory: %s", self._available_models)
        except Exception as exc:
            logger.warning("Could not list models from Token Factory: %s", exc)
            # Assume configured models are available
            self._available_models = {settings.model_fast, settings.model_reasoning}

        self._resolved_fast = self._resolve_model(
            settings.model_fast, settings.model_fast_fallbacks, "fast"
        )
        self._resolved_reasoning = self._resolve_model(
            settings.model_reasoning, settings.model_reasoning_fallbacks, "reasoning"
        )

    def _resolve_model(self, primary: str, fallbacks: list[str], role: str) -> str | None:
        """Pick the first available model from [primary] + fallbacks."""
        candidates = [primary] + fallbacks
        for model_id in candidates:
            if model_id in self._available_models:
                if model_id != primary:
                    logger.warning(
                        "Primary %s model '%s' unavailable — falling back to '%s'",
                        role, primary, model_id,
                    )
                    if role == "fast":
                        self.fast_fallback_triggered = True
                    elif role == "reasoning":
                        self.reasoning_fallback_triggered = True
                else:
                    logger.info("Using %s model: %s", role, model_id)
                return model_id
        logger.error("No %s model available! Tried: %s", role, candidates)
        # Last resort: just try the primary anyway
        return primary

    @property
    def fast_model(self) -> str:
        return self._resolved_fast or settings.model_fast

    @property
    def reasoning_model(self) -> str:
        return self._resolved_reasoning or settings.model_reasoning

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
        for attempt in range(3):  # up to 3 attempts
            try:
                return await self._chat_json_inner(
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    output_schema=output_schema,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except (APIError, APITimeoutError, RateLimitError) as exc:
                last_exc = exc
                if attempt < 2:
                    delay = min(1.0 * (2 ** attempt), 10.0)
                    logger.warning(
                        "API error attempt %d/3: %s — retrying in %.1fs",
                        attempt + 1, exc, delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error("All 3 API attempts failed: %s", exc)
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
        """Inner call: completion → parse → validate → optional JSON-fix retry.
        
        Uses asyncio.to_thread to avoid blocking the event loop with
        the synchronous OpenAI SDK.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Offload blocking SDK call to a thread
        response = await asyncio.to_thread(
            self._client.chat.completions.create,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content or ""
        logger.debug("Raw LLM response (%s): %.300s", model, raw)

        try:
            parsed = json.loads(_clean_json_str(raw))
            return output_schema.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as first_err:
            logger.warning(
                "JSON parse/validation failed on first attempt: %s — retrying with fix prompt",
                first_err,
            )
            # One in-band retry with the error context appended
            fix_prompt = (
                f"Your previous JSON output was invalid.\n"
                f"Error: {first_err}\n"
                f"Original output: {raw[:1000]}\n\n"
                f"Please output ONLY valid JSON matching the required schema. "
                f"Do not include markdown code fences or any text outside the JSON object."
            )
            messages_retry = messages + [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": fix_prompt},
            ]

            response2 = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=model,
                messages=messages_retry,
                temperature=0.1,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )

            raw2 = response2.choices[0].message.content or ""
            parsed2 = json.loads(_clean_json_str(raw2))
            return output_schema.model_validate(parsed2)


# Singleton
nebius_client = NebiusClient()
