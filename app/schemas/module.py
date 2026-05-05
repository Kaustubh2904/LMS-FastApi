from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.module import ContentType

class ModuleBase(BaseModel):
    title: str
    description: Optional[str] = None

class ModuleCreateURL(ModuleBase):
    """Schema for creating a module using a Video URL or External Link."""
    content_type: ContentType
    content_url: str

class ModuleResponse(ModuleBase):
    """Schema for responding with module details (excluding raw binary data)."""
    id: int
    course_id: int
    content_type: ContentType
    content_url: Optional[str] = None
    file_name: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
