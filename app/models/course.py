from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class CourseDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    # Progress tracking could be added here later
    
    user = relationship("User", backref="enrollments")
    course = relationship("Course", back_populates="enrollments")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    difficulty = Column(Enum(CourseDifficulty), default=CourseDifficulty.medium, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    # Will add quizzes relationships in future sprints
