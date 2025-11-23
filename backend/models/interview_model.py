from typing import List, Optional

from pydantic import BaseModel, Field


class InterviewSession(BaseModel):
    user_id: str
    domain: str
    experience: str
    questions: List[str] = Field(default_factory=list)
    answers: List[str] = Field(default_factory=list)
    behaviors: List[str] = Field(default_factory=list)
    resume_context: Optional[str] = None
    candidate_name: Optional[str] = None
    status: str = "active"
