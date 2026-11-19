from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL, DEFAULT_SUBSCRIPTION_PLANS, MONGODB_DATABASE, MONGODB_URI
from app.mongo_store import ensure_indexes, seed_default_plans as seed_mongo_plans, use_mongodb

engine_options = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def migrate_legacy_sqlite_schema() -> None:
    if use_mongodb():
        return

    if DATABASE_URL.startswith("sqlite"):
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        with engine.begin() as connection:
            if "users" in tables:
                user_columns = {column["name"] for column in inspector.get_columns("users")}
                if "token_version" not in user_columns:
                    connection.execute(text("ALTER TABLE users ADD COLUMN token_version INTEGER DEFAULT 0 NOT NULL"))

            if "generated_images" in tables:
                image_columns = {column["name"] for column in inspector.get_columns("generated_images")}
                if "user_id" not in image_columns:
                    connection.execute(text("ALTER TABLE generated_images ADD COLUMN user_id VARCHAR"))
                if "favorite" not in image_columns:
                    connection.execute(text("ALTER TABLE generated_images ADD COLUMN favorite BOOLEAN DEFAULT 0 NOT NULL"))


def init_db() -> None:
    if use_mongodb():
        ensure_indexes()
        seed_mongo_plans()
        return

    from app.models import (
        AdminActivityLog,
        CreditTransaction,
        CreditWallet,
        GeneratedImage,
        PasswordResetChallenge,
        PasswordResetRateLimit,
        Payment,
        SubscriptionPlan,
        User,
        UserProfile,
        UserSubscription,
    )

    migrate_legacy_sqlite_schema()
    Base.metadata.create_all(bind=engine)
    seed_default_plans()


def seed_default_plans() -> None:
    from sqlalchemy.orm import Session
    from app.models import SubscriptionPlan

    db = SessionLocal()
    try:
        existing = db.query(SubscriptionPlan).count()
        if existing > 0:
            return

        for plan in DEFAULT_SUBSCRIPTION_PLANS:
            db.add(
                SubscriptionPlan(
                    slug=plan["slug"],
                    name=plan["name"],
                    monthly_credits=plan["monthly_credits"],
                    yearly_credits=plan["yearly_credits"],
                    price_monthly=plan["price_monthly"],
                    price_yearly=plan["price_yearly"],
                    features=",".join(plan["features"]),
                    is_active=True,
                )
            )
        db.commit()
    finally:
        db.close()


def get_db():
    if use_mongodb():
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
