from sqlalchemy import Column, String
from ..base import Base


class Exercise(Base):
    """Exercise catalog — maps a Hevy exercise to its muscle group.

    Mirrors the §5 contract shape {exercise_id, name, muscle_group}.
    """

    __tablename__ = "exercises"

    exercise_id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    muscle_group = Column(String, nullable=False, index=True)
