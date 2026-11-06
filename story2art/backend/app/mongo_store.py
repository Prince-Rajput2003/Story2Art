import uuid
from datetime import datetime

from pymongo import MongoClient

from app.config import DEFAULT_SUBSCRIPTION_PLANS, MONGODB_DATABASE, MONGODB_URI, WELCOME_CREDITS

client = MongoClient(MONGODB_URI) if MONGODB_URI else None
db = client[MONGODB_DATABASE] if client else None


def use_mongodb() -> bool:
    return client is not None and db is not None


def ensure_indexes() -> None:
    if not use_mongodb():
        return

    db.users.create_index("email", unique=True)
    db.credit_wallets.create_index("user_id", unique=True)
    db.generated_images.create_index("user_id")
    db.subscription_plans.create_index("slug", unique=True)
    db.payments.create_index("user_id")


def seed_default_plans() -> None:
    if not use_mongodb():
        return

    if db.subscription_plans.count_documents({}) > 0:
        return

    for plan in DEFAULT_SUBSCRIPTION_PLANS:
        db.subscription_plans.insert_one(
            {
                "id": uuid.uuid4().hex,
                "slug": plan["slug"],
                "name": plan["name"],
                "monthly_credits": plan["monthly_credits"],
                "yearly_credits": plan["yearly_credits"],
                "price_monthly": plan["price_monthly"],
                "price_yearly": plan["price_yearly"],
                "features": ",".join(plan["features"]),
                "is_active": True,
                "created_at": datetime.utcnow(),
            }
        )


def find_user_by_email(email: str):
    if not use_mongodb():
        return None
    return db.users.find_one({"email": email.lower()})


def find_user_by_id(user_id: str):
    if not use_mongodb():
        return None
    return db.users.find_one({"id": user_id})


def create_user_record(name: str, email: str, password_hash: str, role: str = "user"):
    if not use_mongodb():
        return None

    user_id = uuid.uuid4().hex
    user = {
        "id": user_id,
        "name": name.strip(),
        "email": email.lower(),
        "password_hash": password_hash,
        "role": role,
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    db.users.insert_one(user)

    db.user_profiles.insert_one(
        {
            "user_id": user_id,
            "avatar_url": None,
            "bio": "",
            "country": "IN",
            "timezone": "UTC",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )

    db.credit_wallets.insert_one(
        {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "balance": WELCOME_CREDITS,
            "monthly_limit": WELCOME_CREDITS,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )

    db.credit_transactions.insert_one(
        {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "amount": WELCOME_CREDITS,
            "kind": "welcome",
            "description": "Welcome credits for new account",
            "reference_id": "welcome-bonus",
            "created_at": datetime.utcnow(),
        }
    )

    return user


def get_user_wallet(user_id: str):
    if not use_mongodb():
        return None
    return db.credit_wallets.find_one({"user_id": user_id})


def get_user_profile(user_id: str):
    if not use_mongodb():
        return None
    return db.user_profiles.find_one({"user_id": user_id})


def update_user_profile(user_id: str, profile_updates: dict):
    if not use_mongodb():
        return None
    db.user_profiles.update_one({"user_id": user_id}, {"$set": {**profile_updates, "updated_at": datetime.utcnow()}})
    return db.user_profiles.find_one({"user_id": user_id})


def save_generated_image(image_data: dict):
    if not use_mongodb():
        return None
    record = {
        **image_data,
        "id": image_data.get("id") or uuid.uuid4().hex,
        "favorite": bool(image_data.get("favorite", False)),
        "created_at": image_data.get("created_at") or datetime.utcnow(),
    }
    db.generated_images.insert_one(record)
    return record


def list_generated_images_for_user(user_id: str):
    if not use_mongodb():
        return []
    return list(db.generated_images.find({"user_id": user_id}).sort("created_at", -1))


def get_generated_image_by_id(image_id: str, user_id: str):
    if not use_mongodb():
        return None
    return db.generated_images.find_one({"id": image_id, "user_id": user_id})


def delete_generated_image(image_id: str, user_id: str):
    if not use_mongodb():
        return False
    result = db.generated_images.delete_one({"id": image_id, "user_id": user_id})
    return result.deleted_count > 0


def get_or_create_wallet(user_id: str):
    if not use_mongodb():
        return None
    wallet = db.credit_wallets.find_one({"user_id": user_id})
    if wallet is None:
        wallet = {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "balance": 0,
            "monthly_limit": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        db.credit_wallets.insert_one(wallet)
    return wallet


def add_credit_transaction(user_id: str, amount: int, kind: str, description: str, reference_id: str | None = None):
    if not use_mongodb():
        return None
    return db.credit_transactions.insert_one(
        {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "amount": int(amount),
            "kind": kind,
            "description": description,
            "reference_id": reference_id,
            "created_at": datetime.utcnow(),
        }
    )


def adjust_wallet_balance(user_id: str, amount: int):
    if not use_mongodb():
        return None
    wallet = get_or_create_wallet(user_id)
    new_balance = int(wallet.get("balance", 0)) + int(amount)
    db.credit_wallets.update_one({"user_id": user_id}, {"$set": {"balance": new_balance, "updated_at": datetime.utcnow()}})
    return db.credit_wallets.find_one({"user_id": user_id})


def list_subscription_plans():
    if not use_mongodb():
        return []
    return list(db.subscription_plans.find({"is_active": True}).sort("price_monthly", 1))


def find_plan_by_id(plan_id: str):
    if not use_mongodb():
        return None
    return db.subscription_plans.find_one({"id": plan_id, "is_active": True})


def add_payment_record(record: dict):
    if not use_mongodb():
        return None
    payload = {**record, "id": record.get("id") or uuid.uuid4().hex, "created_at": record.get("created_at") or datetime.utcnow()}
    db.payments.insert_one(payload)
    return payload


def list_payments_for_user(user_id: str):
    if not use_mongodb():
        return []
    return list(db.payments.find({"user_id": user_id}).sort("created_at", -1))


def list_all_users():
    if not use_mongodb():
        return []
    return list(db.users.find().sort("created_at", -1))


def add_admin_log(admin_user_id: str, action: str, details: str | None = None):
    if not use_mongodb():
        return None
    return db.admin_logs.insert_one(
        {"id": uuid.uuid4().hex, "admin_user_id": admin_user_id, "action": action, "details": details, "created_at": datetime.utcnow()}
    )


def list_users():
    if not use_mongodb():
        return []
    return list(db.users.find().sort("created_at", -1))


def count_documents(collection_name: str):
    if not use_mongodb():
        return 0
    return db[collection_name].count_documents({})
