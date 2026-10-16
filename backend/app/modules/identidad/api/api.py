from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import register_handler_errors
from app.modules.identidad.api.router import router as identidad_router

def create_app() -> FastAPI:
    get_settings()

    app = FastAPI(
        title="SURCO API",
        description="API REST de SURCO",
        version="1.0.0",
    )

    register_handler_errors(app)

    app.include_router(
        identidad_router,
        prefix="/api/v1",
    )

    @app.get(
        "/api/v1/salud",
        tags=["System"],
        summary="Consultar estado de la API",
        response_description="Estado de disponibilidad de la API",
    )

    async def health():
        return {"status": "ok"}

    return app

app = create_app()