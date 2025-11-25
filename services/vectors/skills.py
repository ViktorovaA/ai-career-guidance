from typing import Dict
from .base import BaseVectorService


class SkillsVectorService(BaseVectorService):
    @staticmethod
    def default_scores() -> Dict[str, float]:
        return {
            "remember": 0.0,
            "understand": 0.0,
            "apply": 0.0,
            "analyze": 0.0,
            "evaluate": 0.0,
            "create": 0.0
        }

    @staticmethod
    def default_confidence() -> Dict[str, float]:
        return {
            "remember": 0.0,
            "understand": 0.0,
            "apply": 0.0,
            "analyze": 0.0,
            "evaluate": 0.0,
            "create": 0.0
        }


skills_vector = SkillsVectorService()