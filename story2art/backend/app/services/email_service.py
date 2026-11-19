import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from app.config import (
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
)


class EmailDeliveryError(Exception):
    pass


def is_password_reset_email_configured() -> bool:
    return bool(
        SMTP_HOST
        and SMTP_FROM_EMAIL
        and SMTP_USERNAME
        and SMTP_PASSWORD
        and 0 < SMTP_PORT < 65536
    )


def send_password_reset_email(recipient: str, otp: str) -> None:
    if not is_password_reset_email_configured():
        raise EmailDeliveryError("Password reset email is not configured.")

    message = EmailMessage()
    message["Subject"] = "Story2Art – Password Reset Verification Code"
    message["From"] = formataddr((SMTP_FROM_NAME, SMTP_FROM_EMAIL))
    message["To"] = recipient
    message.set_content(
        "Story2Art password reset\n\n"
        f"Your verification code is: {otp}\n\n"
        "This code expires in 5 minutes and can only be used once.\n"
        "If you did not request this password reset, you can ignore this email "
        "and your password will remain unchanged."
    )

    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(
                SMTP_HOST,
                SMTP_PORT,
                timeout=10,
                context=ssl.create_default_context(),
            ) as server:
                if SMTP_USERNAME:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                refused = server.send_message(message)
                if refused:
                    raise EmailDeliveryError("Password reset email was refused by the SMTP server.")
            return

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            refused = server.send_message(message)
            if refused:
                raise EmailDeliveryError("Password reset email was refused by the SMTP server.")
    except EmailDeliveryError:
        raise
    except (OSError, smtplib.SMTPException) as exc:
        raise EmailDeliveryError("Password reset email could not be sent.") from exc
