from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ErrorDominio(Exception):

    def __init__(
            self,
            code: str,
            message: str,
            http_status: int = 400,
    ):
        super().__init__(message)

        self.code = code
        self.message = message
        self.http_status = http_status


def register_handler_errors(app: FastAPI) -> None:

    @app.exception_handler(ErrorDominio)
    async def management_error_domain(
            request: Request,
            exc: ErrorDominio,
    ) -> JSONResponse:

        return JSONResponse(
            status_code=exc.http_status,
            content={
                "code": exc.code,
                "message": exc.message,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def management_request_validation_error(
            request: Request,
            exc: RequestValidationError,
    ) -> JSONResponse:

        detalles = [
            {
                "field": ".".join(map(str, error["loc"])),
                "message": error["msg"],
            }
            for error in exc.errors()
        ]

        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION",
                "message": "Los datos enviados no son válidos.",
                "details": detalles,
            },
        )