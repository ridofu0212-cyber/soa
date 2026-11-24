from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import SERVICE_NAME
from .database import engine, initialize_database
from .dependencies import get_db
from .errors import configure_http
from .schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        initialize_database()
        yield
    finally:
        engine.dispose()


app = FastAPI(
    title=f"F168 {SERVICE_NAME.capitalize()} Service",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=f"/openapi/{SERVICE_NAME}.json",
    lifespan=lifespan,
)
configure_http(app)


@app.get(f"/docs/{SERVICE_NAME}", include_in_schema=False)
def swagger() -> HTMLResponse:
    """Gateway phục vụ các tệp Swagger từ bản build local để demo được offline."""
    return get_swagger_ui_html(
        openapi_url=f"/openapi/{SERVICE_NAME}.json",
        title=app.title,
        swagger_js_url="/swagger-assets/swagger-ui-bundle.js",
        swagger_css_url="/swagger-assets/swagger-ui.css",
        swagger_favicon_url="/favicon.svg",
    )


@app.get("/health", response_model=HealthResponse, include_in_schema=False)
@app.get(f"/health/{SERVICE_NAME}", response_model=HealthResponse, tags=["Foundation"])
def health(db: Session = Depends(get_db)) -> HealthResponse:
    """Chạy một truy vấn thật cho mỗi lần đo. SELECT 1 không sửa dữ liệu."""
    try:
        db.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503) from exc
    return HealthResponse(service=SERVICE_NAME, status="ok", database="ok")
