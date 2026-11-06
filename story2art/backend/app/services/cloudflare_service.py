import base64
import json
import time
from urllib import error as urllib_error
from urllib import request as urllib_request

from app.config import (
    CLOUDFLARE_ACCOUNT_ID,
    CLOUDFLARE_API_TOKEN,
    CLOUDFLARE_IMAGE_MODEL,
    REMOTE_IMAGE_PROVIDER_TIMEOUT,
)
from app.utils.image_utils import save_image_from_base64


class CloudflareAIError(RuntimeError):
    pass


def _build_request_url(account_id: str, model_name: str) -> str:
    if not account_id or not model_name:
        raise CloudflareAIError("Cloudflare account ID and model name are required.")
    return f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_name}"


def _normalize_prompt(prompt: str, style: str, negative_prompt: str | None) -> str:
    style_prompt = {
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
    }.get(style, style or "cinematic")

    if negative_prompt and negative_prompt.strip():
        return f"{style_prompt}. {prompt}. Avoid: {negative_prompt.strip()}"
    return f"{style_prompt}. {prompt}"


def _request_payload(prompt: str, style: str, negative_prompt: str | None, aspect_ratio: str, quality: str) -> dict:
    return {"prompt": _normalize_prompt(prompt, style, negative_prompt)}


def _extract_image_base64(payload):
    if isinstance(payload, str):
        value = payload.strip()
        if value.startswith("data:image"):
            return value.split(",", 1)[1]
        return value

    if isinstance(payload, dict):
        for key in ("image", "result", "output", "data"):
            if key in payload:
                candidate = _extract_image_base64(payload[key])
                if candidate:
                    return candidate
        if "result" in payload and isinstance(payload["result"], dict):
            for key in ("image", "data", "base64"):
                if key in payload["result"]:
                    candidate = _extract_image_base64(payload["result"][key])
                    if candidate:
                        return candidate

    if isinstance(payload, list):
        for item in payload:
            candidate = _extract_image_base64(item)
            if candidate:
                return candidate

    return None


def generate_cloudflare_image(prompt: str, style: str, aspect_ratio: str, quality: str, negative_prompt: str | None = None) -> tuple[str, str]:
    if not CLOUDFLARE_API_TOKEN:
        raise CloudflareAIError("CLOUDFLARE_API_TOKEN is not configured in backend/.env.")
    if not CLOUDFLARE_ACCOUNT_ID:
        raise CloudflareAIError("CLOUDFLARE_ACCOUNT_ID is required to call Cloudflare Workers AI.")

    endpoint = _build_request_url(CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_IMAGE_MODEL)
    payload = _request_payload(prompt, style, negative_prompt, aspect_ratio, quality)
    req = urllib_request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=REMOTE_IMAGE_PROVIDER_TIMEOUT) as response:
            body = response.read()
            if not body:
                raise CloudflareAIError("Cloudflare Workers AI returned an empty response.")
            try:
                json_body = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                raise CloudflareAIError("Cloudflare Workers AI returned a non-JSON response.")

            image_b64 = _extract_image_base64(json_body)
            if not image_b64:
                raise CloudflareAIError("Cloudflare Workers AI did not return an image payload in the expected format.")

            if image_b64.startswith("data:image"):
                image_b64 = image_b64.split(",", 1)[1]
            if not image_b64:
                raise CloudflareAIError("Cloudflare Workers AI returned an empty image payload.")

            try:
                base64.b64decode(image_b64, validate=True)
            except Exception as exc:
                raise CloudflareAIError("Cloudflare Workers AI returned an invalid base64 image payload.") from exc

            filename = save_image_from_base64(image_b64)
            return filename, "base64"
    except urllib_error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")
        raise CloudflareAIError(f"Cloudflare Workers AI request failed with HTTP {exc.code}: {error_text}") from exc
    except urllib_error.URLError as exc:
        raise CloudflareAIError(f"Cloudflare Workers AI request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise CloudflareAIError("Cloudflare Workers AI request timed out.") from exc
