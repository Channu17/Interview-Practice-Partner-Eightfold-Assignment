from typing import List

from pydantic import BaseModel, Field


class InterviewSession(BaseModel):
    user_id: str
    domain: str
    experience: str
    questions: List[str] = Field(default_factory=list)
    answers: List[str] = Field(default_factory=list)
    status: str = "active"
