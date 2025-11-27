import os
import logging
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import AskRequest, AskResponse
from services.assessment_service import assessment_service
from services.chat_service import chat_service
from storage.state_manager import state_manager
from prompts import RECOMMENDATIONS_PROMPT

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(debug=os.getenv("DEBUG", "false").lower() == "true")

# Добавляем CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def _format_vectors_for_prompt(all_vectors: dict) -> str:
    """Форматирует все векторы для передачи в промпт рекомендаций"""
    text_parts = []

    # RIASEC
    if "riasec" in all_vectors:
        riasec = all_vectors["riasec"]["scores"]
        text_parts.append("RIASEC профиль:")
        for key, value in riasec.items():
            text_parts.append(f"  {key}: {round(value, 3)}")
        text_parts.append("")

    # Skills
    if "skills" in all_vectors:
        skills = all_vectors["skills"]["scores"]
        skill_names = {
            "remember": "Помнить", "understand": "Понимать", "apply": "Применять",
            "analyze": "Анализировать", "evaluate": "Оценивать", "create": "Создавать"
        }
        text_parts.append("Когнитивные навыки (таксономия Блума):")
        for key, value in skills.items():
            text_parts.append(f"  {skill_names.get(key, key)}: {round(value, 3)}")
        text_parts.append("")

    # Values
    if "values" in all_vectors:
        values = all_vectors["values"]["scores"]
        value_names = {
            "self_direction": "Независимость", "stimulation": "Новизна",
            "hedonism": "Удовольствие", "achievement": "Достижение",
            "power": "Власть", "security": "Безопасность",
            "conformity": "Следование правилам", "tradition": "Традиции",
            "benevolence": "Забота о близких", "universalism": "Универсализм"
        }
        text_parts.append("Ценностные ориентации:")
        for key, value in values.items():
            text_parts.append(f"  {value_names.get(key, key)}: {round(value, 3)}")
        text_parts.append("")

    # Big5
    if "big5" in all_vectors:
        big5 = all_vectors["big5"]["scores"]
        trait_names = {
            "openness": "Открытость опыту", "conscientiousness": "Сознательность",
            "extraversion": "Экстраверсия", "agreeableness": "Доброжелательность",
            "neuroticism": "Эмоциональная стабильность"
        }
        text_parts.append("Личностные черты (Big Five):")
        for key, value in big5.items():
            text_parts.append(f"  {trait_names.get(key, key)}: {round(value, 3)}")
        text_parts.append("")

    # Learning
    if "learning" in all_vectors:
        learning = all_vectors["learning"]["scores"]
        style_names = {
            "reflective_active": "Рефлексивный-Активный",
            "intuitive_sensory": "Интуитивный-Сенсорный",
            "verbal_visual": "Вербальный-Визуальный",
            "global_sequential": "Глобальный-Последовательный"
        }
        text_parts.append("Стили обучения:")
        for key, value in learning.items():
            text_parts.append(f"  {style_names.get(key, key)}: {round(value, 3)}")
        text_parts.append("")

    return "\n".join(text_parts)


def _format_recommendations_response(recommendations_data: dict) -> str:
    """Форматирует рекомендации для отображения пользователю"""
    text_parts = ["🎉 Все диагностики завершены! На основе вашего профиля мы подготовили рекомендации.\n"]

    # Summary
    if "summary" in recommendations_data:
        text_parts.append(f"📋 Общее резюме:\n{recommendations_data['summary']}\n")

    # Professions
    if "professions" in recommendations_data and recommendations_data["professions"]:
        text_parts.append("💼 Рекомендуемые профессии:")
        for i, prof in enumerate(recommendations_data["professions"][:5], 1):  # Ограничиваем 5 профессиями
            text_parts.append(
                f"\n{i}. {prof.get('name', 'Неизвестно')} (соответствие: {prof.get('match_score', 0) * 100:.1f}%)")
            if prof.get('description'):
                text_parts.append(f"   {prof['description']}")
            if prof.get('reasons'):
                text_parts.append("   Почему подходит:")
                for reason in prof['reasons'][:3]:  # Ограничиваем 3 причинами
                    text_parts.append(f"   • {reason}")
        text_parts.append("")

    # University directions
    if "university_directions" in recommendations_data and recommendations_data["university_directions"]:
        text_parts.append("🎓 Рекомендуемые направления в вузах:")
        for i, direction in enumerate(recommendations_data["university_directions"][:5],
                                      1):  # Ограничиваем 5 направлениями
            text_parts.append(
                f"\n{i}. {direction.get('name', 'Неизвестно')} (соответствие: {direction.get('match_score', 0) * 100:.1f}%)")
            if direction.get('code'):
                text_parts.append(f"   Код: {direction['code']}")
            if direction.get('description'):
                text_parts.append(f"   {direction['description']}")
        text_parts.append("")

    text_parts.append("🌟 Спасибо за прохождение диагностики!")

    return "\n".join(text_parts)


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

    # Добавляем текущее сообщение пользователя в историю
    state_manager.add_to_conversation_history(user_id, assessment_type, "user", text)

    # Обрабатываем сообщение через сервис оценки (передаем историю)
    try:
        logger.info(f"[PROCESSING] user_id={user_id}, stage={assessment_type}, calling assessment_service")
        result = await assessment_service.process_assessment(
            user_text=text,
            assessment_type=assessment_type,
            current_state=state,
            conversation_history=conversation_history
        )

        new_state = result["state"]
        response_data = result["response_data"]

        # Логируем результат обработки
        logger.info(
            f"[PROCESSING RESULT] user_id={user_id}, stage={assessment_type}, finished={new_state.get('finished', False)}")

        # Добавляем ответ ассистента в историю
        state_manager.add_to_conversation_history(
            user_id, assessment_type, "assistant", response_data["next_question"]
        )

    except Exception as e:
        logger.error(f"[ERROR] user_id={user_id}, stage={assessment_type}, error={str(e)}", exc_info=True)
        return AskResponse(
            type="question",
            text="Произошла ошибка при обработке запроса. Пожалуйста, попробуйте еще раз.",
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
            # Все стадии завершены - генерируем рекомендации
            logger.info(f"[ALL STAGES COMPLETED] user_id={user_id}, generating recommendations")

            # Получаем все векторы пользователя
            all_vectors = {}
            for stage in ["riasec", "skills", "values", "big5", "learning"]:
                stage_state = state_manager.get_user_state(user_id, stage)
                if stage_state and "scores" in stage_state:
                    all_vectors[stage] = stage_state

            logger.debug(f"[RECOMMENDATIONS] user_id={user_id}, all_vectors_keys={list(all_vectors.keys())}")

            # Формируем текст с данными для промпта
            vectors_text = _format_vectors_for_prompt(all_vectors)
            logger.debug(f"[RECOMMENDATIONS] user_id={user_id}, vectors_text_length={len(vectors_text)}")

            # Генерируем рекомендации
            try:
                recommendations_data = chat_service.process_message(
                    RECOMMENDATIONS_PROMPT,
                    vectors_text,
                    conversation_history=None
                )
                logger.info(f"[RECOMMENDATIONS] user_id={user_id}, recommendations_generated=true")

                # Формируем текст ответа с рекомендациями
                response_text = _format_recommendations_response(recommendations_data)

                response = AskResponse(
                    type="finish",
                    text=response_text,
                    scores=None
                )
                logger.info(
                    f"[OUTGOING RESPONSE] user_id={user_id}, type=finish, all_stages_completed=true, recommendations_included=true")
                return response
            except Exception as e:
                logger.error(f"[RECOMMENDATIONS ERROR] user_id={user_id}, error={str(e)}", exc_info=True)
                # Если не удалось сгенерировать рекомендации, возвращаем обычное сообщение
                response = AskResponse(
                    type="finish",
                    text="🎉 Все диагностики завершены! Спасибо за прохождение!",
                    scores=None
                )
                logger.info(
                    f"[OUTGOING RESPONSE] user_id={user_id}, type=finish, all_stages_completed=true, recommendations_failed=true")
                return response
        else:
            # Стадия завершена, переходим на следующую
            logger.info(f"[STAGE TRANSITION] user_id={user_id}, from={assessment_type}, to={next_stage}")
            stage_names = {
                "riasec": "профессиональных интересов (RIASEC)",
                "skills": "когнитивных навыков",
                "values": "ценностей",
                "big5": "личности (Big Five)",
                "learning": "стилей обучения"
            }
            current_stage_name = stage_names.get(assessment_type, assessment_type)
            next_stage_name = stage_names.get(next_stage, next_stage)


            response = AskResponse(
                type="question",
                scores=new_state["scores"]  # scores передаем для прогресс-бара, но не показываем пользователю
            )
        logger.info(
            f"[OUTGOING RESPONSE] user_id={user_id}, type=question, stage_transition=true, new_stage={next_stage}")
        return response

    # Если стадия не завершена, возвращаем следующий вопрос
    response = AskResponse(
        type="question",
        text=response_data["next_question"],
        scores=new_state["scores"]
    )
    logger.info(f"[OUTGOING RESPONSE] user_id={user_id}, type=question, stage={assessment_type}, finished=false")
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