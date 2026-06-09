from fastapi import APIRouter

router = APIRouter(prefix="/analytics")


@router.get("/ping")
def ping():
    return {"ok": True, "endpoint": "analytics"}
