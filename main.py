import os
import logging
from fastapi import FastAPI
from dotenv import load_dotenv
from models.schemas import AskRequest, AskResponse
from services.assessment_service import assessment_service
from storage.state_manager import state_manager

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(debug=os.getenv("DEBUG", "false").lower() == "true")


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    user_id = request.user_id
    text = request.text

    # Определяем текущую стадию пользователя
    assessment_type = state_manager.get_current_stage(user_id)

    # Получаем состояние пользователя и историю диалога
    state = state_manager.get_user_state(user_id, assessment_type)
    conversation_history = state_manager.get_conversation_history(user_id, assessment_type)

    # Логируем входящий запрос
    logger.info(f"[INCOMING REQUEST] user_id={user_id}, stage={assessment_type}, text_length={len(text)}")
    logger.debug(f"[INCOMING REQUEST] user_id={user_id}, text='{text[:100]}...' (truncated)" if len(text) > 100 else f"[INCOMING REQUEST] user_id={user_id}, text='{text}'")
    logger.debug(f"[INCOMING REQUEST] user_id={user_id}, current_state={state}")
    logger.debug(f"[INCOMING REQUEST] user_id={user_id}, conversation_history_length={len(conversation_history)}")

    # Добавляем текущее сообщение пользователя в историю
    state_manager.add_to_conversation_history(user_id, assessment_type, "user", text)

    # Обрабатываем сообщение через сервис оценки (передаем историю)
    try:
        logger.info(f"[PROCESSING] user_id={user_id}, stage={assessment_type}, calling assessment_service")
        result = await assessment_service.process_assessment(
            user_text=text,
            assessment_type=assessment_type,
            current_state=state,
            conversation_history=conversation_history  # Передаем историю
        )

        new_state = result["state"]
        response_data = result["response_data"]

        # Логируем результат обработки
        logger.info(f"[PROCESSING RESULT] user_id={user_id}, stage={assessment_type}, finished={new_state.get('finished', False)}")
        logger.debug(f"[PROCESSING RESULT] user_id={user_id}, new_state={new_state}")
        logger.debug(f"[PROCESSING RESULT] user_id={user_id}, response_data keys={list(response_data.keys())}")
        logger.debug(f"[PROCESSING RESULT] user_id={user_id}, next_question='{response_data.get('next_question', '')[:100]}...' (truncated)" if len(response_data.get('next_question', '')) > 100 else f"[PROCESSING RESULT] user_id={user_id}, next_question='{response_data.get('next_question', '')}'")

        # Добавляем ответ ассистента в историю
        state_manager.add_to_conversation_history(
            user_id, assessment_type, "assistant", response_data["next_question"]
        )

    except Exception as e:
        logger.error(f"[ERROR] user_id={user_id}, stage={assessment_type}, error={str(e)}", exc_info=True)
        return AskResponse(
            type="question",
            text=f"Произошла ошибка при обработке запроса. Пожалуйста, попробуйте еще раз. {e}",
            scores=state["scores"]
        )

    # Сохраняем обновленное состояние
    state_manager.update_user_state(user_id, assessment_type, new_state)

    # Проверяем, завершена ли текущая стадия
    if new_state.get("finished", False):
        logger.info(f"[STAGE COMPLETED] user_id={user_id}, completed_stage={assessment_type}")
        # Переходим на следующую стадию
        next_stage = state_manager.move_to_next_stage(user_id)
        
        if next_stage is None:
            # Все стадии завершены
            logger.info(f"[ALL STAGES COMPLETED] user_id={user_id}")
            response = AskResponse(
                type="finish",
                text="Все диагностики завершены. Спасибо за прохождение!",
                scores=None
            )
            logger.info(f"[OUTGOING RESPONSE] user_id={user_id}, type=finish, all_stages_completed=true")
            return response
        else:
            # Стадия завершена, переходим на следующую
            logger.info(f"[STAGE TRANSITION] user_id={user_id}, from={assessment_type}, to={next_stage}")
            stage_names = {
                "riasec": "RIASEC",
                "skills": "когнитивных навыков",
                "values": "ценностей",
                "big5": "личности (Big Five)",
                "learning": "стилей обучения"
            }
            current_stage_name = stage_names.get(assessment_type, assessment_type)
            next_stage_name = stage_names.get(next_stage, next_stage)
            
            message = f"Диагностика {current_stage_name} завершена. Переходим к диагностике {next_stage_name}."
            
            # Формируем сообщение с результатами текущей стадии
            if assessment_type == "riasec":
                scores_text = "\n".join([f"{k}: {round(v, 3)}" for k, v in new_state["scores"].items()])
                message += f"\n\nВаш профиль RIASEC:\n{scores_text}"
            elif assessment_type == "skills":
                skill_names = {
                    "remember": "Помнить", "understand": "Понимать", "apply": "Применять",
                    "analyze": "Анализировать", "evaluate": "Оценивать", "create": "Создавать"
                }
                scores_text = "\n".join([f"{skill_names[k]}: {round(v, 3)}" for k, v in new_state["scores"].items()])
                message += f"\n\nВаш профиль когнитивных навыков:\n{scores_text}"
            elif assessment_type == "values":
                value_names = {
                    "self_direction": "Независимость", "stimulation": "Новизна",
                    "hedonism": "Удовольствие", "achievement": "Достижение",
                    "power": "Власть", "security": "Безопасность",
                    "conformity": "Следование правилам", "tradition": "Традиции",
                    "benevolence": "Забота о близких", "universalism": "Универсализм"
                }
                scores_text = "\n".join([f"{value_names[k]}: {round(v, 3)}" for k, v in new_state["scores"].items()])
                message += f"\n\nВаш профиль ценностей:\n{scores_text}"
            elif assessment_type == "big5":
                trait_names = {
                    "openness": "Открытость опыту", "conscientiousness": "Сознательность",
                    "extraversion": "Экстраверсия", "agreeableness": "Доброжелательность",
                    "neuroticism": "Эмоциональная стабильность"
                }
                scores_text = "\n".join([f"{trait_names[k]}: {round(v, 3)}" for k, v in new_state["scores"].items()])
                message += f"\n\nВаш профиль личности (Big Five):\n{scores_text}"
            elif assessment_type == "learning":
                style_names = {
                    "reflective_active": "Рефлексивный-Активный",
                    "intuitive_sensory": "Интуитивный-Сенсорный",
                    "verbal_visual": "Вербальный-Визуальный",
                    "global_sequential": "Глобальный-Последовательный"
                }
                scores_text = "\n".join([f"{style_names[k]}: {round(v, 3)}" for k, v in new_state["scores"].items()])
                message += f"\n\nВаш профиль стилей обучения:\n{scores_text}"
            
            response = AskResponse(
                type="question",
                text=message,
                scores=new_state["scores"]
            )
            logger.info(f"[OUTGOING RESPONSE] user_id={user_id}, type=question, stage_transition=true, new_stage={next_stage}")
            logger.debug(f"[OUTGOING RESPONSE] user_id={user_id}, response_text_length={len(message)}")
            return response

    # Если стадия не завершена, возвращаем следующий вопрос
    response = AskResponse(
        type="question",
        text=response_data["next_question"],
        scores=new_state["scores"]
    )
    logger.info(f"[OUTGOING RESPONSE] user_id={user_id}, type=question, stage={assessment_type}, finished=false")
    logger.debug(f"[OUTGOING RESPONSE] user_id={user_id}, response_text='{response_data['next_question'][:100]}...' (truncated)" if len(response_data['next_question']) > 100 else f"[OUTGOING RESPONSE] user_id={user_id}, response_text='{response_data['next_question']}'")
    logger.debug(f"[OUTGOING RESPONSE] user_id={user_id}, scores={new_state['scores']}")
    return response


@app.get("/user/{user_id}/history/{assessment_type}")
async def get_conversation_history(user_id: str, assessment_type: str):
    """Эндпоинт для отладки - посмотреть историю диалога"""
    history = state_manager.get_conversation_history(user_id, assessment_type)
    return {"user_id": user_id, "assessment_type": assessment_type, "history": history}

@app.get("/user/{user_id}/current_stage")
async def get_current_stage(user_id: str):
    """Эндпоинт для отладки - посмотреть текущую стадию пользователя"""
    current_stage = state_manager.get_current_stage(user_id)
    return {"user_id": user_id, "current_stage": current_stage}
