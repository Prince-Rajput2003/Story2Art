import hashlib
import hmac
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, DEFAULT_SUBSCRIPTION_PLANS
from app.database import get_db
from app.models import Payment, SubscriptionPlan, User, UserSubscription
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api", tags=["billing"])


class SubscribeRequest(BaseModel):
    plan_id: str
    billing_cycle: str = "monthly"


class VerifyPaymentRequest(BaseModel):
    payment_id: str = Field(..., min_length=1)
    order_id: str = Field(..., min_length=1)
    signature: str = Field(..., min_length=1)
    plan_id: str = Field(..., min_length=1)
    test_mode: bool = False


@router.get("/plans")
def list_plans(db: Session = Depends(get_db)):
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active.is_(True)).order_by(SubscriptionPlan.price_monthly.asc()).all()
    return [
        {
            "id": plan.id,
            "slug": plan.slug,
            "name": plan.name,
            "monthly_credits": plan.monthly_credits,
            "yearly_credits": plan.yearly_credits,
            "price_monthly": plan.price_monthly,
            "price_yearly": plan.price_yearly,
            "features": (plan.features or "").split(",") if plan.features else [],
        }
        for plan in plans
    ]


@router.post("/subscriptions/checkout")
def create_subscription_checkout(payload: SubscribeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == payload.plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found.")

    amount = plan.price_monthly if payload.billing_cycle == "monthly" else plan.price_yearly
    order_id = f"story2art_{current_user.id}_{payload.billing_cycle}_{int(datetime.utcnow().timestamp())}"
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        return {
            "order_id": order_id,
            "amount": amount,
            "currency": "INR",
            "gateway": "razorpay",
            "test_mode": False,
            "message": "Razorpay test credentials are configured. Complete the payment flow in the configured gateway.",
        }

    return {
        "order_id": order_id,
        "amount": amount,
        "currency": "INR",
        "gateway": "test-mode",
        "test_mode": True,
        "message": "Payment is running in backend test mode because Razorpay credentials are not configured.",
    }


@router.post("/payments/verify")
def verify_payment(payload: VerifyPaymentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == payload.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    verified = False
    if payload.test_mode:
        verified = True
    elif RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        expected = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            f"{payload.order_id}|{payload.payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        verified = hmac.compare_digest(expected, payload.signature)

    if not verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment signature verification failed.")

    subscription = UserSubscription(
        user_id=current_user.id,
        plan_id=plan.id,
        status="active",
        billing_cycle="monthly",
        started_at=datetime.utcnow(),
        auto_renew=True,
        expires_at=datetime.utcnow(),
    )
    db.add(subscription)
    db.flush()

    payment = Payment(
        user_id=current_user.id,
        subscription_id=subscription.id,
        plan_id=plan.id,
        amount=plan.price_monthly,
        currency="INR",
        gateway="razorpay" if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET else "test-mode",
        status="paid",
        order_id=payload.order_id,
        payment_id=payload.payment_id,
        signature=payload.signature,
        payment_metadata='{"verified": true, "test_mode": true}' if payload.test_mode else '{"verified": true}',
    )
    db.add(payment)
    db.commit()
    return {"message": "Payment verified successfully.", "status": "paid", "plan": plan.name}


@router.get("/payments/history")
def payment_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payments = db.query(Payment).filter(Payment.user_id == current_user.id).order_by(Payment.created_at.desc()).all()
    return [
        {
            "id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "gateway": payment.gateway,
            "status": payment.status,
            "order_id": payment.order_id,
            "created_at": payment.created_at.isoformat(),
        }
        for payment in payments
    ]
