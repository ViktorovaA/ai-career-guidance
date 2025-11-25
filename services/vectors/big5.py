from typing import Dict
from .base import BaseVectorService


class Big5VectorService(BaseVectorService):
    @staticmethod
    def default_scores() -> Dict[str, float]:
        return {
            "openness": 0.0,
            "conscientiousness": 0.0,
            "extraversion": 0.0,
            "agreeableness": 0.0,
            "neuroticism": 0.0
        }

    @staticmethod
    def default_confidence() -> Dict[str, float]:
        return {k: 0.0 for k in [
            "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"
        ]}


big5_vector = Big5VectorService()