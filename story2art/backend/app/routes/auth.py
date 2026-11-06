from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.config import WELCOME_CREDITS
from app.database import get_db
from app.models import CreditTransaction, CreditWallet, User, UserProfile
from app.services.auth_service import create_access_token, decode_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=72)


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    bio: str | None = None
    country: str | None = None
    timezone: str | None = None


@router.post("/register")
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists.")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role="user",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.flush()

    profile = UserProfile(user_id=user.id, bio="", country="IN", timezone="UTC")
    wallet = CreditWallet(user_id=user.id, balance=WELCOME_CREDITS, monthly_limit=WELCOME_CREDITS)
    db.add(profile)
    db.add(wallet)

    transaction = CreditTransaction(
        user_id=user.id,
        amount=WELCOME_CREDITS,
        kind="welcome",
        description="Welcome credits for new account",
        reference_id="welcome-bonus",
    )
    db.add(transaction)
    db.commit()
    db.refresh(user)

    token = create_access_token(user)
    return {
        "message": "Registration successful.",
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "credits": wallet.balance,
        },
    }


@router.post("/login")
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is disabled.")

    token = create_access_token(user)
    wallet = db.query(CreditWallet).filter(CreditWallet.user_id == user.id).first()
    return {
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "credits": wallet.balance if wallet else 0,
        },
    }


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        return {"message": "If the email is registered, a password reset link has been generated."}

    token = create_access_token(user)
    return {
        "message": "Password reset instructions were generated for this account.",
        "reset_token": token,
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.token)
        email = decoded.get("sub")
        user = db.query(User).filter(User.email == email).first()
    except Exception:
        user = None

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token.")

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully."}


@router.get("/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    wallet = current_user.wallet
    profile = current_user.profile or UserProfile(user_id=current_user.id)
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "credits": wallet.balance if wallet else 0,
        "profile": {
            "bio": profile.bio or "",
            "country": profile.country or "IN",
            "timezone": profile.timezone or "UTC",
            "avatar_url": profile.avatar_url,
        },
    }


@router.put("/profile")
def update_profile(payload: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = current_user.profile or UserProfile(user_id=current_user.id)
    if payload.name is not None:
        current_user.name = payload.name.strip()
    if payload.bio is not None:
        profile.bio = payload.bio
    if payload.country is not None:
        profile.country = payload.country
    if payload.timezone is not None:
        profile.timezone = payload.timezone

    db.add(profile)
    db.commit()
    return {"message": "Profile updated successfully."}


@router.post("/logout")
def logout_user():
    return {"message": "Logged out successfully."}
