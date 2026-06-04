from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from ..base import Base


class User(Base):
    """A Hevy user. `id` is the stable handle the agent/UI pass around
    (e.g. "demo-user")."""

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
