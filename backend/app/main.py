from fastapi import FastAPI

from app.core.logging import setup_logging
from app.core.settings import settings
from app.api.routes import router

def create_app() -> FastAPI:
    setup_logging(settings.log_level)
    app = FastAPI(title="PGAGI Interview API")
    app.include_router(router)
    return app

app = create_app()