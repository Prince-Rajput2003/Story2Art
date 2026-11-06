from datetime import datetime

from sqlalchemy.orm import Session

from app.config import DEFAULT_CREDIT_COST, IMAGE_STYLE_OPTIONS
from app.models import CreditTransaction, CreditWallet, User


def get_credit_cost(style: str, quality: str) -> int:
    style_bonus = 0
    if style in {"Realistic Photography", "Cinematic", "Architecture", "Landscape"}:
        style_bonus = 2
    elif style in {"3D Render", "Cyberpunk", "Fantasy"}:
        style_bonus = 3

    quality_cost = {"low": 1, "medium": 2, "high": 3}.get((quality or "medium").lower(), 2)
    return max(DEFAULT_CREDIT_COST, DEFAULT_CREDIT_COST + style_bonus + quality_cost)


def get_or_create_wallet(db: Session, user: User) -> CreditWallet:
    wallet = user.wallet or db.query(CreditWallet).filter(CreditWallet.user_id == user.id).first()
    if wallet is None:
        wallet = CreditWallet(user_id=user.id, balance=0, monthly_limit=0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet


def add_credits(db: Session, user: User, amount: int, kind: str, description: str, reference_id: str | None = None) -> CreditWallet:
    wallet = get_or_create_wallet(db, user)
    wallet.balance += int(amount)
    wallet.updated_at = datetime.utcnow()
    db.add(CreditTransaction(user_id=user.id, amount=int(amount), kind=kind, description=description, reference_id=reference_id))
    db.commit()
    db.refresh(wallet)
    return wallet


def deduct_credits(db: Session, user: User, amount: int, kind: str, description: str, reference_id: str | None = None) -> CreditWallet:
    wallet = get_or_create_wallet(db, user)
    if wallet.balance < amount:
        raise ValueError("Insufficient credits for this generation.")
    wallet.balance -= int(amount)
    wallet.updated_at = datetime.utcnow()
    db.add(CreditTransaction(user_id=user.id, amount=-int(amount), kind=kind, description=description, reference_id=reference_id))
    db.commit()
    db.refresh(wallet)
    return wallet


def refund_credits(db: Session, user: User, amount: int, kind: str, description: str, reference_id: str | None = None) -> CreditWallet:
    return add_credits(db, user, amount, kind, description, reference_id)
