from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.image_utils import image_to_data_url
from app.models import CreditTransaction, GeneratedImage, User
from app.schemas import EnhanceStoryRequest, GenerateRequest
from app.services import openai_service, prompt_service
from app.services.auth_service import get_current_user
from app.services.credit_service import deduct_credits, get_credit_cost, get_or_create_wallet

router = APIRouter()


@router.post("/api/enhance-story")
def enhance_story(payload: EnhanceStoryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        enhanced_prompt = prompt_service.enhance_story_prompt(payload.story)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"enhanced_prompt": enhanced_prompt}


@router.post("/api/generate")
def generate_story_image(payload: GenerateRequest, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enhanced_prompt = payload.story
    if payload.enhance_story:
        try:
            enhanced_prompt = prompt_service.enhance_story_prompt(payload.story)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    cost = get_credit_cost(payload.image_style, payload.quality)
    wallet = get_or_create_wallet(db, current_user)
    if wallet.balance < cost:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. {cost} credits are required for this generation.")

    try:
        filename, source = openai_service.generate_image(
            prompt=enhanced_prompt,
            style=payload.image_style,
            aspect_ratio=payload.aspect_ratio,
            quality=payload.quality,
            negative_prompt=getattr(payload, "negative_prompt", None),
        )
        image_data_url = image_to_data_url(filename)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        wallet = deduct_credits(
            db,
            current_user,
            cost,
            "generation",
            f"Image generation using {payload.image_style} style",
            reference_id=f"gen-{payload.image_style.lower().replace(' ', '-')}",
        )

        image_record = GeneratedImage(
            user_id=current_user.id,
            original_story=payload.story,
            enhanced_prompt=enhanced_prompt,
            image_style=payload.image_style,
            aspect_ratio=payload.aspect_ratio,
            quality=payload.quality,
            filename=filename,
        )
        db.add(image_record)
        db.commit()
        db.refresh(image_record)
    except Exception as exc:
        if wallet.balance < cost:
            wallet.balance += cost
        db.rollback()
        raise HTTPException(status_code=500, detail="Generation was processed but credit storage failed. Please retry.") from exc

    return {
        "message": "Image generated successfully.",
        "image": {
            "id": image_record.id,
            "filename": image_record.filename,
            "image_url": str(request.url_for("serve_generated_image", filename=image_record.filename)),
            "image_data_url": image_data_url,
            "image_style": image_record.image_style,
            "aspect_ratio": image_record.aspect_ratio,
            "quality": image_record.quality,
            "enhanced_prompt": image_record.enhanced_prompt,
            "created_at": image_record.created_at.isoformat(),
        },
    }
