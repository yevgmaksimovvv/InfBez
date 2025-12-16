"""
Email service for OTP and notifications
"""
from fastapi import HTTPException
import logging

from backend.config import settings
from backend.core.security import generate_otp, create_otp_hash

logger = logging.getLogger(__name__)


async def send_otp_email(email: str) -> str:
    """
    Send OTP to email and return hashed value for storage

    Args:
        email: Recipient email address

    Returns:
        str: hash:timestamp for storage

    Raises:
        HTTPException: If SMTP not configured or sending failed
    """
    try:
        import aiosmtplib
        from email.mime.text import MIMEText
    except ImportError:
        logger.error("aiosmtplib not installed. Install: pip install aiosmtplib")
        raise HTTPException(
            status_code=500,
            detail="Email service not available. Please contact administrator."
        )

    # Generate OTP code and timestamp
    otp_code, timestamp = generate_otp()

    # Check SMTP configuration
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        logger.warning(f"SMTP not configured. Cannot send OTP to {email}")
        raise HTTPException(
            status_code=500,
            detail="Email service not configured. Please contact administrator."
        )

    # Send email asynchronously
    try:
        msg = MIMEText(
            f"Your OTP code is: {otp_code}\n\n"
            f"This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
            f"If you did not request this code, please ignore this email."
        )
        msg['Subject'] = "CyberSecurity OTP Code"
        msg['From'] = settings.SMTP_USER
        msg['To'] = email

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True
        )

        logger.info(f"OTP sent successfully to {email}")
    except aiosmtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Email service authentication failed. Please contact administrator."
        )
    except aiosmtplib.SMTPException as e:
        logger.error(f"SMTP error sending OTP: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send OTP email. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error sending OTP: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send OTP email. Please contact administrator."
        )

    # Return hash for storage
    return create_otp_hash(otp_code, timestamp)
