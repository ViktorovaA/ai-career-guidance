from typing import Dict, Any
from prompts import RIASEC_PROMPT, SKILLS_PROMPT, VALUES_PROMPT, BIG5_PROMPT, LEARNING_PROMPT
from services.chat_service import chat_service
from services.vectors import riasec_vector, skills_vector, values_vector, big5_vector, learning_vector


# сервис для
class AssessmentService:
    def __init__(self):
        self.vector_services = {
            "riasec": (riasec_vector, RIASEC_PROMPT),
            "skills": (skills_vector, SKILLS_PROMPT),
            "values": (values_vector, VALUES_PROMPT),
            "big5": (big5_vector, BIG5_PROMPT),
            "learning": (learning_vector, LEARNING_PROMPT)
        }

    async def process_assessment(self, user_text: str, assessment_type: str, current_state: dict, conversation_history: list = None) -> Dict[str, Any]:
        if assessment_type not in self.vector_services:
            raise ValueError(f"Unknown assessment type: {assessment_type}")

        vector_service, prompt = self.vector_services[assessment_type]

        # Обрабатываем сообщение с историей диалога
        data = chat_service.process_message(prompt, user_text, conversation_history)

        # Обновляем состояние
        new_state = vector_service.update_state(current_state, data)

        return {
            "state": new_state,
            "response_data": data
        }

assessment_service = AssessmentService()