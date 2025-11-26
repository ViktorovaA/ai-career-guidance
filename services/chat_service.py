import os
import json
import re
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )

    def _extract_json(self, text: str) -> str:
        """Извлекает JSON из текста, убирая markdown блоки кода если есть"""
        if not text:
            raise ValueError("Пустой ответ от API")
        
        # Убираем пробелы в начале и конце
        text = text.strip()
        
        # Пытаемся найти JSON в markdown блоке кода (```json ... ``` или ``` ... ```)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            extracted = json_match.group(1).strip()
            logger.debug(f"[JSON EXTRACTION] Found JSON in markdown code block, length={len(extracted)}")
            return extracted
        
        # Пытаемся найти JSON объект напрямую (ищем сбалансированные фигурные скобки)
        # Начинаем с первой открывающей скобки
        start_idx = text.find('{')
        if start_idx != -1:
            # Ищем соответствующую закрывающую скобку
            brace_count = 0
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        extracted = text[start_idx:i+1]
                        logger.debug(f"[JSON EXTRACTION] Found JSON object directly, length={len(extracted)}")
                        return extracted
        
        # Если ничего не найдено, возвращаем весь текст (может быть это уже чистый JSON)
        logger.warning(f"[JSON EXTRACTION] No JSON pattern found, returning full text (length={len(text)})")
        return text

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

            logger.debug(f"[API REQUEST] messages_count={len(messages)}, user_text_length={len(user_text)}")
            logger.debug(f"[API REQUEST] system_prompt_length={len(system_prompt)}")

            completion = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages
            )

            gpt_result = completion.choices[0].message.content
            
            # Логируем сырой ответ от API
            logger.info(f"[API RESPONSE] response_length={len(gpt_result) if gpt_result else 0}")
            logger.debug(f"[API RESPONSE] raw_response='{gpt_result[:200]}...' (truncated)" if gpt_result and len(gpt_result) > 200 else f"[API RESPONSE] raw_response='{gpt_result}'")
            
            if not gpt_result:
                raise ValueError("Получен пустой ответ от API")
            
            # Извлекаем JSON из ответа
            json_text = self._extract_json(gpt_result)
            logger.debug(f"[API RESPONSE] extracted_json='{json_text[:200]}...' (truncated)" if len(json_text) > 200 else f"[API RESPONSE] extracted_json='{json_text}'")
            
            # Парсим JSON
            parsed_json = json.loads(json_text)
            logger.debug(f"[API RESPONSE] parsed_json keys={list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'not a dict'}")
            
            return parsed_json

        except json.JSONDecodeError as e:
            logger.error(f"[API ERROR] JSON decode error: {str(e)}")
            logger.error(f"[API ERROR] Failed to parse: '{gpt_result[:500] if gpt_result else 'None'}'")
            raise Exception(f"Ошибка при парсинге JSON ответа от API: {str(e)}")
        except Exception as e:
            logger.error(f"[API ERROR] Unexpected error: {str(e)}", exc_info=True)
            raise Exception(f"Ошибка при обработке сообщения: {str(e)}")


chat_service = ChatService()