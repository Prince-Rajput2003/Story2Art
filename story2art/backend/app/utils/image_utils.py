import base64
import hashlib
import io
import os
import uuid
from pathlib import Path
from urllib.request import urlopen

from PIL import Image

from app.config import GENERATED_IMAGES_DIR


def _safe_filename(name: str) -> str:
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    safe_stem = "".join(ch for ch in stem if ch.isalnum() or ch in {"-", "_"}) or "story"
    return f"{safe_stem}-{uuid.uuid4().hex[:8]}{suffix if suffix else '.png'}"


def save_image_from_base64(base64_data: str) -> str:
    image_bytes = base64.b64decode(base64_data)
    file_name = _safe_filename("generated_image.png")
    target_path = GENERATED_IMAGES_DIR / file_name

    if target_path.exists():
        file_name = _safe_filename("generated_image.png")
        target_path = GENERATED_IMAGES_DIR / file_name

    with open(target_path, "wb") as image_file:
        image_file.write(image_bytes)

    with Image.open(io.BytesIO(image_bytes)) as img:
        img.verify()

    return file_name


def save_image_from_url(image_url: str) -> str:
    file_name = _safe_filename("generated_image.png")
    target_path = GENERATED_IMAGES_DIR / file_name
    if target_path.exists():
        file_name = _safe_filename("generated_image.png")
        target_path = GENERATED_IMAGES_DIR / file_name

    response = urlopen(image_url)
    image_bytes = response.read()
    with open(target_path, "wb") as image_file:
        image_file.write(image_bytes)

    with Image.open(io.BytesIO(image_bytes)) as img:
        img.verify()

    return file_name


def get_image_mime_type(image_bytes: bytes) -> str:
    with Image.open(io.BytesIO(image_bytes)) as img:
        mime_type = Image.MIME.get(img.format)
    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError("Generated file is not a supported image format.")
    return mime_type


def image_to_data_url(filename: str) -> str:
    image_bytes = (GENERATED_IMAGES_DIR / filename).read_bytes()
    mime_type = get_image_mime_type(image_bytes)
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded_image}"


def remove_image_file(filename: str) -> None:
    path = GENERATED_IMAGES_DIR / filename
    if path.exists() and path.is_file():
        path.unlink()
