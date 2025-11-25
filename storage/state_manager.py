from services.vectors import riasec_vector, skills_vector, values_vector, big5_vector, learning_vector


class StateManager:
    def __init__(self):
        self.user_states = {}
        self.conversation_histories = {}

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
            elif assessment_type == "skills":
                self.user_states[user_id][assessment_type] = {
                    "scores": skills_vector.default_scores(),
                    "confidence": skills_vector.default_confidence(),
                    "finished": False
                }
            elif assessment_type == "values":
                self.user_states[user_id][assessment_type] = {
                    "scores": values_vector.default_scores(),
                    "confidence": values_vector.default_confidence(),
                    "finished": False
                }
            elif assessment_type == "big5":
                self.user_states[user_id][assessment_type] = {
                    "scores": big5_vector.default_scores(),
                    "confidence": big5_vector.default_confidence(),
                    "finished": False
                }
            elif assessment_type == "learning":
                self.user_states[user_id][assessment_type] = {
                    "scores": learning_vector.default_scores(),
                    "confidence": learning_vector.default_confidence(),
                    "finished": False
                }

        return self.user_states[user_id][assessment_type]

    def get_conversation_history(self, user_id: str, assessment_type: str):
        if user_id not in self.conversation_histories:
            self.conversation_histories[user_id] = {}

        if assessment_type not in self.conversation_histories[user_id]:
            self.conversation_histories[user_id][assessment_type] = []

        return self.conversation_histories[user_id][assessment_type]

    def add_to_conversation_history(self, user_id: str, assessment_type: str, role: str, content: str):
        if user_id not in self.conversation_histories:
            self.conversation_histories[user_id] = {}

        if assessment_type not in self.conversation_histories[user_id]:
            self.conversation_histories[user_id][assessment_type] = []

        self.conversation_histories[user_id][assessment_type].append({
            "role": role,
            "content": content
        })

    def update_user_state(self, user_id: str, assessment_type: str, state: dict):
        if user_id not in self.user_states:
            self.user_states[user_id] = {}
        self.user_states[user_id][assessment_type] = state

    def delete_user_state(self, user_id: str):
        if user_id in self.user_states:
            del self.user_states[user_id]
        if user_id in self.conversation_histories:
            del self.conversation_histories[user_id]


state_manager = StateManager()