from typing import Dict
from .base import BaseVectorService


class LearningVectorService(BaseVectorService):
    @staticmethod
    def default_scores() -> Dict[str, float]:
        return {
            "reflective_active": 0.0,  # -1.0 to +1.0
            "intuitive_sensory": 0.0,  # -1.0 to +1.0
            "verbal_visual": 0.0,  # -1.0 to +1.0
            "global_sequential": 0.0  # -1.0 to +1.0
        }

    @staticmethod
    def default_confidence() -> Dict[str, float]:
        return {k: 0.0 for k in [
            "reflective_active", "intuitive_sensory", "verbal_visual", "global_sequential"
        ]}


learning_vector = LearningVectorService()