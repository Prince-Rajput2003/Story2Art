from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import GENERATED_IMAGES_DIR
from app.database import get_db
from app.models import GeneratedImage, User
from app.services.auth_service import get_current_user
from app.utils.image_utils import get_image_mime_type, remove_image_file

router = APIRouter()


def serialize_image(record: GeneratedImage, request: Request):
    return {
        "id": record.id,
        "original_story": record.original_story,
        "enhanced_prompt": record.enhanced_prompt,
        "image_style": record.image_style,
        "aspect_ratio": record.aspect_ratio,
        "quality": record.quality,
        "filename": record.filename,
        "favorite": record.favorite,
        "created_at": record.created_at.isoformat(),
        "image_url": str(request.url_for("serve_generated_image", filename=record.filename)),
    }


@router.get("/api/gallery")
def list_gallery(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    images = db.query(GeneratedImage).filter(GeneratedImage.user_id == current_user.id).order_by(GeneratedImage.created_at.desc()).all()
    return [serialize_image(item, request) for item in images]


@router.get("/api/gallery/{image_id}")
def get_gallery_item(image_id: str, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id, GeneratedImage.user_id == current_user.id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found.")
    return serialize_image(image, request)


@router.delete("/api/gallery/{image_id}")
def delete_gallery_item(image_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id, GeneratedImage.user_id == current_user.id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found.")

    try:
        remove_image_file(image.filename)
    except Exception:
        pass

    db.delete(image)
    db.commit()
    return {"message": "Image deleted successfully."}


@router.get("/api/images/{filename}")
def serve_generated_image(filename: str):
    safe_filename = Path(filename).name
    if safe_filename != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid image path.")

    image_path = GENERATED_IMAGES_DIR / safe_filename
    if not image_path.exists() or not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found.")

    image_mime_type = get_image_mime_type(image_path.read_bytes())
    return FileResponse(
        image_path,
        media_type=image_mime_type,
        headers={"Cross-Origin-Resource-Policy": "cross-origin"},
    )
