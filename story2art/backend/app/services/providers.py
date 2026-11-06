import base64
import json
import time
from abc import ABC, abstractmethod
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from openai import OpenAI

from app.config import (
    CLOUDFLARE_ACCOUNT_ID,
    CLOUDFLARE_API_TOKEN,
    CLOUDFLARE_IMAGE_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    REMOTE_IMAGE_MODEL,
    REMOTE_IMAGE_PROVIDER_API_KEY,
    REMOTE_IMAGE_PROVIDER_RETRIES,
    REMOTE_IMAGE_PROVIDER_TIMEOUT,
    REMOTE_IMAGE_PROVIDER_URL,
)
from app.services.cloudflare_service import CloudflareAIError, generate_cloudflare_image
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


class ImageGenerationError(RuntimeError):
    pass


class ImageProvider(ABC):
    name: str = "provider"

    @abstractmethod
    def generate(
        self,
        prompt: str,
        style: str,
        aspect_ratio: str,
        quality: str,
        negative_prompt: str | None = None,
    ) -> tuple[str, str]:
        raise NotImplementedError


class OpenAIImageProvider(ImageProvider):
    name = "openai"

    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise ImageGenerationError("OpenAI API key is missing. Set OPENAI_API_KEY in backend/.env before using the OpenAI provider.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def _resolve_image_model(self) -> str:
        preferred_candidates = [
            OPENAI_MODEL,
            "gpt-image-2",
            "gpt-image-1.5",
            "gpt-image-1-mini",
            "chatgpt-image-latest",
        ]

        try:
            models = self.client.models.list()
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

    @staticmethod
    def _to_openai_size(aspect_ratio: str) -> str:
        mapping = {
            "1:1": "1024x1024",
            "16:9": "1536x1024",
            "9:16": "1024x1536",
            "4:3": "1024x768",
            "3:4": "768x1024",
        }
        return mapping.get(aspect_ratio, "1024x1024")

    def generate(
        self,
        prompt: str,
        style: str,
        aspect_ratio: str,
        quality: str,
        negative_prompt: str | None = None,
    ) -> tuple[str, str]:
        resolved_model = self._resolve_image_model()
        style_prompt = STYLE_PROMPTS.get(style, style or "cinematic")
        negative_text = f" Negative prompt: {negative_prompt}." if negative_prompt and negative_prompt.strip() else ""

        try:
            response = self.client.images.generate(
                model=resolved_model,
                prompt=f"{style_prompt}. {prompt}{negative_text}",
                size=self._to_openai_size(aspect_ratio),
                quality=quality,
                n=1,
            )

            if hasattr(response, "data") and response.data:
                image_data = response.data[0]
                if hasattr(image_data, "b64_json") and image_data.b64_json:
                    filename = save_image_from_base64(image_data.b64_json)
                    return filename, "base64"
                if hasattr(image_data, "url") and image_data.url:
                    filename = save_image_from_url(image_data.url)
                    return filename, "url"

            raise ImageGenerationError("The image generation response did not contain usable image data.")
        except Exception as exc:
            message = str(exc).lower()
            if "api key" in message or "authentication" in message or "invalid" in message:
                raise ImageGenerationError("OpenAI authentication failed. Please check your API key.") from exc
            if "credits" in message or "quota" in message or "insufficient" in message:
                raise ImageGenerationError("Your OpenAI account has insufficient credits or quota for image generation.") from exc
            if "model" in message or "not supported" in message:
                raise ImageGenerationError("The configured OpenAI model is not available or incompatible with the current API version.") from exc
            raise ImageGenerationError("Image generation failed. Please try again or check your OpenAI configuration.") from exc


class CloudflareWorkersAIProvider(ImageProvider):
    name = "cloudflare_workers_ai"

    def __init__(self) -> None:
        if not CLOUDFLARE_API_TOKEN:
            raise ImageGenerationError("Cloudflare API token is missing. Set CLOUDFLARE_API_TOKEN in backend/.env.")
        if not CLOUDFLARE_ACCOUNT_ID:
            raise ImageGenerationError("Cloudflare account ID is missing. Set CLOUDFLARE_ACCOUNT_ID in backend/.env.")
        self.model = CLOUDFLARE_IMAGE_MODEL or "@cf/black-forest-labs/flux-1-schnell"

    def generate(
        self,
        prompt: str,
        style: str,
        aspect_ratio: str,
        quality: str,
        negative_prompt: str | None = None,
    ) -> tuple[str, str]:
        try:
            return generate_cloudflare_image(prompt, style, aspect_ratio, quality, negative_prompt)
        except CloudflareAIError as exc:
            raise ImageGenerationError(str(exc)) from exc


class RemoteStableDiffusionProvider(ImageProvider):
    name = "remote_stable_diffusion"

    def __init__(self) -> None:
        self.endpoint = REMOTE_IMAGE_PROVIDER_URL.strip()
        self.model = (REMOTE_IMAGE_MODEL or "stable-diffusion").strip()
        self.timeout_seconds = REMOTE_IMAGE_PROVIDER_TIMEOUT
        self.max_retries = max(1, REMOTE_IMAGE_PROVIDER_RETRIES)
        if not self.endpoint:
            raise ImageGenerationError(
                "Remote image provider is not configured. Set REMOTE_IMAGE_PROVIDER_URL and REMOTE_IMAGE_MODEL in backend/.env."
            )

    @staticmethod
    def _to_sd_size(aspect_ratio: str) -> tuple[int, int]:
        mapping = {
            "1:1": (1024, 1024),
            "16:9": (1536, 1024),
            "9:16": (1024, 1536),
            "4:3": (1024, 768),
            "3:4": (768, 1024),
        }
        return mapping.get(aspect_ratio, (1024, 1024))

    def _normalize_prompt(self, prompt: str, style: str, negative_prompt: str | None) -> str:
        style_prompt = STYLE_PROMPTS.get(style, style or "cinematic")
        if negative_prompt and negative_prompt.strip():
            return f"{style_prompt}. {prompt}. Negative prompt: {negative_prompt.strip()}"
        return f"{style_prompt}. {prompt}"

    def _request_payload(self, prompt: str, style: str, aspect_ratio: str, quality: str, negative_prompt: str | None) -> dict[str, Any]:
        width, height = self._to_sd_size(aspect_ratio)
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": self._normalize_prompt(prompt, style, negative_prompt),
            "negative_prompt": negative_prompt.strip() if negative_prompt and negative_prompt.strip() else "",
            "width": width,
            "height": height,
            "steps": 28 if quality == "high" else 22 if quality == "medium" else 18,
            "guidance_scale": 7.5 if quality != "low" else 6.5,
            "num_images": 1,
        }
        return payload

    def _extract_image_url(self, payload: Any) -> str | None:
        if isinstance(payload, dict):
            for key in ("image_url", "url", "image", "output_url"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    return value
            for key in ("images", "data"):
                value = payload.get(key)
                if isinstance(value, list) and value:
                    first = value[0]
                    if isinstance(first, dict):
                        for nested_key in ("image_url", "url", "image", "output_url"):
                            nested_value = first.get(nested_key)
                            if isinstance(nested_value, str) and nested_value:
                                return nested_value
            for key in ("image_base64", "base64"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    return value
        return None

    def _request_generation(self, payload: dict[str, Any]) -> Any:
        headers = {"Content-Type": "application/json"}
        if REMOTE_IMAGE_PROVIDER_API_KEY:
            headers["Authorization"] = f"Bearer {REMOTE_IMAGE_PROVIDER_API_KEY}"

        request_payload = json.dumps(payload).encode("utf-8")
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                req = urllib_request.Request(self.endpoint, data=request_payload, headers=headers, method="POST")
                with urllib_request.urlopen(req, timeout=self.timeout_seconds) as response:
                    body = response.read()
                    if not body:
                        raise ImageGenerationError("Remote image provider returned an empty response.")
                    try:
                        return json.loads(body.decode("utf-8"))
                    except json.JSONDecodeError:
                        return body
            except (urllib_error.HTTPError, urllib_error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(min(2.0 * attempt, 4.0))
                    continue
                if isinstance(exc, urllib_error.HTTPError):
                    try:
                        error_body = exc.read().decode("utf-8", errors="replace")
                    except Exception:
                        error_body = str(exc)
                    raise ImageGenerationError(f"Remote image provider failed with HTTP {exc.code}: {error_body}") from exc
                raise ImageGenerationError(f"Remote image provider request failed: {exc}") from exc

        if last_error is not None:
            raise ImageGenerationError(f"Remote image provider failed after {self.max_retries} attempts: {last_error}")

        raise ImageGenerationError("Remote image provider failed without a response.")

    def generate(
        self,
        prompt: str,
        style: str,
        aspect_ratio: str,
        quality: str,
        negative_prompt: str | None = None,
    ) -> tuple[str, str]:
        payload = self._request_payload(prompt, style, aspect_ratio, quality, negative_prompt)

        try:
            response = self._request_generation(payload)
        except ImageGenerationError:
            raise
        except Exception as exc:
            raise ImageGenerationError(f"Remote image generation failed unexpectedly: {exc}") from exc

        if isinstance(response, (bytes, bytearray)):
            image_bytes = bytes(response)
            return save_image_from_base64(base64.b64encode(image_bytes).decode("utf-8")), "base64"

        image_url = self._extract_image_url(response)
        if not image_url:
            raise ImageGenerationError("Remote image provider did not return a valid image response.")

        if image_url.startswith("data:image"):
            encoded = image_url.split(",", 1)[1]
            return save_image_from_base64(encoded), "base64"

        if image_url.startswith("http://") or image_url.startswith("https://"):
            return save_image_from_url(image_url), "url"

        if image_url.startswith("/"):
            absolute_url = self.endpoint.rsplit("/", 1)[0] + image_url
            return save_image_from_url(absolute_url), "url"

        raise ImageGenerationError("Remote image provider returned an unsupported image response format.")


def get_active_image_provider() -> ImageProvider:
    try:
        from app.config import IMAGE_PROVIDER
    except ImportError:
        IMAGE_PROVIDER = "remote_stable_diffusion"

    provider_name = (IMAGE_PROVIDER or "remote_stable_diffusion").strip().lower()

    if provider_name in {"openai", "paid_openai"}:
        if not OPENAI_API_KEY:
            raise ImageGenerationError("OpenAI image generation is not configured. Set OPENAI_API_KEY or switch IMAGE_PROVIDER to cloudflare_workers_ai.")
        return OpenAIImageProvider()

    if provider_name in {"cloudflare_workers_ai", "cloudflare", "workers_ai"}:
        if not CLOUDFLARE_API_TOKEN or not CLOUDFLARE_ACCOUNT_ID:
            raise ImageGenerationError(
                "Cloudflare Workers AI is not configured. Set CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID in backend/.env."
            )
        return CloudflareWorkersAIProvider()

    if provider_name in {"remote_stable_diffusion", "stable_diffusion", "remote_sd"}:
        if not REMOTE_IMAGE_PROVIDER_URL:
            raise ImageGenerationError(
                "No remote Stable Diffusion provider is configured. Set REMOTE_IMAGE_PROVIDER_URL and REMOTE_IMAGE_MODEL in backend/.env."
            )
        return RemoteStableDiffusionProvider()

    raise ImageGenerationError(
        f"Unsupported image provider '{provider_name}'. Supported values: openai, cloudflare_workers_ai, remote_stable_diffusion."
    )
