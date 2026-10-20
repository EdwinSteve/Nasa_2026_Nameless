import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorDominio(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


def register_handler_errors(app: FastAPI) -> None:

    @app.exception_handler(ErrorDominio)
    async def handle_domain_error(request: Request, exc: ErrorDominio) -> JSONResponse:
        logger.info("domain_error code=%s path=%s", exc.code, request.url.path)
        return JSONResponse(
            status_code=exc.http_status,
            content={"code": exc.code, "message": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
            request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        detalles = [
            {"field": ".".join(map(str, e["loc"])), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION",
                "message": "Los datos enviados no son válidos.",
                "details": detalles,
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error path=%s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "Ocurrió un error inesperado.",
            },
        )