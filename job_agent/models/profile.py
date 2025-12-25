from pydantic import BaseModel, Field
from typing import List

class CompanyPrefs(BaseModel):
    preferred: List[str] = Field(default_factory=list)
    avoided: List[str] = Field(default_factory=list)

class Profile(BaseModel):
    name: str
    target_titles: List[str]
    preferred_locations: List[str]
    must_have_skills: List[str]
    nice_to_have_skills: List[str]
    domain_keywords: List[str]
    company_preferences: CompanyPrefs
    resume_summary: str = ""
    achievements: List[str] = []

class RootProfile(BaseModel):
    profile: Profile
