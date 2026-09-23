from __future__ import annotations

from pydantic import ValidationError

from app.agents.llm_client import LLMClient
from app.core.enums import Department, Priority
from app.core.logging import logger
from app.schemas.agent import FeedbackAnalysis


class FeedbackClassifier:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def analyze(self, text: str) -> FeedbackAnalysis:
        payload = self.llm_client.analyze_feedback(text)
        try:
            analysis = FeedbackAnalysis.model_validate(payload)
            return analysis
        except ValidationError as exc:
            logger.warning(
                "llm_validation_failed", extra={"reason": str(exc), "text": text}
            )
            fallback = FeedbackAnalysis(
                summary="Service issue identified",
                category="Administration",
                issue_type="General Support",
                priority=Priority.MEDIUM,
                department=Department.ADMINISTRATION,
                confidence=0.65,
            )
            return fallback
