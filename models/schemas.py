from pydantic import BaseModel
from typing import Dict, Optional

class AskRequest(BaseModel):
    user_id: str
    text: str

class AskResponse(BaseModel):
    type: str  # "question" | "finish"
    text: str
    scores: Optional[Dict[str, float]] = None