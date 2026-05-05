from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str
    role: str = "employee"

class UserCreateAdmin(UserBase):
    password: str

class User(UserBase):
    id: int
    role: str
    is_active: bool
    team_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class TeamBase(BaseModel):
    name: str
    department_id: Optional[int] = None

class TeamCreate(TeamBase):
    pass

class Team(TeamBase):
    id: int
    
    class Config:
        from_attributes = True

class DepartmentBase(BaseModel):
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: int
    
    class Config:
        from_attributes = True
