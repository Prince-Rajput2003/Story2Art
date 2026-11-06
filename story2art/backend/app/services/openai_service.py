import base64
import os
from pathlib import Path

from openai import OpenAI

from app.config import GENERATED_IMAGES_DIR, OPENAI_API_KEY, OPENAI_MODEL
from app.services.providers import ImageGenerationError, get_active_image_provider
from app.utils.image_utils import save_image_from_base64, save_image_from_url


STYLE_PROMPTS = {
    "Realistic Photography": "photorealistic, natural skin textures, cinematic lighting, realistic detail, high fidelity",
    "Cinematic": "cinematic composition, dramatic lighting, shallow depth of field, rich contrast, atmosphere",
    "Anime": "anime illustration style, clean lines, vibrant colors, expressive face, strong composition",
    "3D Render": "3D render, volumetric lighting, detailed model, glossy surfaces, premium CGI",
    "Digital Art": "digital painting, layered textures, polished color grading, stylized details",
    "Fantasy": "fantasy worldbuilding, magical atmosphere, ornate details, ethereal lighting",
    "Oil Painting": "oil painting texture, painterly brushwork, rich color palette, classical composition",
    "Watercolor": "watercolor painting, soft washes, delicate textures, elegant transparency",
    "Cartoon": "cartoon style, bold outlines, cheerful colors, playful composition",
    "Cyberpunk": "cyberpunk aesthetic, neon reflections, urban futuristic mood, atmospheric contrast",
    "Minimalist": "minimalist composition, clean negative space, elegant simplicity, refined framing",
    "Portrait Photography": "portrait photography, shallow depth of field, eye contact, natural expression, studio lighting",
    "Architecture": "architectural visualization, precise lines, strong perspective, premium design details",
    "Landscape": "wide landscape photography, atmospheric depth, natural lighting, detailed environment",
}


def resolve_image_model(client: OpenAI) -> str:
    preferred_candidates = [
        OPENAI_MODEL,
        "gpt-image-2",
        "gpt-image-1.5",
        "gpt-image-1-mini",
        "chatgpt-image-latest",
    ]

    try:
        models = client.models.list()
        available_ids = {model.id for model in models.data}
        for candidate in preferred_candidates:
            if candidate in available_ids:
                return candidate

        for model_id in sorted(available_ids):
            if "image" in model_id.lower() or "dall" in model_id.lower():
                return model_id
    except Exception:
        pass

    return OPENAI_MODEL


def generate_image(prompt: str, style: str, aspect_ratio: str, quality: str, negative_prompt: str | None = None) -> tuple[str, str]:
    try:
        provider = get_active_image_provider()
        return provider.generate(prompt, style, aspect_ratio, quality, negative_prompt)
    except ImageGenerationError as exc:
        raise ValueError(str(exc)) from exc
