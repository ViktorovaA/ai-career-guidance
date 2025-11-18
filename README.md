после клонирования добавить файл ".env", в котором написать следующее

`OPENAI_API_KEY=вставить_сюда_токен_open_ai
MODEL=gpt-4.1
DEBUG=false`

запуск сервера в терминале из корня командой

`pip install uvicorn fastapi`

через postman можно проверить через запрос

`POST http://localhost:8000/ask`
