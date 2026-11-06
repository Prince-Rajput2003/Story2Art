from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.config import ASPECT_RATIO_OPTIONS, IMAGE_STYLE_OPTIONS, MAX_STORY_LENGTH, MIN_STORY_LENGTH, QUALITY_OPTIONS


class GenerateRequest(BaseModel):
    story: str = Field(..., min_length=MIN_STORY_LENGTH, max_length=MAX_STORY_LENGTH)
    image_style: str = "Cinematic"
    aspect_ratio: str = "1:1"
    quality: str = "medium"
    enhance_story: bool = False

    @field_validator("story")
    @classmethod
    def validate_story_content(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned.strip():
            raise ValueError("Story cannot be empty.")
        return cleaned

    @field_validator("image_style")
    @classmethod
    def normalize_style(cls, value: str) -> str:
        normalized = (value or "Cinematic").strip()
        if normalized not in IMAGE_STYLE_OPTIONS:
            raise ValueError(f"Image style must be one of: {', '.join(IMAGE_STYLE_OPTIONS)}")
        return normalized

    @field_validator("aspect_ratio")
    @classmethod
    def normalize_aspect_ratio(cls, value: str) -> str:
        normalized = (value or "1:1").strip()
        if normalized not in ASPECT_RATIO_OPTIONS:
            raise ValueError("Aspect ratio must be one of 1:1, 16:9, 9:16, 4:3, or 3:4.")
        return normalized

    @field_validator("quality")
    @classmethod
    def normalize_quality(cls, value: str) -> str:
        normalized = (value or "medium").lower()
        if normalized not in QUALITY_OPTIONS:
            raise ValueError("Quality must be low, medium, or high.")
        return normalized


class EnhanceStoryRequest(BaseModel):
    story: str = Field(..., min_length=MIN_STORY_LENGTH, max_length=MAX_STORY_LENGTH)


class ImageGenerationResult(BaseModel):
    id: str
    filename: str
    image_url: str
    image_style: str
    aspect_ratio: str
    quality: str
    enhanced_prompt: str
    created_at: datetime


class GalleryItem(BaseModel):
    id: str
    original_story: str
    enhanced_prompt: str
    image_style: str
    aspect_ratio: str
    quality: str
    filename: str
    created_at: datetime
    image_url: str
    favorite: bool = False


class SuccessResponse(BaseModel):
    message: str
    image: Optional[ImageGenerationResult] = None


class HealthResponse(BaseModel):
    status: str
    message: str
    openai_configured: bool
    openai_connected: bool
    image_model_ready: bool
    configured_model: str
