from fastapi import FastAPI, APIRouter
from app.models.user import User, Team, Department
from app.models.course import Course, Enrollment
from app.models.module import Module, ContentType
from app.models.quiz import Quiz, Question, QuizAssignment, QuizAttempt
from app.models.certificate import Certificate, CertificateTemplate
from app.routes import auth, users, courses, modules, quizzes, certificates, analytics

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
api_router.include_router(modules.router, tags=["Modules & Content"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["Quizzes & Progress"])
api_router.include_router(certificates.router, tags=["Certificates"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}