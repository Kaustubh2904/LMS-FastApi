from fastapi import FastAPI, APIRouter
from app.models.user import User, Team, Department
from app.models.course import Course, Enrollment
from app.routes import auth, users, courses

app = FastAPI(title="LMS Backend", version="1.0.0")

# Create database tables
@app.on_event("startup")
async def startup():
    # Code to create database tables
    pass

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses & Enrollment"])

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}