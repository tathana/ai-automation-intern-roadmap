"""Three small task contracts and fixtures; these are not model-generated results."""
from typing import Literal
from pydantic import BaseModel, ConfigDict


class TicketLabel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    category: Literal["payment", "account", "other", "needs_review"]


class IncidentSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    summary: str
    confirmed_root_cause: str | None


FIXTURES = {
    "classification": {"input": "Cannot sign in", "expected": {"category": "account"}},
    "extraction": {"input": "Built a Python ETL project.", "expected_skill": "Python"},
    "summary": {"input": "Timeouts increased after deploy. Root cause is under investigation.",
                "expected": {"summary": "Timeouts increased after deploy; root cause remains unconfirmed.", "confirmed_root_cause": None}},
}


def validate_summary_for_fixture(payload):
    result = IncidentSummary.model_validate(payload)
    if result.confirmed_root_cause is not None:
        raise ValueError("Source does not confirm root cause")
    # A reviewer still has to judge whether free-text summary preserves meaning.
    return result
