from services.vectors import riasec_vector


class StateManager:
    def __init__(self):
        self.user_states = {}  # user_id -> {"riasec": state}

    def get_user_state(self, user_id: str, assessment_type: str = "riasec"):

        if user_id not in self.user_states:
            self.user_states[user_id] = {}

        if assessment_type not in self.user_states[user_id]:
            if assessment_type == "riasec":

                self.user_states[user_id][assessment_type] = {
                    "scores": riasec_vector.default_scores(),
                    "confidence": riasec_vector.default_confidence(),
                    "finished": False
                }

                # далее добавляем остальные вектора

        return self.user_states[user_id][assessment_type]

    def update_user_state(self, user_id: str, assessment_type: str, state: dict):
        if user_id not in self.user_states:
            self.user_states[user_id] = {}
        self.user_states[user_id][assessment_type] = state


state_manager = StateManager()