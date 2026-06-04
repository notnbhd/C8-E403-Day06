from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from ..base import Base


class WorkoutSet(Base):
    """One logged set. Corresponds to the §5 `Set` shape; `exercise_name`
    in the contract is resolved by joining `exercises`.
    """

    __tablename__ = "workout_sets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(String, ForeignKey("exercises.exercise_id"), nullable=False)
    performed_on = Column(Date, nullable=False)
    weight_kg = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)
    set_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_workout_sets_user_date", "user_id", "performed_on"),
        Index("ix_workout_sets_user_exercise", "user_id", "exercise_id"),
    )
