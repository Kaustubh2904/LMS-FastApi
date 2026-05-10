from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class CertificateTemplateResponse(BaseModel):
    id: int
    course_id: int
    file_name: str
    content_type: str
    name_x: int
    name_y: int
    course_x: int
    course_y: int
    date_x: int
    date_y: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CertificateResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    issued_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
