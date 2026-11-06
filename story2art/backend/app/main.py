from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS
from app.database import init_db
from app.routes.admin import router as admin_router
from app.routes.auth import router as auth_router
from app.routes.gallery import router as gallery_router
from app.routes.generate import router as generate_router
from app.routes.health import router as health_router
from app.routes.subscriptions import router as billing_router

app = FastAPI(
    title="Story2Art API",
    description="AI-powered story-to-image generation API and SaaS platform",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(generate_router)
app.include_router(gallery_router)
app.include_router(billing_router)
app.include_router(admin_router)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def read_root():
    return {"message": "Welcome to Story2Art API", "status": "online"}
