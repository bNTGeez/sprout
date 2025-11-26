"""Place SQLAlchemy models in this module."""

from .base import Base

__all__ = ["Base"]

# Example model (remove once you add real tables):
# class Goal(Base):
#     __tablename__ = "goals"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     ...
