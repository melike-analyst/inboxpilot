from typing import Literal, Optional
from pydantic import BaseModel, Field

Category = Literal["billing", "technical", "sales", "complaint", "general"]
Priority = Literal["low", "medium", "high", "urgent"]
Sentiment = Literal["positive", "neutral", "negative"]


class InboundMessage(BaseModel):
    source: str = Field("web", description="web, email, telegram, form ...")
    sender: Optional[str] = None
    subject: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=5000)


class TriageResult(BaseModel):
    id: int
    category: Category
    priority: Priority
    sentiment: Sentiment
    summary: str
    suggested_reply: str
    kb_sources: list[str]
    provider: str  # "llm" or "rules"
    needs_alert: bool
