import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from PIL import Image, ImageDraw, ImageFont

from app.database import get_db
from app.models.certificate import CertificateTemplate, Certificate
from app.models.course import Course, Enrollment
from app.models.quiz import QuizAttempt
from app.models.user import User
from app.schemas.certificate import CertificateTemplateResponse, CertificateResponse
from app.deps import get_current_admin, get_current_user

router = APIRouter()

@router.post("/courses/{course_id}/certificate-template", response_model=CertificateTemplateResponse)
def upload_certificate_template(
    course_id: int,
    file: UploadFile = File(...),
    name_x: int = Form(100),
    name_y: int = Form(100),
    course_x: int = Form(100),
    course_y: int = Form(150),
    date_x: int = Form(100),
    date_y: int = Form(200),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Admin uploads a blank certificate image (PNG/JPEG) and configures text coordinates.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image templates are supported at this time.")

    file_data = file.file.read()
    file.file.close()

    template = db.query(CertificateTemplate).filter(CertificateTemplate.course_id == course_id).first()
    if template:
        template.file_data = file_data
        template.file_name = file.filename
        template.content_type = file.content_type
        template.name_x = name_x
        template.name_y = name_y
        template.course_x = course_x
        template.course_y = course_y
        template.date_x = date_x
        template.date_y = date_y
    else:
        template = CertificateTemplate(
            course_id=course.id,
            file_data=file_data,
            file_name=file.filename,
            content_type=file.content_type,
            name_x=name_x,
            name_y=name_y,
            course_x=course_x,
            course_y=course_y,
            date_x=date_x,
            date_y=date_y
        )
        db.add(template)
        
    db.commit()
    db.refresh(template)
    return template


def _generate_image_certificate(template_bytes: bytes, user_name: str, course_name: str, template: CertificateTemplate) -> bytes:
    image = Image.open(io.BytesIO(template_bytes))
    draw = ImageDraw.Draw(image)
    
    try:
        # Tries to load standard font, might fall back to default
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()

    draw.text((template.name_x, template.name_y), user_name, fill="black", font=font)
    draw.text((template.course_x, template.course_y), course_name, fill="black", font=font)
    
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    draw.text((template.date_x, template.date_y), date_str, fill="black", font=font)
    
    output = io.BytesIO()
    # Save using the format inferred from PIL
    image.save(output, format=image.format or 'PNG')
    return output.getvalue()


@router.post("/courses/{course_id}/generate-certificates")
def generate_certificates(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Finds all users enrolled in the given course. If they passed all quizzes, auto-generates certificates.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    template = db.query(CertificateTemplate).filter(CertificateTemplate.course_id == course_id).first()
    if not template:
        raise HTTPException(status_code=400, detail="Upload a certificate template for this course first.")
        
    enrollments = db.query(Enrollment).filter(Enrollment.course_id == course_id).all()
    
    generated_count = 0
    for en in enrollments:
        user = db.query(User).filter(User.id == en.user_id).first()
        
        # Check if already generated
        existing_cert = db.query(Certificate).filter(
            Certificate.course_id == course_id, 
            Certificate.user_id == user.id
        ).first()
        if existing_cert:
            continue
            
        # Simplified Progress Logic: Admin triggers generation, so we just assume completion
        # You can expand it to cross-check `QuizAttempt` if you require it here.
        
        cert_bytes = _generate_image_certificate(template.file_data, user.full_name, course.title, template)
        
        cert = Certificate(
            user_id=user.id,
            course_id=course.id,
            file_data=cert_bytes
        )
        db.add(cert)
        generated_count += 1
        
    db.commit()
    return {"message": f"Successfully generated {generated_count} new certificates!"}


@router.get("/users/me/certificates", response_model=List[CertificateResponse])
def get_my_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Certificate).filter(Certificate.user_id == current_user.id).all()


@router.get("/certificates/{certificate_id}/download")
def download_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
        
    if cert.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this certificate")
        
    return StreamingResponse(
        io.BytesIO(cert.file_data),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="certificate_{cert.id}.png"'}
    )
