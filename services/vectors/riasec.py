from typing import Dict


class RIASECVectorService:
    @staticmethod
    def default_scores() -> Dict[str, float]:
        return {k: 0.0 for k in "RIASEC"}

    @staticmethod
    def default_confidence() -> Dict[str, float]:
        return {k: 0.0 for k in "RIASEC"}

    @staticmethod
    def mix_vectors(old: Dict[str, float], new: Dict[str, float],
                    weight_old: float = 0.7, weight_new: float = 0.3) -> Dict[str, float]:
        return {
            k: old[k] * weight_old + new[k] * weight_new
            for k in old.keys()
        }

    def update_state(self, current_state: dict, gpt_response: dict) -> dict:
        new_scores = self.mix_vectors(current_state["scores"], gpt_response["scores"])
        new_conf = self.mix_vectors(current_state["confidence"], gpt_response["confidence"])

        return {
            "scores": new_scores,
            "confidence": new_conf,
            "finished": gpt_response["should_finish"]
        }


riasec_vector = RIASECVectorService()