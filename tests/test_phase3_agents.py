from app.agents.classifier import FeedbackClassifier
from app.agents.llm_client import LLMClient
from app.core.enums import Department, Priority
from typing import cast


def test_phase3_local_fallback_classifies_academic_feedback():
    analysis = LLMClient(api_key=None).analyze_feedback(
        "My marks are missing from the student portal"
    )

    assert analysis["department"] == Department.ACADEMIC_AFFAIRS.value
    assert analysis["priority"] == Priority.HIGH.value
    assert analysis["issue_type"] == "Missing Marks"


def test_phase3_classifier_validates_injected_llm_result():
    class FakeLLMClient:
        def analyze_feedback(self, text: str) -> dict:
            assert text == "The login system is unavailable"
            return {
                "summary": "System login unavailable",
                "category": "IT",
                "issue_type": "System Access",
                "priority": "HIGH",
                "department": "IT",
                "confidence": 0.91,
            }

    analysis = FeedbackClassifier(llm_client=cast(LLMClient, FakeLLMClient())).analyze(
        "The login system is unavailable"
    )

    assert analysis.department == Department.IT
    assert analysis.priority == Priority.HIGH
    assert analysis.confidence == 0.91


def test_phase3_classifier_returns_safe_fallback_for_invalid_llm_result():
    class InvalidLLMClient:
        def analyze_feedback(self, text: str) -> dict:
            return {
                "summary": "",
                "category": "Unknown",
                "issue_type": "Unknown",
                "priority": "NOT_A_PRIORITY",
                "department": "NOT_A_DEPARTMENT",
                "confidence": 2.0,
            }

    analysis = FeedbackClassifier(
        llm_client=cast(LLMClient, InvalidLLMClient())
    ).analyze("bad data")

    assert analysis.department == Department.ADMINISTRATION
    assert analysis.priority == Priority.MEDIUM
    assert analysis.confidence == 0.65


def test_phase3_openrouter_response_is_parsed_without_network():
    import app.agents.llm_client as llm_module

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"summary":"Missing marks",'
                                '"category":"Academic",'
                                '"issue_type":"Missing Marks",'
                                '"priority":"HIGH",'
                                '"department":"Academic Affairs",'
                                '"confidence":0.98}'
                            )
                        }
                    }
                ]
            }

    original_post = llm_module.httpx.post
    llm_module.httpx.post = lambda *args, **kwargs: FakeResponse()
    try:
        result = LLMClient(api_key="test-key", model="test-model").analyze_feedback(
            "marks missing"
        )
    finally:
        llm_module.httpx.post = original_post

    assert result["department"] == "Academic Affairs"
    assert result["confidence"] == 0.98
