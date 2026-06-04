"""FastAPI surface — docs/agent-workflow §6.

Tuỳ chọn: UI Streamlit có thể import agent.runner trực tiếp. API này dành cho
client tách rời (vd webapp JS) hoặc test bằng curl.

    uvicorn agent.api:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from agent import runner

app = FastAPI(title="Hevy AI Insight Agent")


class ChatIn(BaseModel):
    user_id: str
    conversation_id: str
    message: str


class ResumeIn(BaseModel):
    conversation_id: str
    approved: bool
    edits: dict | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
def chat(body: ChatIn) -> dict:
    """Trả JSON. status='awaiting_confirm' nghĩa là cần user xác nhận routine."""
    return runner.chat(body.user_id, body.conversation_id, body.message)


@app.post("/chat/resume")
def chat_resume(body: ResumeIn) -> dict:
    return runner.resume(body.conversation_id, body.approved, body.edits)
