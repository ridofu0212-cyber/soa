from collections.abc import Iterator

from sqlalchemy.orm import Session

from .database import SessionLocal


def get_db() -> Iterator[Session]:
    """Mỗi request mượn một session. Khi ra khỏi with, trả kết nối về pool."""
    with SessionLocal() as session:
        yield session
