from sqlalchemy import Column, Integer, String, ForeignKey
from ..base import Base


class RoutineExercise(Base):
    """One exercise line inside a routine: {exercise_id, sets, reps, rest_sec}.

    `reps` is a string because Hevy allows ranges ("8-12").
    """

    __tablename__ = "routine_exercises"

    id = Column(Integer, primary_key=True, index=True)
    routine_id = Column(Integer, ForeignKey("routines.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(String, ForeignKey("exercises.exercise_id"), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    sets = Column(Integer, nullable=False)
    reps = Column(String, nullable=False)
    rest_sec = Column(Integer, nullable=False)
