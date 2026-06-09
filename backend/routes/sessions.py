from fastapi import APIRouter

router = APIRouter(prefix="/sessions")


@router.get("/ping")
def ping():
    return {"ok": True, "endpoint": "sessions"}
