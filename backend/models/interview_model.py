from pydantic import BaseModel, Field


class InterviewSession(BaseModel):
    role: str
    scenario: str
    transcript: list[str] = Field(default_factory=list)
