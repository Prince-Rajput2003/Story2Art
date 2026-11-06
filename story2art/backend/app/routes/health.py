from fastapi import APIRouter

from app.config import (
    CLOUDFLARE_ACCOUNT_ID,
    CLOUDFLARE_API_TOKEN,
    CLOUDFLARE_IMAGE_MODEL,
    IMAGE_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    REMOTE_IMAGE_PROVIDER_URL,
    REMOTE_IMAGE_MODEL,
)
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
def health_check():
    configured = bool(OPENAI_API_KEY or REMOTE_IMAGE_PROVIDER_URL or CLOUDFLARE_API_TOKEN)
    connected = False
    image_model_ready = False
    resolved_model = OPENAI_MODEL

    if IMAGE_PROVIDER.lower() in {"cloudflare_workers_ai", "cloudflare", "workers_ai"}:
        resolved_model = CLOUDFLARE_IMAGE_MODEL or "@cf/black-forest-labs/flux-1-schnell"
        connected = bool(CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID)
        image_model_ready = connected
        status = "ok" if connected else "warning"
        message = "Story2Art backend is running successfully." if connected else "Cloudflare Workers AI is not configured."
    elif IMAGE_PROVIDER.lower() in {"remote_stable_diffusion", "stable_diffusion", "remote_sd"}:
        resolved_model = REMOTE_IMAGE_MODEL or "stable-diffusion"
        connected = bool(REMOTE_IMAGE_PROVIDER_URL)
        image_model_ready = connected
        status = "ok" if connected else "warning"
        message = "Story2Art backend is running successfully." if connected else "No remote Stable Diffusion provider is configured."
    else:
        resolved_model = OPENAI_MODEL
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=OPENAI_API_KEY)
                models = client.models.list()
                model_ids = {model.id for model in models.data}
                connected = True
                resolved_model = OPENAI_MODEL
                image_model_ready = resolved_model in model_ids
            except Exception:
                connected = False
                image_model_ready = False
        status = "ok" if configured else "warning"
        message = "Story2Art backend is running successfully." if configured else "OpenAI API key is not configured."

    return HealthResponse(
        status=status,
        message=message,
        openai_configured=configured,
        openai_connected=connected,
        image_model_ready=image_model_ready,
        configured_model=resolved_model,
    )
