import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User, Team, Department
from app.schemas.user import User as UserSchema, UserCreate, TeamCreate, Team as TeamSchema, DepartmentCreate, Department as DepartmentSchema
from app.deps import get_current_admin, get_current_user
from app.core.security import get_password_hash

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/employees/upload", response_model=dict)
def upload_employees_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = file.file.read().decode("utf-8")
    file.file.close()
    
    csv_reader = csv.DictReader(io.StringIO(content))
    required_fields = ['email', 'password', 'full_name']
    
    if not csv_reader.fieldnames or not all(field in csv_reader.fieldnames for field in required_fields):
        raise HTTPException(status_code=400, detail=f"CSV must contain {', '.join(required_fields)} columns")
    
    added_count = 0
    for row in csv_reader:
        email = row.get('email', '').strip()
        if not email:
            continue
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            new_user = User(
                email=email,
                full_name=row.get('full_name', '').strip(),
                hashed_password=get_password_hash(row.get('password', '')),
                role="employee"
            )
            db.add(new_user)
            added_count += 1
            
    db.commit()
    return {"message": f"Successfully added {added_count} employees."}

@router.post("/departments", response_model=DepartmentSchema)
def create_department(dept_in: DepartmentCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    dept = Department(name=dept_in.name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept

@router.post("/teams", response_model=TeamSchema)
def create_team(team_in: TeamCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    team = Team(name=team_in.name, department_id=team_in.department_id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team

@router.put("/employees/{user_id}/team")
def assign_team_to_employee(user_id: int, team_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    user.team_id = team.id
    db.commit()
    return {"message": "Team assigned successfully."}
