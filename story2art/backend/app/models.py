import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    token_version = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    wallet = relationship("CreditWallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    images = relationship("GeneratedImage", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    credit_transactions = relationship("CreditTransaction", back_populates="user", cascade="all, delete-orphan")
    admin_logs = relationship("AdminActivityLog", back_populates="admin_user", cascade="all, delete-orphan")


class PasswordResetChallenge(Base):
    __tablename__ = "password_reset_challenges"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    email_digest = Column(String(64), unique=True, index=True, nullable=False)
    otp_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_sent_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    reset_token_hash = Column(String(64), nullable=True)
    reset_token_expires_at = Column(DateTime, nullable=True)
    consumed_at = Column(DateTime, nullable=True)


class PasswordResetRateLimit(Base):
    __tablename__ = "password_reset_rate_limits"

    key_hash = Column(String(64), primary_key=True)
    window_started_at = Column(DateTime, index=True, nullable=False)
    request_count = Column(Integer, default=0, nullable=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    avatar_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    country = Column(String(80), default="IN")
    timezone = Column(String(80), default="UTC")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="profile")


class CreditWallet(Base):
    __tablename__ = "credit_wallets"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Integer, default=0, nullable=False)
    monthly_limit = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="wallet")


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    kind = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    reference_id = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="credit_transactions")


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(80), nullable=False)
    monthly_credits = Column(Integer, default=0, nullable=False)
    yearly_credits = Column(Integer, default=0, nullable=False)
    price_monthly = Column(Integer, default=0, nullable=False)
    price_yearly = Column(Integer, default=0, nullable=False)
    features = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    subscriptions = relationship("UserSubscription", back_populates="plan")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    plan_id = Column(String, ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(String(30), default="active", nullable=False)
    billing_cycle = Column(String(20), default="monthly", nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(String, ForeignKey("user_subscriptions.id"), nullable=True)
    plan_id = Column(String, ForeignKey("subscription_plans.id"), nullable=True)
    amount = Column(Integer, default=0, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    gateway = Column(String(50), default="razorpay", nullable=False)
    status = Column(String(30), default="pending", nullable=False)
    order_id = Column(String(120), nullable=True)
    payment_id = Column(String(120), nullable=True)
    signature = Column(String(255), nullable=True)
    payment_metadata = Column("metadata", Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="payments")
    subscription = relationship("UserSubscription", back_populates="payments")


class AdminActivityLog(Base):
    __tablename__ = "admin_activity_logs"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    admin_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    action = Column(String(120), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    admin_user = relationship("User", back_populates="admin_logs")


class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    original_story = Column(Text, nullable=False)
    enhanced_prompt = Column(Text, nullable=False)
    image_style = Column(String(100), nullable=False)
    aspect_ratio = Column(String(20), nullable=False)
    quality = Column(String(20), nullable=False, default="medium")
    filename = Column(String(255), nullable=False, unique=True)
    favorite = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="images")
