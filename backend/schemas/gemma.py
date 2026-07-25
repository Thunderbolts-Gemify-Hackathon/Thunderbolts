from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    historique: list[ChatMessage] = Field(default_factory=list)


class ToolCallTrace(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: Any


class ChatResponse(BaseModel):
    reponse: str
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)


class RemedeResponse(BaseModel):
    remede: str
    
class ChatVocalResponse(BaseModel):
    transcription: str
    reponse: str
