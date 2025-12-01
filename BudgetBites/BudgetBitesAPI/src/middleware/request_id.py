from __future__ import annotations

import uuid
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..utils.logger import get_logger, set_request_id

logger = get_logger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        # Honor incoming request id header if present
        incoming = request.headers.get("X-Request-ID") or request.headers.get("x-request-id")
        request_id = incoming or str(uuid.uuid4())
        set_request_id(request_id)
        try:
            logger.info("Request start %s %s | request_id=%s", request.method, request.url.path, request_id)
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "Request end %s %s %s | request_id=%s",
                request.method,
                request.url.path,
                response.status_code,
                request_id,
            )
            return response
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Request failed %s %s | request_id=%s | error=%s", request.method, request.url.path, request_id, exc)
            raise
        finally:
            # Clear context to avoid leaking into background tasks
            set_request_id(None)
