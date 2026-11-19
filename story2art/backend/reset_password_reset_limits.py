import os

from app.config import APP_ENV, DATABASE_URL
from app.database import SessionLocal
from app.models import PasswordResetRateLimit


def main() -> None:
    if APP_ENV != "development" or os.getenv("APP_ENV", "").strip().lower() != "development":
        raise SystemExit("Refusing to clear rate limits unless APP_ENV=development is explicitly set.")
    if not DATABASE_URL.startswith("sqlite:"):
        raise SystemExit("Refusing to clear rate limits in a non-SQLite database.")

    db = SessionLocal()
    try:
        deleted = db.query(PasswordResetRateLimit).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"Cleared {deleted} development password-reset rate-limit record(s).")


if __name__ == "__main__":
    main()
