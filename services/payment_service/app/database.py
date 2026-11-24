from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .config import database_url
from .models import Base

engine = create_engine(
    database_url(),
    pool_pre_ping=True,
    pool_timeout=3,
    connect_args={"connect_timeout": 3},
    hide_parameters=True,
)
SessionLocal = sessionmaker(bind=engine)


def initialize_database() -> None:
    """Chỉ khởi động khi kết nối được PostgreSQL của service. Phase 1 có 0 bảng."""
    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))
        Base.metadata.create_all(bind=connection)
