from typing import Dict
from .base import BaseVectorService


class ValuesVectorService(BaseVectorService):
    @staticmethod
    def default_scores() -> Dict[str, float]:
        return {
            "self_direction": 0.0,
            "stimulation": 0.0,
            "hedonism": 0.0,
            "achievement": 0.0,
            "power": 0.0,
            "security": 0.0,
            "conformity": 0.0,
            "tradition": 0.0,
            "benevolence": 0.0,
            "universalism": 0.0
        }

    @staticmethod
    def default_confidence() -> Dict[str, float]:
        return {k: 0.0 for k in [
            "self_direction", "stimulation", "hedonism", "achievement", "power",
            "security", "conformity", "tradition", "benevolence", "universalism"
        ]}


values_vector = ValuesVectorService()