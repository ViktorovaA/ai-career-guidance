from openai import OpenAI
from config import OPENAI_API_KEY, MODEL

client = OpenAI(api_key=OPENAI_API_KEY)


def ask_model(prompt: str):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]


def evaluate_holland(text: str):
    prompt = f"""
Определи личностный вектор RIASEC по тексту пользователя:
{text}

Формат ответа строго JSON:
{{
  "realistic": float,
  "investigative": float,
  "artistic": float,
  "social": float,
  "enterprising": float,
  "conventional": float,
  "confidence": float
}}
"""
    return ask_model(prompt)


def evaluate_motivation(text: str):
    prompt = f"""
Оцени мотивационный профиль человека по тексту:
{text}

Формат ответа (строго JSON):
{{
  "achievement": float,
  "stability": float,
  "creativity": float,
  "communication": float,
  "confidence": float
}}
"""
    return ask_model(prompt)


def recommend(riasec, motivation):
    prompt = f"""
На основе двух векторов дай профессиональные рекомендации:

RIASEC:
{riasec}

Motivation:
{motivation}

Ответ: список профессий + объяснение (JSON).
"""
    return ask_model(prompt)
