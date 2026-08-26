from __future__ import annotations

from pydantic import BaseModel


class ChatTurn(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    audit_id: str
    question: str
    history: list[ChatTurn] = []


class ChatResponse(BaseModel):
    answer: str


class AuditResponse(BaseModel):
    audit_id: str
    summary: dict
    subscriptions: list[dict]


class HealthResponse(BaseModel):
    status: str
    agent_configured: bool
