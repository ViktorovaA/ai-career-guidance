from services.vectors import riasec_vector, skills_vector, values_vector, big5_vector, learning_vector

# Порядок прохождения стадий
ASSESSMENT_STAGES = ["riasec", "skills", "values", "big5", "learning"]


class StateManager:
    def __init__(self):
        self.user_states = {}
        self.conversation_histories = {}
        self.current_stages = {}  # Хранит текущую стадию для каждого пользователя

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
        if user_id in self.current_stages:
            del self.current_stages[user_id]

    def get_current_stage(self, user_id: str) -> str:
        """Возвращает текущую стадию пользователя. Если стадии нет, возвращает первую."""
        if user_id not in self.current_stages:
            self.current_stages[user_id] = ASSESSMENT_STAGES[0]
        return self.current_stages[user_id]

    def move_to_next_stage(self, user_id: str) -> str | None:
        """Переходит на следующую стадию. Возвращает новую стадию или None, если все стадии завершены."""
        current = self.get_current_stage(user_id)
        current_index = ASSESSMENT_STAGES.index(current)
        
        if current_index < len(ASSESSMENT_STAGES) - 1:
            next_stage = ASSESSMENT_STAGES[current_index + 1]
            self.current_stages[user_id] = next_stage
            return next_stage
        return None

    def is_all_stages_completed(self, user_id: str) -> bool:
        """Проверяет, завершены ли все стадии."""
        current = self.get_current_stage(user_id)
        return current == ASSESSMENT_STAGES[-1] and self.get_user_state(user_id, current).get("finished", False)


state_manager = StateManager()