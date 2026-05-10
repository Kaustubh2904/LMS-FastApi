from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class CertificateTemplate(Base):
    __tablename__ = "certificate_templates"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), unique=True, index=True)
    file_data = Column(LargeBinary, nullable=False)
    file_name = Column(String, nullable=False)
    content_type = Column(String, nullable=False) # 'application/pdf' or 'image/png' etc.
    
    # Store hardcoded positions (X, Y) for text overlap (simplified format, maybe JSON or just columns)
    name_x = Column(Integer, default=100)
    name_y = Column(Integer, default=100)
    course_x = Column(Integer, default=100)
    course_y = Column(Integer, default=150)
    date_x = Column(Integer, default=100)
    date_y = Column(Integer, default=200)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    course = relationship("Course", backref="certificate_template")

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    file_data = Column(LargeBinary, nullable=False)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", backref="certificates")
    course = relationship("Course", backref="issued_certificates")
