from fastapi import APIRouter

router = APIRouter(
    tags=["Identidad"],
)

@router.get(
    "/auth/status",
    summary="Consultar disponibilidad del módulo de autenticación",
)
async def estado_auth():
    return {
        "status": "available",
        "module": "identidad",
    }