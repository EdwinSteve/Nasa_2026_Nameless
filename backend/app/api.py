from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_handler_errors
from app.modules.identidad.api.router import router as identidad_router
from app.modules.territorio.api.router import router as territorio_router
from app.modules.fincas.api.router import router as fincas_router

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="SURCO API",
        description="API REST de SURCO",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_handler_errors(app)

    # La UI corre en otro origen (Next.js en :3000): sin esto el navegador bloquea las llamadas.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origenes_lista,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(
        identidad_router,
        prefix="/api/v1",
    )
    app.include_router(territorio_router, prefix="/api/v1")
    app.include_router(fincas_router, prefix="/api/v1")

    @app.get(
        "/api/v1/health",
        tags=["System"],
        summary="Consultar estado de la API",
        response_description="Estado de disponibilidad de la API",
    )

    async def health():
        return {"status": "ok"}

    return app

app = create_app()