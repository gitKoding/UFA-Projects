from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from ..utils.logger import get_logger
from ..utils.config import get_setting
from ..validation.schemas import SearchResponse, StatusInfo

logger = get_logger()

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Unhandled error: %s", exc)
            status = StatusInfo(
                http_code=500,
                reason_code="INTERNAL_ERROR",
                reason_status="failure",
                reason_details="An unexpected error occurred.",
            )
            response = SearchResponse(
                stores_list=[],
                status_info=status,
                prompt_used=None,
                api_name=get_setting("app.api_name", "UFA - Budget Bite API"),
            )
            return JSONResponse(status_code=500, content=response.model_dump())
