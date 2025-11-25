from typing import Dict, Any
from prompts import RIASEC_PROMPT
from services.chat_service import chat_service
from .vectors.riasec import riasec_vector


class AssessmentService:
    def __init__(self):
        self.vector_services = {
            "riasec": (riasec_vector, RIASEC_PROMPT)
        }

    async def process_assessment(self, user_text: str, assessment_type: str, current_state: dict) -> Dict[str, Any]:
        if assessment_type not in self.vector_services:
            raise ValueError(f"Unknown assessment type: {assessment_type}")

        vector_service, prompt = self.vector_services[assessment_type]

        # Обрабатываем сообщение
        data = chat_service.process_message(prompt, user_text)

        # Обновляем состояние
        new_state = vector_service.update_state(current_state, data)

        return {
            "state": new_state,
            "response_data": data
        }


assessment_service = AssessmentService()