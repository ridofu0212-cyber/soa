from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Metadata riêng. Các bảng nghiệp vụ sẽ được khai báo tại file này."""
