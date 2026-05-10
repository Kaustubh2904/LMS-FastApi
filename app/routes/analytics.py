from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.course import Course, Enrollment
from app.models.user import User
from app.models.quiz import Quiz, QuizAttempt
from app.models.certificate import Certificate
from app.models.module import Module
from app.schemas.analytics import CourseAnalytics, EmployeeAnalytics, QuizAnalytics
from app.deps import get_current_admin

router = APIRouter()

@router.get("/courses", response_model=List[CourseAnalytics])
def get_course_analytics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    courses = db.query(Course).all()
    results = []
    
    for c in courses:
        enrollments = db.query(Enrollment).filter(Enrollment.course_id == c.id).count()
        modules = db.query(Module).filter(Module.course_id == c.id).count()
        quizzes = db.query(Quiz).filter(Quiz.course_id == c.id).count()
        certs = db.query(Certificate).filter(Certificate.course_id == c.id).count()
        
        results.append(CourseAnalytics(
            course_id=c.id,
            title=c.title,
            total_enrollments=enrollments,
            modules_count=modules,
            quizzes_count=quizzes,
            certificates_issued=certs
        ))
    return results

@router.get("/employees", response_model=List[EmployeeAnalytics])
def get_employee_analytics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    users = db.query(User).filter(User.role == "employee").all()
    results = []
    
    for u in users:
        courses = db.query(Enrollment).filter(Enrollment.user_id == u.id).count()
        certs = db.query(Certificate).filter(Certificate.user_id == u.id).count()
        attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == u.id).count()
        
        results.append(EmployeeAnalytics(
            user_id=u.id,
            full_name=u.full_name or "Unknown",
            email=u.email,
            assigned_courses_count=courses,
            certificates_earned=certs,
            total_quiz_attempts=attempts
        ))
    return results

@router.get("/quizzes", response_model=List[QuizAnalytics])
def get_quiz_analytics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    quizzes = db.query(Quiz).all()
    results = []
    
    for q in quizzes:
        attempts_q = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == q.id).all()
        total_attempts = len(attempts_q)
        passed_attempts = sum(1 for a in attempts_q if a.passed)
        avg_score = sum(a.score for a in attempts_q) / total_attempts if total_attempts > 0 else 0.0
        
        results.append(QuizAnalytics(
            quiz_id=q.id,
            title=q.title,
            total_attempts=total_attempts,
            passed_attempts=passed_attempts,
            average_score=avg_score
        ))
    return results
