from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CreditTransaction, CreditWallet, GeneratedImage, Payment, SubscriptionPlan, User, UserSubscription
from app.services.auth_service import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
def admin_dashboard(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()
    total_images = db.query(GeneratedImage).count()
    total_credits_consumed = db.query(CreditTransaction).with_entities(func.coalesce(func.sum(CreditTransaction.amount), 0)).scalar() or 0
    total_revenue = db.query(Payment).with_entities(func.coalesce(func.sum(Payment.amount), 0)).scalar() or 0
    plans = db.query(SubscriptionPlan).count()

    return {
        "summary": {
            "total_users": total_users,
            "active_users": active_users,
            "total_images": total_images,
            "total_credits_consumed": abs(int(total_credits_consumed)),
            "total_revenue": int(total_revenue),
            "subscription_plans": plans,
        }
    }


@router.get("/users")
def list_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "credits": (user.wallet.balance if user.wallet else 0),
        }
        for user in users
    ]


@router.post("/users/{user_id}/toggle-status")
def toggle_user_status(user_id: str, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User status updated to {'active' if user.is_active else 'disabled'}."}


@router.post("/users/{user_id}/role")
def update_user_role(user_id: str, payload: dict, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    role = payload.get("role", "user").lower()
    if role not in {"user", "admin"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be user or admin.")
    user.role = role
    db.commit()
    return {"message": "User role updated successfully."}


@router.post("/users/{user_id}/credits")
def admin_adjust_credit(user_id: str, payload: dict, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    amount = int(payload.get("amount", 0))
    if amount == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credit adjustment must be non-zero.")

    wallet = user.wallet or CreditWallet(user_id=user.id, balance=0, monthly_limit=0)
    wallet.balance += amount
    db.add(wallet)
    db.add(CreditTransaction(user_id=user.id, amount=amount, kind="admin_adjustment", description=f"Admin adjusted credits by {amount}", reference_id="admin-adjustment"))
    db.commit()
    return {"message": "Credits updated successfully.", "balance": wallet.balance}


@router.get("/payments")
def payment_records(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    records = db.query(Payment).order_by(Payment.created_at.desc()).all()
    return [
        {
            "id": payment.id,
            "user_id": payment.user_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "gateway": payment.gateway,
            "order_id": payment.order_id,
            "created_at": payment.created_at.isoformat(),
        }
        for payment in records
    ]
