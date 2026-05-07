from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from app.models.quiz import QuizDifficulty
from app.schemas.course import AssignmentTargetType

class QuestionBase(BaseModel):
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    points: int = 1

class QuestionResponse(QuestionBase):
    id: int
    quiz_id: int
    model_config = ConfigDict(from_attributes=True)

class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    difficulty: QuizDifficulty = QuizDifficulty.medium
    passing_percentage: float = 50.0
    course_id: Optional[int] = None

class QuizCreate(QuizBase):
    pass

class QuizResponse(QuizBase):
    id: int
    created_at: datetime
    # Omitting questions in large lists, but maybe helpful for detailed fetch
    model_config = ConfigDict(from_attributes=True)

class QuizAttemptSubmit(BaseModel):
    answers: Dict[int, str]  # map of question_id -> 'A', 'B', 'C', 'D'

class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    score: float
    passed: bool
    attempt_date: datetime
    model_config = ConfigDict(from_attributes=True)

class QuizAssignRequest(BaseModel):
    target_type: AssignmentTargetType
    target_id: Optional[int] = None
