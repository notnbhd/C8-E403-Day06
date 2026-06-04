from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class Routine(Base):
    """A saved routine. The §5 contract exposes a string `routine_id`
    (e.g. "rt_0001"); it is derived from this integer `id`.
    """

    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exercises = relationship(
        "RoutineExercise",
        cascade="all, delete-orphan",
        order_by="RoutineExercise.position",
        backref="routine",
    )
