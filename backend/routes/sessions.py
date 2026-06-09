import firebase_admin
from firebase_admin import firestore
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Any

router = APIRouter(prefix="/sessions")


class NewSessionRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)


def _get_firestore_client() -> firestore.Client:
    try:
        firebase_admin.get_app()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Admin is not initialized.",
        ) from exc
    return firestore.client()


@router.get("/ping")
def ping():
    return {"ok": True, "endpoint": "sessions"}


@router.get("/{user_id}")
def list_sessions(user_id: str) -> list[dict[str, Any]]:
    db = _get_firestore_client()
    sessions_ref = db.collection("sessions")
    try:
        # Avoid composite index requirement by fetching matching docs and sorting in Python
        docs = sessions_ref.where("user_id", "==", user_id).stream()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query sessions: {exc}",
        ) from exc
    out = []
    for d in docs:
        data = d.to_dict()
        out.append(
            {
                "id": d.id,
                "title": data.get("title"),
                "last_updated": data.get("last_updated"),
                "message_count": data.get("message_count", 0),
            }
        )

    # sort by last_updated descending in Python
    out.sort(key=lambda x: x.get("last_updated") or datetime(1970,1,1,tzinfo=timezone.utc), reverse=True)
    return out


@router.post("/new")
def create_session(payload: NewSessionRequest) -> dict[str, str]:
    db = _get_firestore_client()
    now = datetime.now(timezone.utc)
    try:
        doc_ref = db.collection("sessions").document()
        doc_ref.set(
            {
                "user_id": payload.user_id,
                "title": payload.title,
                "created_at": now,
                "last_updated": now,
                "message_count": 0,
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {exc}",
        ) from exc

    return {"session_id": doc_ref.id}


@router.get("/{session_id}/messages")
def get_session_messages(session_id: str) -> list[dict[str, Any]]:
    db = _get_firestore_client()
    try:
        msgs = (
            db.collection("sessions")
            .document(session_id)
            .collection("messages")
            .order_by("timestamp", direction=firestore.Query.ASCENDING)
            .stream()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {exc}",
        ) from exc

    out = []
    for m in msgs:
        d = m.to_dict()
        d["id"] = m.id
        out.append(d)
    return out


@router.delete("/{session_id}")
def delete_session(session_id: str) -> dict[str, str]:
    db = _get_firestore_client()
    session_ref = db.collection("sessions").document(session_id)
    try:
        # delete all messages
        msgs = session_ref.collection("messages").stream()
        batch = db.batch()
        for m in msgs:
            batch.delete(m.reference)
        batch.delete(session_ref)
        batch.commit()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {exc}",
        ) from exc

    return {"ok": "deleted"}
