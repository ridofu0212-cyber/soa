import logging
import re
from time import monotonic
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.responses import Response

from .config import SERVICE_NAME

logger = logging.getLogger("uvicorn.error")
REQUEST_ID = re.compile(r"(?:[0-9a-fA-F]{32}|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})")
HTTP_ERRORS = {
    404: ("NOT_FOUND", "Không tìm thấy tài nguyên."),
    405: ("METHOD_NOT_ALLOWED", "Phương thức HTTP không phù hợp."),
    503: ("DATABASE_UNAVAILABLE", "Chưa kết nối được cơ sở dữ liệu."),
}


def error_response(request: Request, status: int, code: str, message: str) -> JSONResponse:
    body = {
        "error": {
            "code": code,
            "message": message,
            "details": {},
            "request_id": request.state.request_id,
        }
    }
    return JSONResponse(status_code=status, content=body)


def configure_http(app: FastAPI) -> None:
    """Dùng chung một mã để tra log và đọc lỗi của cùng request."""
    @app.middleware("http")
    async def trace_request(request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", "")
        if not REQUEST_ID.fullmatch(request_id):
            request_id = str(uuid4())
        request.state.request_id = request_id

        start = monotonic()
        try:
            response = await call_next(request)
        except Exception as exc:
            # Biên HTTP cuối cùng. Không ghi body, URL thô hay nội dung exception.
            logger.error("service=%s request_id=%s exception=%s",
                         SERVICE_NAME, request_id, type(exc).__name__)
            response = error_response(request, 500, "INTERNAL_ERROR", "Lỗi xử lý tại service.")

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Service-Name"] = SERVICE_NAME
        elapsed_ms = round((monotonic() - start) * 1000)
        logger.info("service=%s request_id=%s method=%s status=%s duration_ms=%s",
                    SERVICE_NAME, request_id, request.method, response.status_code, elapsed_ms)
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        code, message = HTTP_ERRORS.get(exc.status_code, ("HTTP_ERROR", "Yêu cầu gặp lỗi."))
        response = error_response(request, exc.status_code, code, message)
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Pydantic có thể giữ giá trị đầu vào trong lỗi, kể cả mật khẩu.
        return error_response(request, 422, "VALIDATION_ERROR", "Dữ liệu đầu vào không hợp lệ.")
