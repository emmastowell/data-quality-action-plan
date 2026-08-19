from fastapi import Request
from fastapi.responses import JSONResponse
from psycopg.errors import UniqueViolation, ForeignKeyViolation


class AppError(Exception):
    def __init__(self, code, message, status, details=None):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details or {}


def not_found(resource: str) -> AppError:
    return AppError("not_found", f"{resource} not found", 404)


def install_handlers(app):
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}})

    @app.exception_handler(UniqueViolation)
    async def _unique(_: Request, exc: UniqueViolation):
        return JSONResponse(status_code=409,
            content={"error": {"code": "conflict", "message": "resource already exists", "details": {}}})

    @app.exception_handler(ForeignKeyViolation)
    async def _fk(_: Request, exc: ForeignKeyViolation):
        return JSONResponse(status_code=422,
            content={"error": {"code": "invalid_reference", "message": "referenced resource not found", "details": {}}})
