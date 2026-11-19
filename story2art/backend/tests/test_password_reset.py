import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, migrate_legacy_sqlite_schema
from app.main import app
from app.models import PasswordResetChallenge, User
from app.routes.auth import _keyed_digest
from app.services.auth_service import hash_password


class PasswordResetApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        db = self.Session()
        db.add(
            User(
                id="reset-test-user",
                name="Reset Test",
                email="registered@example.com",
                password_hash=hash_password("OldPassword1!"),
                role="user",
                is_active=True,
                token_version=0,
            )
        )
        db.commit()
        db.close()

        def override_get_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.init_db_patch = patch("app.main.init_db")
        self.init_db_patch.start()
        self.session_factory_patch = patch("app.routes.auth.SessionLocal", self.Session)
        self.session_factory_patch.start()
        self.secret_patch = patch("app.routes.auth.JWT_SECRET", "test-only-reset-secret-with-more-than-32-characters")
        self.secret_patch.start()
        self.smtp_config_patches = [
            patch("app.routes.auth.SMTP_HOST", "smtp.test"),
            patch("app.routes.auth.SMTP_FROM_EMAIL", "no-reply@example.com"),
            patch("app.routes.auth.SMTP_USERNAME", ""),
            patch("app.routes.auth.SMTP_PASSWORD", ""),
        ]
        for config_patch in self.smtp_config_patches:
            config_patch.start()
        self.email_patch = patch("app.routes.auth.send_password_reset_email")
        self.send_email = self.email_patch.start()
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)
        app.dependency_overrides.clear()
        self.email_patch.stop()
        for config_patch in reversed(self.smtp_config_patches):
            config_patch.stop()
        self.secret_patch.stop()
        self.session_factory_patch.stop()
        self.init_db_patch.stop()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def request_code(self, email="registered@example.com"):
        response = self.client.post("/api/auth/forgot-password", json={"email": email})
        return response, self.send_email.call_args.args[1] if self.send_email.called else None

    def test_generic_response_and_otp_hash_storage(self):
        registered, otp = self.request_code()
        unregistered = self.client.post(
            "/api/auth/forgot-password",
            json={"email": "unknown@example.com"},
        )

        self.assertEqual(registered.status_code, 200)
        self.assertEqual(registered.json(), unregistered.json())
        self.assertNotIn("reset_token", registered.json())
        self.assertRegex(otp, r"^\d{6}$")
        db = self.Session()
        challenge = db.query(PasswordResetChallenge).filter_by(
            email_digest=_keyed_digest("reset-email", "registered@example.com")
        ).one()
        self.assertNotEqual(challenge.otp_hash, otp)
        self.assertNotIn(otp, registered.text)
        db.close()

    def test_wrong_expired_and_reused_codes_are_rejected(self):
        _, otp = self.request_code()
        wrong = self.client.post(
            "/api/auth/verify-otp",
            json={"email": "registered@example.com", "otp": "000000" if otp != "000000" else "000001"},
        )
        self.assertEqual(wrong.status_code, 400)

        db = self.Session()
        challenge = db.query(PasswordResetChallenge).one()
        challenge.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        db.commit()
        db.close()
        expired = self.client.post(
            "/api/auth/verify-otp",
            json={"email": "registered@example.com", "otp": otp},
        )
        self.assertEqual(expired.status_code, 400)

        _, next_otp = self.request_code_after_cooldown()
        verified = self.client.post(
            "/api/auth/verify-otp",
            json={"email": "registered@example.com", "otp": next_otp},
        )
        self.assertEqual(verified.status_code, 200)
        reused = self.client.post(
            "/api/auth/verify-otp",
            json={"email": "registered@example.com", "otp": next_otp},
        )
        self.assertEqual(reused.status_code, 400)

    def request_code_after_cooldown(self):
        db = self.Session()
        challenge = db.query(PasswordResetChallenge).one()
        challenge.last_sent_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=61)
        db.commit()
        db.close()
        return self.request_code()

    def test_attempt_limit_and_resend_cooldown(self):
        _, otp = self.request_code()
        throttled = self.client.post(
            "/api/auth/resend-otp",
            json={"email": "registered@example.com"},
        )
        self.assertEqual(throttled.status_code, 429)

        wrong_code = "000000" if otp != "000000" else "000001"
        for _ in range(5):
            response = self.client.post(
                "/api/auth/verify-otp",
                json={"email": "registered@example.com", "otp": wrong_code},
            )
        self.assertEqual(response.status_code, 400)
        locked = self.client.post(
            "/api/auth/verify-otp",
            json={"email": "registered@example.com", "otp": otp},
        )
        self.assertEqual(locked.status_code, 400)

    def test_verified_reset_logs_out_old_sessions_and_allows_new_login(self):
        login = self.client.post(
            "/api/auth/login",
            json={"email": "registered@example.com", "password": "OldPassword1!"},
        )
        old_token = login.json()["token"]
        _, otp = self.request_code()
        verified = self.client.post(
            "/api/auth/verify-otp",
            json={"email": "registered@example.com", "otp": otp},
        )
        self.assertEqual(verified.status_code, 200)
        reset_token = verified.json()["reset_token"]

        weak_password = self.client.post(
            "/api/auth/reset-password",
            json={"reset_token": reset_token, "new_password": "weakpassword"},
        )
        self.assertEqual(weak_password.status_code, 422)

        new_password = "NewSecurePassword2!"
        reset = self.client.post(
            "/api/auth/reset-password",
            json={"reset_token": reset_token, "new_password": new_password},
        )
        self.assertEqual(reset.status_code, 200)
        reused_authorization = self.client.post(
            "/api/auth/reset-password",
            json={"reset_token": reset_token, "new_password": "AnotherSecure3!"},
        )
        self.assertEqual(reused_authorization.status_code, 400)
        old_session = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {old_token}"},
        )
        self.assertEqual(old_session.status_code, 401)
        new_login = self.client.post(
            "/api/auth/login",
            json={"email": "registered@example.com", "password": new_password},
        )
        self.assertEqual(new_login.status_code, 200)
        logout = self.client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {new_login.json()['token']}"},
        )
        self.assertEqual(logout.status_code, 200)
        revoked_session = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_login.json()['token']}"},
        )
        self.assertEqual(revoked_session.status_code, 401)

    def test_delivery_failure_invalidates_code_and_missing_smtp_is_explicit(self):
        from app.services.email_service import EmailDeliveryError

        self.send_email.side_effect = EmailDeliveryError("mail unavailable")
        failed_delivery, _ = self.request_code()
        self.assertEqual(failed_delivery.status_code, 200)
        self.assertNotIn("otp", failed_delivery.text.lower())
        db = self.Session()
        challenge = db.query(PasswordResetChallenge).one()
        self.assertIsNone(challenge.otp_hash)
        db.close()

        with patch("app.routes.auth.SMTP_HOST", ""):
            unavailable = self.client.post(
                "/api/auth/forgot-password",
                json={"email": "nobody@example.com"},
            )
        self.assertEqual(unavailable.status_code, 503)
        self.assertIn("not configured", unavailable.json()["detail"].lower())

    def test_request_rate_limit_is_shared_across_unknown_addresses(self):
        for index in range(15):
            response = self.client.post(
                "/api/auth/forgot-password",
                json={"email": f"unknown{index}@example.com"},
            )
            self.assertEqual(response.status_code, 200)

        limited = self.client.post(
            "/api/auth/forgot-password",
            json={"email": "another-unknown@example.com"},
        )
        self.assertEqual(limited.status_code, 429)
        self.assertNotIn("registered", limited.json()["detail"].lower())

    def test_legacy_schema_migration_preserves_existing_rows(self):
        legacy_engine = create_engine("sqlite://")
        with legacy_engine.begin() as connection:
            connection.execute(text("CREATE TABLE users (id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL)"))
            connection.execute(text("INSERT INTO users (id, name) VALUES ('legacy-user', 'Existing User')"))
            connection.execute(text("CREATE TABLE generated_images (id VARCHAR PRIMARY KEY, filename VARCHAR NOT NULL)"))
            connection.execute(text("INSERT INTO generated_images (id, filename) VALUES ('legacy-image', 'existing.png')"))

        with (
            patch("app.database.engine", legacy_engine),
            patch("app.database.DATABASE_URL", "sqlite://"),
            patch("app.database.use_mongodb", return_value=False),
        ):
            migrate_legacy_sqlite_schema()

        inspector = inspect(legacy_engine)
        self.assertIn("token_version", {column["name"] for column in inspector.get_columns("users")})
        image_columns = {column["name"] for column in inspector.get_columns("generated_images")}
        self.assertTrue({"user_id", "favorite"}.issubset(image_columns))
        with legacy_engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT name FROM users WHERE id = 'legacy-user'")).scalar_one(), "Existing User")
            self.assertEqual(connection.execute(text("SELECT filename FROM generated_images WHERE id = 'legacy-image'")).scalar_one(), "existing.png")
        legacy_engine.dispose()


if __name__ == "__main__":
    unittest.main()
