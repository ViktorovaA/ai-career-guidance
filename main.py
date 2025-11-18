import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from prompts import SYSTEM_PROMPT

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------
# Хранилище состояния (вместо Redis)
# ---------------------------
user_states = {}  # user_id -> { scores, confidence, finished }


class AskRequest(BaseModel):
    user_id: str
    text: str


class AskResponse(BaseModel):
    type: str  # "question" | "finish"
    text: str
    scores: dict | None = None


def default_scores():
    return {k: 0.0 for k in "RIASEC"}


def default_confidence():
    return {k: 0.0 for k in "RIASEC"}


def mix_vectors(old, new, weight_old=0.7, weight_new=0.3):
    return {
        k: old[k] * weight_old + new[k] * weight_new
        for k in old.keys()
    }


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    user_id = request.user_id
    text = request.text

    # Инициализация состояния
    if user_id not in user_states:
        user_states[user_id] = {
            "scores": default_scores(),
            "confidence": default_confidence(),
            "finished": False
        }

    state = user_states[user_id]

    # ---------------------------
    # GPT — анализ ответа
    # ---------------------------
    completion = client.responses.create(
        model="gpt-4.1",   # можно заменить на gpt-4.1-mini
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": text
            }
        ],
        response_format={"type": "json_object"}
    )

    gpt_result = completion.output[0].content[0].text

    import json
    data = json.loads(gpt_result)

    # ---------------------------
    # Обновление векторов
    # ---------------------------
    new_scores = mix_vectors(state["scores"], data["scores"])
    new_conf = mix_vectors(state["confidence"], data["confidence"])

    state["scores"] = new_scores
    state["confidence"] = new_conf
    state["finished"] = data["should_finish"]

    # ---------------------------
    # Ответ пользователю
    # ---------------------------
    if state["finished"]:
        return AskResponse(
            type="finish",
            text="Диагностика завершена. Ваш RIASEC-профиль:\n" +
                 "\n".join([f"{k}: {round(v, 3)}" for k, v in new_scores.items()]),
            scores=new_scores
        )

    else:
        return AskResponse(
            type="question",
            text=data["next_question"],
            scores=new_scores
        )
