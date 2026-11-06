import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env", override=True)

GENERATED_IMAGES_DIR = BASE_DIR / "generated_images"
GENERATED_IMAGES_DIR.mkdir(exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-image-1").strip()
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
CLOUDFLARE_IMAGE_MODEL = os.getenv("CLOUDFLARE_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell").strip()
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "cloudflare_workers_ai").strip().lower()
REMOTE_IMAGE_PROVIDER_URL = os.getenv("REMOTE_IMAGE_PROVIDER_URL", "").strip()
REMOTE_IMAGE_MODEL = os.getenv("REMOTE_IMAGE_MODEL", "stable-diffusion-v1-5").strip()
REMOTE_IMAGE_PROVIDER_TIMEOUT = float(os.getenv("REMOTE_IMAGE_PROVIDER_TIMEOUT", "30"))
REMOTE_IMAGE_PROVIDER_RETRIES = int(os.getenv("REMOTE_IMAGE_PROVIDER_RETRIES", "2"))
REMOTE_IMAGE_PROVIDER_API_KEY = os.getenv("REMOTE_IMAGE_PROVIDER_API_KEY", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./story2art.db").strip()
MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", os.getenv("MONGODB_DB_NAME", "story2art")).strip()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").strip()
JWT_SECRET = os.getenv("JWT_SECRET", "story2art-dev-secret-change-me").strip()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip()
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
WELCOME_CREDITS = int(os.getenv("WELCOME_CREDITS", "25"))
DEFAULT_CREDIT_COST = int(os.getenv("DEFAULT_CREDIT_COST", "5"))
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "").strip()
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "").strip()

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    FRONTEND_URL,
    "*",
]

MAX_STORY_LENGTH = 2500
MIN_STORY_LENGTH = 20

IMAGE_STYLE_OPTIONS = [
    "Realistic Photography",
    "Cinematic",
    "Anime",
    "3D Render",
    "Digital Art",
    "Fantasy",
    "Oil Painting",
    "Watercolor",
    "Cartoon",
    "Cyberpunk",
    "Minimalist",
    "Portrait Photography",
    "Architecture",
    "Landscape",
]

ASPECT_RATIO_OPTIONS = ["1:1", "16:9", "9:16", "4:3", "3:4"]
QUALITY_OPTIONS = {"low": "low", "medium": "medium", "high": "high"}

DEFAULT_SUBSCRIPTION_PLANS = [
    {
        "slug": "free",
        "name": "Free",
        "monthly_credits": 25,
        "yearly_credits": 300,
        "price_monthly": 0.0,
        "price_yearly": 0.0,
        "features": ["Limited monthly credits", "Standard generation", "Personal gallery"],
    },
    {
        "slug": "basic",
        "name": "Basic",
        "monthly_credits": 200,
        "yearly_credits": 2400,
        "price_monthly": 399,
        "price_yearly": 3990,
        "features": ["More monthly credits", "All standard styles", "Priority support"],
    },
    {
        "slug": "pro",
        "name": "Pro",
        "monthly_credits": 600,
        "yearly_credits": 7200,
        "price_monthly": 999,
        "price_yearly": 9990,
        "features": ["Higher monthly credits", "Advanced options", "Priority generation"],
    },
    {
        "slug": "premium",
        "name": "Premium",
        "monthly_credits": 2000,
        "yearly_credits": 24000,
        "price_monthly": 1999,
        "price_yearly": 19990,
        "features": ["Max credits", "Premium features", "Dedicated support"],
    },
]
