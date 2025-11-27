from pydantic import BaseModel
from typing import Dict, Optional, List

class AskRequest(BaseModel):
    user_id: str
    text: str

class ProfessionRecommendation(BaseModel):
    name: str
    description: str
    match_score: float
    reasons: List[str]

class UniversityDirection(BaseModel):
    name: str
    code: Optional[str] = None
    description: str
    match_score: float
    reasons: List[str]

class AskResponse(BaseModel):
    type: str  # "question" | "finish"
    text: str
    scores: Optional[Dict[str, float]] = None
    recommendations: Optional[Dict] = None  # {"professions": [...], "university_directions": [...], "summary": "..."}