from fastapi import APIRouter
from src.utils.config import get_setting

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": get_setting("app.name", "BudgetBitesAPI"),
        "version": get_setting("app.version", "1.0.0"),
    }
