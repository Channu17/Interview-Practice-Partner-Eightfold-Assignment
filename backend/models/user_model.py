from typing import Optional

from pydantic import BaseModel


class UserRegistration(BaseModel):
    name: str
    resume_present: bool = False
    resume_url: Optional[str] = None
    domain: Optional[str] = None
    experience: Optional[str] = None
    resume_context: Optional[str] = None
