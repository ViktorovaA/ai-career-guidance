import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ChatService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )

    def process_message(self, system_prompt: str, user_text: str, conversation_history: list = None) -> dict:
        """Обрабатывает сообщение через DeepSeek API с учетом истории диалога"""
        try:
            # Формируем messages с историей
            messages = [{"role": "system", "content": system_prompt}]

            # Добавляем историю диалога, если есть
            if conversation_history:
                messages.extend(conversation_history)

            # Добавляем текущее сообщение пользователя
            messages.append({"role": "user", "content": user_text})

            completion = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages
            )

            gpt_result = completion.choices[0].message.content
            return json.loads(gpt_result)

        except Exception as e:
            raise Exception(f"Ошибка при обработке сообщения: {str(e)}")


chat_service = ChatService()