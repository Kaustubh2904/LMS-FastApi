import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database import get_db
from app.models.quiz import Quiz, Question, QuizAssignment, QuizAttempt
from app.models.course import Course, Enrollment
from app.models.user import User, Team
from app.schemas.quiz import (
    QuizCreate, QuizResponse, QuestionResponse, 
    QuizAttemptSubmit, QuizAttemptResponse, QuizAssignRequest
)
from app.schemas.course import AssignmentTargetType
from app.deps import get_current_admin, get_current_user

router = APIRouter()

@router.post("/", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(
    quiz_in: QuizCreate, 
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    # Verify course if embedded
    if quiz_in.course_id:
        course = db.query(Course).filter(Course.id == quiz_in.course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
            
    quiz = Quiz(**quiz_in.model_dump())
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    
    # If the quiz is embedded, we should automatically assign it to all users already enrolled in the course.
    if quiz.course_id:
        enrollments = db.query(Enrollment).filter(Enrollment.course_id == quiz.course_id).all()
        for en in enrollments:
            assignment = QuizAssignment(quiz_id=quiz.id, user_id=en.user_id)
            db.add(assignment)
        db.commit()
        
    return quiz

@router.post("/{quiz_id}/questions/upload")
def upload_questions_csv(
    quiz_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
        
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
        
    content = file.file.read().decode("utf-8")
    file.file.close()
    
    csv_reader = csv.DictReader(io.StringIO(content))
    required_fields = ['Question', 'OptionA', 'OptionB', 'OptionC', 'OptionD', 'CorrectAnswer', 'Points']
    
    if not csv_reader.fieldnames or not all(field in csv_reader.fieldnames for field in required_fields):
        raise HTTPException(status_code=400, detail=f"CSV must contain {', '.join(required_fields)} columns")
        
    added_count = 0
    # Clear existing questions if needed (optional), but we will append for now.
    
    for row in csv_reader:
        if not row.get('Question', '').strip():
            continue
            
        points = 1
        points_val = row.get('Points', '').strip()
        if points_val:
            try:
                points = int(points_val)
            except ValueError:
                pass # Defaulting to 1 if not an integer
            
        q = Question(
            quiz_id=quiz.id,
            text=row.get('Question', '').strip(),
            option_a=row.get('OptionA', '').strip(),
            option_b=row.get('OptionB', '').strip(),
            option_c=row.get('OptionC', '').strip(),
            option_d=row.get('OptionD', '').strip(),
            correct_answer=row.get('CorrectAnswer', '').strip().upper(),
            points=points
        )
        db.add(q)
        added_count += 1
        
    db.commit()
    return {"message": f"Successfully added {added_count} questions."}

@router.get("/{quiz_id}/questions", response_model=List[QuestionResponse])
def get_quiz_questions(
    quiz_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
        
    if current_user.role != "admin":
        assignment = db.query(QuizAssignment).filter(
            QuizAssignment.quiz_id == quiz.id, 
            QuizAssignment.user_id == current_user.id
        ).first()
        if not assignment:
            raise HTTPException(status_code=403, detail="You are not assigned to this quiz")
            
    return quiz.questions

@router.post("/{quiz_id}/assign")
def assign_quiz(
    quiz_id: int,
    assign_req: QuizAssignRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    users_to_assign = []

    if assign_req.target_type == AssignmentTargetType.all:
        users_to_assign = db.query(User).filter(User.role == "employee", User.is_active == True).all()
    elif assign_req.target_type == AssignmentTargetType.team:
        users_to_assign = db.query(User).filter(User.team_id == assign_req.target_id, User.role == "employee", User.is_active == True).all()
    elif assign_req.target_type == AssignmentTargetType.user:
        user = db.query(User).filter(User.id == assign_req.target_id, User.is_active == True).first()
        if user:
            users_to_assign = [user]

    existing = db.query(QuizAssignment.user_id).filter(QuizAssignment.quiz_id == quiz_id).all()
    existing_ids = {e[0] for e in existing}

    new_assignments = 0
    for user in users_to_assign:
        if user.id not in existing_ids:
            assignment = QuizAssignment(quiz_id=quiz.id, user_id=user.id)
            db.add(assignment)
            new_assignments += 1

    db.commit()
    return {"message": f"Successfully assigned quiz to {new_assignments} new users."}

@router.post("/{quiz_id}/attempt", response_model=QuizAttemptResponse)
def submit_quiz_attempt(
    quiz_id: int,
    payload: QuizAttemptSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
        
    assignment = db.query(QuizAssignment).filter(
        QuizAssignment.quiz_id == quiz.id, 
        QuizAssignment.user_id == current_user.id
    ).first()
    
    if not assignment and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You are not assigned to this quiz")
        
    questions = quiz.questions
    if not questions:
        raise HTTPException(status_code=400, detail="Quiz has no questions")

    total_points = sum(q.points for q in questions)
    earned_points = 0
    
    for q in questions:
        user_answer = payload.answers.get(q.id)
        if user_answer and user_answer.strip().upper() == q.correct_answer:
            earned_points += q.points
            
    score_percentage = (earned_points / total_points) * 100 if total_points > 0 else 0
    passed = score_percentage >= quiz.passing_percentage
    
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        score=score_percentage,
        passed=passed
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    return attempt
