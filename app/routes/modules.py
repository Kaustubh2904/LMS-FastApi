import io
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.course import Course, Enrollment
from app.models.module import Module, ContentType
from app.models.user import User
from app.schemas.module import ModuleCreateURL, ModuleResponse
from app.deps import get_current_admin, get_current_user

router = APIRouter()

@router.post("/courses/{course_id}/modules/upload", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
def upload_module_file(
    course_id: int,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    content_type: ContentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    """
    Upload a PDF or Image as a new Module for the specified course.
    """
    if content_type not in [ContentType.pdf, ContentType.image]:
        raise HTTPException(
            status_code=400, 
            detail="This endpoint is for uploading files. Use /url endpoint for Links and Videos."
        )

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    file_data = file.file.read()
    file.file.close()

    db_module = Module(
        course_id=course.id,
        title=title,
        description=description,
        content_type=content_type,
        file_data=file_data,
        file_name=file.filename
    )
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module

@router.post("/courses/{course_id}/modules/url", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
def create_module_url(
    course_id: int,
    module_in: ModuleCreateURL,
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    """
    Add a Video URL or External Link as a new Module for the specified course.
    """
    if module_in.content_type not in [ContentType.video_url, ContentType.external_link]:
        raise HTTPException(
            status_code=400, 
            detail="This endpoint is for Video and External Links. Use /upload endpoint for PDFs and Images."
        )

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db_module = Module(
        course_id=course.id,
        **module_in.model_dump()
    )
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module


@router.get("/courses/{course_id}/modules", response_model=List[ModuleResponse])
def get_course_modules(
    course_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of all modules for a specific course (excluding file binary data).
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Basic check to see if employee is enrolled or admin
    if current_user.role != "admin":
        is_enrolled = db.query(Enrollment).filter(
            Enrollment.course_id == course_id, 
            Enrollment.user_id == current_user.id
        ).first()
        if not is_enrolled:
            raise HTTPException(status_code=403, detail="Not enrolled in this course")

    return course.modules


@router.get("/modules/{module_id}/file")
def download_module_file(
    module_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download the binary file data (PDF or Image) for a module.
    """
    module_obj = db.query(Module).filter(Module.id == module_id).first()
    if not module_obj or module_obj.file_data is None:
        raise HTTPException(status_code=404, detail="File content not found for this module")
    
    # Basic check to see if employee is enrolled or admin
    if current_user.role != "admin":
        is_enrolled = db.query(Enrollment).filter(
            Enrollment.course_id == module_obj.course_id, 
            Enrollment.user_id == current_user.id
        ).first()
        if not is_enrolled:
            raise HTTPException(status_code=403, detail="Not enrolled in the parent course")

    # Serve the file from DB
    return StreamingResponse(
        io.BytesIO(module_obj.file_data),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{module_obj.file_name}"'}
    )

@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(
    module_id: int, 
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete a module permanently. Admin only.
    """
    module_obj = db.query(Module).filter(Module.id == module_id).first()
    if not module_obj:
        raise HTTPException(status_code=404, detail="Module not found")
        
    db.delete(module_obj)
    db.commit()
    return None
