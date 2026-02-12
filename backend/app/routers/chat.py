"""Chat router — AI-powered recipe generation."""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas import ChatRequest, ChatResponse
from app.services import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """Send a message to the AI chef and receive a recipe response."""
    try:
        response = await llm_service.chat(body)
        return response
    except Exception as exc:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail=f"AI service error: {exc}")
