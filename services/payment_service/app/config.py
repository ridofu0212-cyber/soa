import os

from sqlalchemy import URL

SERVICE_NAME = "payment"


def database_url() -> URL:
    """Tách từng biến môi trường để mật khẩu có ký tự đặc biệt vẫn hợp lệ."""
    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
    )
