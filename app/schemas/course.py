from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class CourseDifficultyEnum(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    difficulty: CourseDifficultyEnum = CourseDifficultyEnum.medium

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[CourseDifficultyEnum] = None

class CourseResponse(CourseBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AssignmentTargetType(str, Enum):
    all = "all"
    team = "team"
    user = "user"

class CourseAssignRequest(BaseModel):
    target_type: AssignmentTargetType
    target_id: Optional[int] = None  # Required if target_type is team or user 
