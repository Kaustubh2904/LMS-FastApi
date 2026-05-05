from fastapi import FastAPI
from app.models.user import User, Team, Department
from app.models.course import Course, Enrollment
from app.routes import auth, users, courses

app = FastAPI()

# Create database tables
@app.on_event("startup")
async def startup():
    # Code to create database tables
    pass

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(courses.router, prefix="/courses", tags=["courses"])

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}