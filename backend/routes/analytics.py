import firebase_admin
from firebase_admin import firestore
from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta, timezone
from typing import Any

router = APIRouter(prefix="/analytics")


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
    return {"ok": True, "endpoint": "analytics"}


@router.get("/{user_id}")
def analytics_for_user(user_id: str) -> dict[str, Any]:
    db = _get_firestore_client()

    # Fetch sessions for the user
    sessions = db.collection("sessions").where("user_id", "==", user_id).stream()
    session_list = []
    for s in sessions:
        d = s.to_dict()
        session_list.append({"id": s.id, **d})

    total_sessions = len(session_list)

    total_messages = 0
    positive_feedback = 0
    negative_feedback = 0

    # messages per day for last 14 days (date string -> count)
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=13)
    counts = { (start_date + timedelta(days=i)).isoformat(): 0 for i in range(14) }

    # Iterate sessions and their messages
    for s in session_list:
        msgs = db.collection("sessions").document(s["id"]).collection("messages").stream()
        for m in msgs:
            md = m.to_dict()
            role = md.get("role")
            ts = md.get("timestamp")
            if role == "user":
                total_messages += 1
                # bucket by day if timestamp available
                if isinstance(ts, datetime):
                    dday = ts.date()
                    if start_date <= dday <= today:
                        counts[dday.isoformat()] += 1

            fb = md.get("feedback")
            if fb == "positive":
                positive_feedback += 1
            elif fb == "negative":
                negative_feedback += 1

    messages_per_day = [{"date": k, "count": counts[k]} for k in sorted(counts.keys())]
    avg_messages_per_session = (total_messages / total_sessions) if total_sessions > 0 else 0.0

    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "positive_feedback": positive_feedback,
        "negative_feedback": negative_feedback,
        "messages_per_day": messages_per_day,
        "avg_messages_per_session": avg_messages_per_session,
    }
