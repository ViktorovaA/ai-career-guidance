from session import UserSession, Stage
from bot import evaluate_holland, evaluate_motivation, recommend
import json


class ConversationManager:
    def __init__(self):
        self.session = UserSession()

    def handle_message(self, message: str):
        stage = self.session.stage

        # 1. START → задаём первый вопрос
        if stage == Stage.START:
            self.session.next_stage()
            return "Привет! Давай определим твой профессиональный профиль. Расскажи немного о себе: что тебе нравится делать?"

        # 2. Пользователь описал себя → считаем RIASEC
        elif stage == Stage.RIASEC_EVAL:
            vector_json = evaluate_holland(message)
            self.session.riasec_vector = json.loads(vector_json)
            self.session.next_stage()
            return "Спасибо! Теперь расскажи, что мотивирует тебя в работе? Что тебя вдохновляет?"

        # 3. Пользователь описал мотивацию → считаем второй вектор
        elif stage == Stage.MOTIVATION_EVAL:
            vector_json = evaluate_motivation(message)
            self.session.motivation_vector = json.loads(vector_json)
            self.session.next_stage()

            # финальная рекомендация
            result = recommend(
                self.session.riasec_vector,
                self.session.motivation_vector,
            )
            return result

        # 4. Промежуточный этап — задаём вопросы
        elif stage == Stage.ASK_RIASEC:
            self.session.next_stage()
            return "Хорошо, расскажи подробно о своих интересах, о том, что нравится делать."

        elif stage == Stage.ASK_MOTIVATION:
            self.session.next_stage()
            return "Расскажи подробнее, что тебя мотивирует в учёбе или деятельности."

        else:
            return "Диалог завершён."
