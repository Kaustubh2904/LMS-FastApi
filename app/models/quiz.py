from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class QuizDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    difficulty = Column(Enum(QuizDifficulty), default=QuizDifficulty.medium, nullable=False)
    passing_percentage = Column(Float, default=50.0, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    course = relationship("Course", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    assignments = relationship("QuizAssignment", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(String, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False) # Expected to be 'A', 'B', 'C', or 'D'
    points = Column(Integer, default=1, nullable=False)
    
    quiz = relationship("Quiz", back_populates="questions")

class QuizAssignment(Base):
    __tablename__ = "quiz_assignments"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    quiz = relationship("Quiz", back_populates="assignments")
    user = relationship("User", backref="quiz_assignments")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    passed = Column(Boolean, nullable=False)
    attempt_date = Column(DateTime(timezone=True), server_default=func.now())
    
    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", backref="quiz_attempts")
