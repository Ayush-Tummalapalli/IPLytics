"""
IPLytics — AI Assistant API Route

Endpoints:
    POST /ai/ask  → Ask a natural language question about IPL
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.ai.gemini_service import ask_question

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


class QuestionRequest(BaseModel):
    """Request body for the AI question endpoint."""
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural language question about IPL",
        examples=["Who has scored the most runs in IPL history?"],
    )


class AnswerResponse(BaseModel):
    """Response body with the AI-generated answer."""
    question: str
    answer: str


@router.post("/ask", response_model=AnswerResponse)
def ask_ai(
    request: QuestionRequest,
    db: Session = Depends(get_db),
) -> AnswerResponse:
    """
    Ask a natural language question about IPL.

    The AI assistant fetches relevant data from the database,
    sends it to Google Gemini with context, and returns an
    intelligent, data-backed answer.

    Example questions:
    - "Who has the best batting average in IPL?"
    - "Compare V Kohli and RG Sharma"
    - "How does Mumbai Indians perform at Wankhede Stadium?"
    - "What is the highest score at Chinnaswamy?"
    """
    logger.info("AI question: %s", request.question)

    try:
        answer = ask_question(request.question, db)
        return AnswerResponse(question=request.question, answer=answer)

    except Exception as e:
        logger.error("AI endpoint error: %s", e)
        raise HTTPException(status_code=500, detail=f"AI service error: {e}")
