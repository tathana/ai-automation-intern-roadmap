from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Mode = Literal['normal', 'transient', 'timeout', 'invalid_json', 'hallucination']


class Transaction(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    event_id: str = Field(min_length=1, max_length=80)
    user_id: str = Field(min_length=1, max_length=80)
    amount_minor: int = Field(gt=0, le=100_000_000)
    currency: Literal['THB'] = 'THB'
    mode: Mode = 'normal'

    @field_validator('event_id', 'user_id')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('blank identifier')
        return value


class Resume(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    candidate_id: str = Field(min_length=1, max_length=80)
    document_text: str = Field(min_length=1, max_length=20_000)
    processing_version: Literal['v1'] = 'v1'
    job_version: str = Field(default='demo-v1', min_length=1, max_length=80)
    job_requirements: list[str] = Field(default_factory=lambda: ['Python', 'SQL'], min_length=1, max_length=20)
    mode: Mode = 'normal'

    @field_validator('candidate_id', 'document_text', 'job_version')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('blank input')
        return value

    @field_validator('job_requirements')
    @classmethod
    def valid_requirements(cls, values):
        if any(not v.strip() or len(v)>80 for v in values):
            raise ValueError('requirements must be nonblank skill names up to 80 characters')
        cleaned=[v.strip() for v in values]
        if len({v.casefold() for v in cleaned})!=len(cleaned):
            raise ValueError('duplicate requirement')
        return cleaned


class SkillClaim(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    skill: str = Field(min_length=1, max_length=80)
    quote: str = Field(min_length=1, max_length=20_000)


class ResumeOutput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    claims: list[SkillClaim] = Field(max_length=50)


class Decision(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    decision_id: str = Field(min_length=1, max_length=80)
    outcome: Literal['verified', 'needs_followup']
    note: str = Field(min_length=1, max_length=300)
