import os
from fastapi import FastAPI
from dotenv import load_dotenv

# Импорты из вашей структуры
from models.schemas import AskRequest, AskResponse
from services.assessment_service import assessment_service
from storage.state_manager import state_manager

load_dotenv()

app = FastAPI(debug=os.getenv("DEBUG", "false").lower() == "true")


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    user_id = request.user_id
    text = request.text
    assessment_type = "riasec"  # Используем RIASEC

    # Получаем состояние пользователя
    state = state_manager.get_user_state(user_id, assessment_type)

    # Обрабатываем сообщение через сервис оценки
    try:
        result = await assessment_service.process_assessment(
            user_text=text,
            assessment_type=assessment_type,
            current_state=state
        )

        new_state = result["state"]
        response_data = result["response_data"]

    except Exception as e:
        # Обработка ошибок
        return AskResponse(
            type="question",
            text="Произошла ошибка при обработке запроса. Пожалуйста, попробуйте еще раз.",
            scores=state["scores"]
        )

    # Сохраняем обновленное состояние
    state_manager.update_user_state(user_id, assessment_type, new_state)

    # Формируем ответ пользователю
    if new_state["finished"]:
        scores_text = "\n".join([f"{k}: {round(v, 3)}" for k, v in new_state["scores"].items()])
        return AskResponse(
            type="finish",
            text=f"Диагностика завершена. Ваш RIASEC-профиль:\n{scores_text}",
            scores=new_state["scores"]
        )
    else:
        return AskResponse(
            type="question",
            text=response_data["next_question"],
            scores=new_state["scores"]
        )


@app.get("/")
async def root():
    return {"message": "RIASEC Assessment API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/user/{user_id}/state")
async def get_user_state(user_id: str):
    """Эндпоинт для отладки - посмотреть состояние пользователя"""
    state = state_manager.get_user_state(user_id, "riasec")
    return {"user_id": user_id, "state": state}


@app.delete("/user/{user_id}")
async def reset_user_state(user_id: str):
    """Эндпоинт для сброса состояния пользователя"""
    state_manager.delete_user_state(user_id)
    return {"message": f"State for user {user_id} has been reset"}