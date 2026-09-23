from __future__ import annotations

import json
from typing import Any

import httpx

from app.agents.prompts import FEEDBACK_ANALYSIS_PROMPT
from app.core.config import get_settings
from app.core.logging import logger


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.openrouter_model

    def analyze_feedback(self, text: str) -> dict[str, Any]:
        if not self.api_key:
            return self._fallback_analysis(text)

        try:
            response = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": FEEDBACK_ANALYSIS_PROMPT},
                        {"role": "user", "content": text},
                    ],
                    "temperature": 0.1,
                },
                timeout=15,
            )
            response.raise_for_status()
            content = response.json()
            message = (
                content.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            parsed = json.loads(message)
            if isinstance(parsed, dict):
                return parsed
        except (
            AttributeError,
            IndexError,
            KeyError,
            TypeError,
            ValueError,
            httpx.HTTPError,
        ) as exc:  # pragma: no cover - behavior is intentionally resilient
            logger.warning("llm_request_failed", extra={"error": str(exc)})

        return self._fallback_analysis(text)

    @staticmethod
    def _fallback_analysis(text: str) -> dict[str, Any]:
        lower = text.lower()
        if "marks" in lower or "grade" in lower or "portal" in lower:
            return {
                "summary": "Marks missing from portal",
                "category": "Academic",
                "issue_type": "Missing Marks",
                "priority": "HIGH",
                "department": "Academic Affairs",
                "confidence": 0.95,
            }
        if "wifi" in lower or "login" in lower or "system" in lower or "email" in lower:
            return {
                "summary": "IT system access issue",
                "category": "IT",
                "issue_type": "System Access",
                "priority": "HIGH",
                "department": "IT",
                "confidence": 0.9,
            }
        if (
            "room" in lower
            or "clean" in lower
            or "facility" in lower
            or "security" in lower
        ):
            return {
                "summary": "Facilities issue reported",
                "category": "Facilities",
                "issue_type": "Facility Problem",
                "priority": "MEDIUM",
                "department": "Facilities",
                "confidence": 0.8,
            }
        return {
            "summary": "General service issue",
            "category": "Administration",
            "issue_type": "Service Request",
            "priority": "MEDIUM",
            "department": "Administration",
            "confidence": 0.7,
        }
