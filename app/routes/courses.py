from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.course import Course, Enrollment
from app.models.user import User, Team
from app.models.quiz import Quiz, QuizAssignment
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse, CourseAssignRequest, AssignmentTargetType
from app.deps import get_current_admin, get_current_user

router = APIRouter()

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course_in: CourseCreate, 
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    course = Course(**course_in.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

@router.get("/", response_model=List[CourseResponse])
def get_courses(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    courses = db.query(Course).offset(skip).limit(limit).all()
    return courses

@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int, 
    course_in: CourseUpdate, 
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    update_data = course_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(course, key, value)
        
    db.commit()
    db.refresh(course)
    return course

@router.post("/{course_id}/assign")
def assign_course(
    course_id: int,
    assign_req: CourseAssignRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    users_to_enroll = []

    if assign_req.target_type == AssignmentTargetType.all:
        users_to_enroll = db.query(User).filter(User.role == "employee", User.is_active == True).all()
    
    elif assign_req.target_type == AssignmentTargetType.team:
        if not assign_req.target_id:
            raise HTTPException(status_code=400, detail="target_id is required for team assignment")
        team = db.query(Team).filter(Team.id == assign_req.target_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        users_to_enroll = db.query(User).filter(User.team_id == team.id, User.role == "employee", User.is_active == True).all()
        
    elif assign_req.target_type == AssignmentTargetType.user:
        if not assign_req.target_id:
            raise HTTPException(status_code=400, detail="target_id is required for user assignment")
        user = db.query(User).filter(User.id == assign_req.target_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        users_to_enroll = [user]

    # Find existing enrollments for this course to avoid duplicates
    existing_enrollments = db.query(Enrollment.user_id).filter(Enrollment.course_id == course_id).all()
    existing_user_ids = {e[0] for e in existing_enrollments}

    # Fetch quizzes embedded in this course for auto-assignment
    course_quizzes = db.query(Quiz).filter(Quiz.course_id == course_id).all()

    new_enrollments = 0
    for user in users_to_enroll:
        if user.id not in existing_user_ids:
            enrollment = Enrollment(user_id=user.id, course_id=course.id)
            db.add(enrollment)
            new_enrollments += 1
            
            # Auto-assign embedded quizzes to newly enrolled user
            for quiz in course_quizzes:
                existing_qa = db.query(QuizAssignment).filter(
                    QuizAssignment.quiz_id == quiz.id, 
                    QuizAssignment.user_id == user.id
                ).first()
                if not existing_qa:
                    db.add(QuizAssignment(quiz_id=quiz.id, user_id=user.id))

    db.commit()
    
    return {
        "message": f"Successfully assigned course to {new_enrollments} new users.",
        "total_enrolled": new_enrollments
    }
