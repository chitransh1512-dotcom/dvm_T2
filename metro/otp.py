import random
import time

from django.core.mail import send_mail
from django.conf import settings

from .utils import get_verified_email


# Stores OTPs as:
# { email : (otp_value, expiry_timestamp) }
OTPS = {}


def generate_otp(key, ttl_seconds=300):
    # key = verified email
    otp = str(random.randint(100000, 999999))
    expires = time.time() + ttl_seconds
    OTPS[key] = (otp, expires)
    return otp


def send_otp(user):
    email = get_verified_email(user)
    if not email:
        raise Exception("No verified email found for OTP")

    otp = generate_otp(email)

    send_mail(
        subject="Your Metro Ticket OTP",
        message=f"Your OTP is {otp}. Valid for 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return otp


def validate_otp(key, otp):
    if key not in OTPS:
        return False

    saved_otp, expiry = OTPS[key]

    if time.time() > expiry:
        del OTPS[key]
        return False

    if saved_otp != str(otp):
        return False

    del OTPS[key]
    return True

