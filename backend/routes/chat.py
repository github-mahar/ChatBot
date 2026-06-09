import os
from datetime import datetime, timezone
from typing import Any

import firebase_admin
import httpx
from fastapi import APIRouter, HTTPException, status
from firebase_admin import firestore
from pydantic import BaseModel, Field

router = APIRouter(prefix="/chat")


class ChatHistoryMessage(BaseModel):
    role: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class ChatMessageRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    history: list[ChatHistoryMessage] = Field(default_factory=list)


def _get_firestore_client() -> firestore.Client:
    try:
        firebase_admin.get_app()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Admin is not initialized.",
        ) from exc

    return firestore.client()


def _ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def _ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3")


@router.post("/message")
async def post_message(payload: ChatMessageRequest) -> dict[str, Any]:
    messages = [item.model_dump() for item in payload.history]
    messages.append({"role": "user", "content": payload.message})

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{_ollama_base_url()}/api/chat",
                json={
                    "model": _ollama_model(),
                    "messages": messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama is unreachable.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama returned an error: {exc.response.text}",
        ) from exc

    assistant_content = response.json().get("message", {}).get("content")
    if not assistant_content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama response did not contain message content.",
        )

    db = _get_firestore_client()
    session_ref = db.collection("sessions").document(payload.session_id)
    messages_ref = session_ref.collection("messages")
    now = datetime.now(timezone.utc)

    try:
        user_doc = messages_ref.document()
        assistant_doc = messages_ref.document()

        batch = db.batch()
        batch.set(
            user_doc,
            {
                "role": "user",
                "content": payload.message,
                "timestamp": now,
                "user_id": payload.user_id,
            },
        )
        batch.set(
            assistant_doc,
            {
                "role": "assistant",
                "content": assistant_content,
                "timestamp": now,
                "user_id": payload.user_id,
            },
        )
        batch.set(
            session_ref,
            {
                "user_id": payload.user_id,
                "last_updated": now,
                "message_count": firestore.Increment(2),
            },
            merge=True,
        )
        batch.commit()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist chat messages: {exc}",
        ) from exc

    return {
        "response": assistant_content,
        "session_id": payload.session_id,
    }