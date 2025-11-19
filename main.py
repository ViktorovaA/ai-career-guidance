from fastapi import FastAPI
from manager import ConversationManager

app = FastAPI()
manager = ConversationManager()


@app.post("/chat")
def chat(req: dict):
    msg = req.get("message", "")
    return {"reply": manager.handle_message(msg)}
