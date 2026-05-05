from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class ContentType(str, enum.Enum):
    pdf = "pdf"
    image = "image"
    video_url = "video_url"
    external_link = "external_link"

class Module(Base):
    __tablename__ = "modules"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    content_type = Column(Enum(ContentType), nullable=False)
    
    # Text data (URLs, paths)
    content_url = Column(String, nullable=True)
    
    # Binary data (PDFs, Images)
    file_data = Column(LargeBinary, nullable=True)
    file_name = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    course = relationship("Course", back_populates="modules")
