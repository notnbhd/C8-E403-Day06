from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import JSON as JSONType
from sqlalchemy.sql import func
from ..base import Base


class LogEntry(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, nullable=False, index=True)
    message = Column(String, nullable=False)
    meta = Column(JSONType, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
