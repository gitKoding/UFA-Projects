from pathlib import Path
import sys

# Allow running this file directly (python src/server/app.py) by ensuring project root on sys.path
if __package__ is None or __package__ == "":  # executed as a script, not as a module
    project_root = Path(__file__).resolve().parents[2]  # .../BudgetBitesAPI
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.middleware.error_handler import ErrorHandlingMiddleware
from src.middleware.request_id import RequestIDMiddleware
from src.routes.search_route import router as search_router
from src.routes.health_route import router as health_router
from src.utils.config import load_config, get_setting
from src.utils.logger import get_logger

logger = get_logger()

def create_app() -> FastAPI:
    load_config()  # Ensure config is loaded early
    app = FastAPI(title="Budget Bites API", version="1.0.0")
    # Middlewares (order: request id -> CORS -> error handler)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_setting("cors.allow_origins", ["*"]),
        allow_credentials=bool(get_setting("cors.allow_credentials", False)),
        allow_methods=get_setting("cors.allow_methods", ["*"]),
        allow_headers=get_setting("cors.allow_headers", ["*"]),
        expose_headers=get_setting("cors.expose_headers", ["X-Request-ID"]),
        max_age=int(get_setting("cors.max_age_seconds", 600)),
    )
    app.add_middleware(ErrorHandlingMiddleware)
    app.include_router(search_router)
    app.include_router(health_router)
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    host = get_setting("app.host", "0.0.0.0")
    try:
        port = int(get_setting("app.port", 8080))
    except (ValueError, TypeError):
        port = 8080
    # For debugging in VS Code when launching this file directly,
    # avoid uvicorn's reload (which spawns a child process and can miss breakpoints).
    # Run the app object in a single process so breakpoints bind reliably.
    uvicorn.run(app, host=host, port=port, reload=False)
