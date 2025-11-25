import os
from fastapi import FastAPI
from dotenv import load_dotenv
from models.schemas import AskRequest, AskResponse
from services.assessment_service import assessment_service
from storage.state_manager import state_manager

load_dotenv()

app = FastAPI(debug=os.getenv("DEBUG", "false").lower() == "true")


@app.post("/ask/{assessment_type}", response_model=AskResponse)
async def ask(assessment_type: str, request: AskRequest):
    user_id = request.user_id
    text = request.text

    # Получаем состояние пользователя и историю диалога
    state = state_manager.get_user_state(user_id, assessment_type)
    conversation_history = state_manager.get_conversation_history(user_id, assessment_type)

    # Добавляем текущее сообщение пользователя в историю
    state_manager.add_to_conversation_history(user_id, assessment_type, "user", text)

    # Обрабатываем сообщение через сервис оценки (передаем историю)
    try:
        result = await assessment_service.process_assessment(
            user_text=text,
            assessment_type=assessment_type,
            current_state=state,
            conversation_history=conversation_history  # Передаем историю
        )

        new_state = result["state"]
        response_data = result["response_data"]

        # Добавляем ответ ассистента в историю
        state_manager.add_to_conversation_history(
            user_id, assessment_type, "assistant", response_data["next_question"]
        )

    except Exception as e:
        return AskResponse(
            type="question",
            text="Произошла ошибка при обработке запроса. Пожалуйста, попробуйте еще раз.",
            scores=state["scores"]
        )

    # Сохраняем обновленное состояние
    state_manager.update_user_state(user_id, assessment_type, new_state)

    # Формируем ответ пользователю
    if new_state["finished"]:
        if assessment_type == "riasec":
            scores_text = "\n".join([f"{k}: {round(v, 3)}" for k, v in new_state["scores"].items()])
            message = f"Диагностика RIASEC завершена. Ваш профиль:\n{scores_text}"
        elif assessment_type == "skills":
            skill_names = {
                "remember": "Помнить",
                "understand": "Понимать",
                "apply": "Применять",
                "analyze": "Анализировать",
                "evaluate": "Оценивать",
                "create": "Создавать"
            }
            scores_text = "\n".join([f"{skill_names[k]}: {round(v, 3)}" for k, v in new_state["scores"].items()])
            message = f"Диагностика когнитивных навыков завершена. Ваш профиль:\n{scores_text}"
        else:
            message = "Диагностика завершена."

        return AskResponse(
            type="finish",
            text=message,
            scores=new_state["scores"]
        )
    else:
        return AskResponse(
            type="question",
            text=response_data["next_question"],
            scores=new_state["scores"]
        )


@app.get("/user/{user_id}/history/{assessment_type}")
async def get_conversation_history(user_id: str, assessment_type: str):
    """Эндпоинт для отладки - посмотреть историю диалога"""
    history = state_manager.get_conversation_history(user_id, assessment_type)
    return {"user_id": user_id, "assessment_type": assessment_type, "history": history}
