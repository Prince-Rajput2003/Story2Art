import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from app.config import (
    JWT_SECRET,
    PASSWORD_RESET_EMAIL_LIMIT_PER_HOUR,
    PASSWORD_RESET_IP_LIMIT_PER_HOUR,
    WELCOME_CREDITS,
)
from app.database import get_db
from app.models import (
    CreditTransaction,
    CreditWallet,
    PasswordResetChallenge,
    PasswordResetRateLimit,
    User,
    UserProfile,
)
from app.services.auth_service import create_access_token, get_current_user, hash_password, verify_password
from app.services.email_service import (
    EmailDeliveryError,
    is_password_reset_email_configured,
    send_password_reset_email,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

OTP_EXPIRATION = timedelta(minutes=5)
RESET_AUTHORIZATION_EXPIRATION = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=60)
RATE_LIMIT_WINDOW = timedelta(hours=1)
MAX_EMAIL_REQUESTS_PER_HOUR = PASSWORD_RESET_EMAIL_LIMIT_PER_HOUR
MAX_IP_REQUESTS_PER_HOUR = PASSWORD_RESET_IP_LIMIT_PER_HOUR
MAX_OTP_ATTEMPTS = 5
RESET_REQUEST_MESSAGE = "If an account exists for this email, password reset instructions will be sent."


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., pattern=r"^\d{6}$")


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(..., min_length=32, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=72)
    confirm_password: str = Field(..., min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be no more than 72 UTF-8 bytes.")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain an uppercase letter.")
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain a lowercase letter.")
        if not any(char.isdecimal() for char in value):
            raise ValueError("Password must contain a number.")
        if not any(not char.isalnum() and not char.isspace() for char in value):
            raise ValueError("Password must contain a special character.")
        return value

    @model_validator(mode="after")
    def validate_password_confirmation(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    bio: str | None = None
    country: str | None = None
    timezone: str | None = None


def _keyed_digest(purpose: str, value: str) -> str:
    if len(JWT_SECRET) < 32 or JWT_SECRET in {
        "story2art-dev-secret-change-me",
        "replace-with-a-random-secret-of-at-least-32-characters",
    }:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset is temporarily unavailable. Configure a strong JWT_SECRET and try again.",
        )
    return hmac.new(
        JWT_SECRET.encode("utf-8"),
        f"{purpose}:{value}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _consume_request_limits(db: Session, email_digest: str, client_ip: str, now: datetime) -> bool:
    db.query(PasswordResetRateLimit).filter(
        PasswordResetRateLimit.window_started_at < now - RATE_LIMIT_WINDOW
    ).delete(synchronize_session=False)

    buckets = (
        (_keyed_digest("rate-email", email_digest), MAX_EMAIL_REQUESTS_PER_HOUR),
        (_keyed_digest("rate-ip", client_ip), MAX_IP_REQUESTS_PER_HOUR),
    )
    existing = {
        key: db.query(PasswordResetRateLimit).filter(PasswordResetRateLimit.key_hash == key).first()
        for key, _ in buckets
    }

    for key, max_requests in buckets:
        bucket = existing[key]
        if bucket and now - bucket.window_started_at < RATE_LIMIT_WINDOW and bucket.request_count >= max_requests:
            return False

    for key, _ in buckets:
        bucket = existing[key]
        if bucket is None:
            db.add(PasswordResetRateLimit(key_hash=key, window_started_at=now, request_count=1))
        elif now - bucket.window_started_at >= RATE_LIMIT_WINDOW:
            bucket.window_started_at = now
            bucket.request_count = 1
        else:
            bucket.request_count += 1
    return True


def _request_password_reset(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session,
) -> dict[str, str]:
    now = _utcnow()
    email = str(payload.email).strip().lower()
    email_digest = _keyed_digest("reset-email", email)
    client_ip = request.client.host if request.client else "unknown"

    if not is_password_reset_email_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset email is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL in backend/.env.",
        )

    challenge = (
        db.query(PasswordResetChallenge)
        .filter(PasswordResetChallenge.email_digest == email_digest)
        .first()
    )
    if challenge and challenge.last_sent_at and now - challenge.last_sent_at < RESEND_COOLDOWN:
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait 60 seconds before requesting another code.",
        )

    if not _consume_request_limits(db, email_digest, client_ip, now):
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please try again later.",
        )

    user = db.query(User).filter(User.email == email).first()
    if challenge is None:
        challenge = PasswordResetChallenge(email_digest=email_digest)
        db.add(challenge)
        db.flush()

    challenge.user_id = user.id if user and user.is_active else None
    challenge.otp_hash = None
    challenge.created_at = now
    challenge.expires_at = now + OTP_EXPIRATION
    challenge.last_sent_at = now
    challenge.attempts = 0
    challenge.verified_at = None
    challenge.reset_token_hash = None
    challenge.reset_token_expires_at = None
    challenge.consumed_at = None

    otp = f"{secrets.randbelow(1_000_000):06d}"
    if challenge.user_id:
        challenge.otp_hash = _keyed_digest("reset-otp", f"{challenge.id}:{otp}")

    db.commit()

    if challenge.user_id:
        try:
            send_password_reset_email(email, otp)
        except EmailDeliveryError as exc:
            challenge.otp_hash = None
            challenge.expires_at = None
            challenge.last_sent_at = None
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Password reset email could not be delivered. Check the SMTP settings and try again.",
            ) from exc

    return {"message": RESET_REQUEST_MESSAGE}


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
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    return _request_password_reset(payload, request, db)


@router.post("/resend-otp")
def resend_password_reset_otp(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    return _request_password_reset(payload, request, db)


@router.post("/verify-otp")
def verify_password_reset_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    email_digest = _keyed_digest("reset-email", str(payload.email).strip().lower())
    challenge = (
        db.query(PasswordResetChallenge)
        .filter(PasswordResetChallenge.email_digest == email_digest)
        .first()
    )
    now = _utcnow()
    if (
        not challenge
        or not challenge.user_id
        or not challenge.otp_hash
        or not challenge.expires_at
        or challenge.expires_at <= now
        or challenge.consumed_at
        or challenge.attempts >= MAX_OTP_ATTEMPTS
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification code.")

    candidate_hash = _keyed_digest("reset-otp", f"{challenge.id}:{payload.otp}")
    if not hmac.compare_digest(challenge.otp_hash, candidate_hash):
        challenge.attempts += 1
        if challenge.attempts >= MAX_OTP_ATTEMPTS:
            challenge.otp_hash = None
            challenge.expires_at = None
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification code.")

    reset_token = secrets.token_urlsafe(32)
    challenge.otp_hash = None
    challenge.expires_at = None
    challenge.verified_at = now
    challenge.reset_token_hash = _keyed_digest("reset-token", reset_token)
    challenge.reset_token_expires_at = now + RESET_AUTHORIZATION_EXPIRATION
    db.commit()
    return {
        "message": "Email verified. You can now reset your password.",
        "reset_token": reset_token,
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_hash = _keyed_digest("reset-token", payload.reset_token)
    challenge = (
        db.query(PasswordResetChallenge)
        .filter(PasswordResetChallenge.reset_token_hash == token_hash)
        .first()
    )
    now = _utcnow()
    if (
        not challenge
        or not challenge.user_id
        or not challenge.verified_at
        or not challenge.reset_token_expires_at
        or challenge.reset_token_expires_at <= now
        or challenge.consumed_at
        or not hmac.compare_digest(challenge.reset_token_hash, token_hash)
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset authorization.")

    user = db.query(User).filter(User.id == challenge.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset authorization.")

    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    for active_challenge in (
        db.query(PasswordResetChallenge)
        .filter(PasswordResetChallenge.user_id == user.id)
        .all()
    ):
        active_challenge.otp_hash = None
        active_challenge.expires_at = None
        active_challenge.reset_token_hash = None
        active_challenge.reset_token_expires_at = None
        active_challenge.consumed_at = now
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
def logout_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.token_version += 1
    db.commit()
    return {"message": "Logged out successfully."}
