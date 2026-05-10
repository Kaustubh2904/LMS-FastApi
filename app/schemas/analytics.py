from pydantic import BaseModel
from typing import List, Dict, Any

class CourseAnalytics(BaseModel):
    course_id: int
    title: str
    total_enrollments: int
    modules_count: int
    quizzes_count: int
    certificates_issued: int

class EmployeeAnalytics(BaseModel):
    user_id: int
    full_name: str
    email: str
    assigned_courses_count: int
    certificates_earned: int
    total_quiz_attempts: int

class QuizAnalytics(BaseModel):
    quiz_id: int
    title: str
    total_attempts: int
    passed_attempts: int
    average_score: float
