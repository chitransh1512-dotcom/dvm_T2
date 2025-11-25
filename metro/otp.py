import random
import time

# Stores OTPs as:
# { key : (otp_value, expiry_timestamp) }
OTPS = {}


# def generate_otp(key, ttl_seconds=300):
#     """
#     Creates a 6-digit OTP for a given key.
#     key = usually the user's email.
#     ttl_seconds = validity period (default: 5 minutes)
#     """
#     otp = str(random.randint(100000, 999999))
#     expires = time.time() + ttl_seconds
#     OTPS[key] = (otp, expires)
#     return otp
def generate_otp(key, ttl_seconds=300):
    otp = str(random.randint(100000, 999999))
    expires = time.time() + ttl_seconds
    OTPS[key] = (otp, expires)

    print("OTP for", key, ":", otp)   # ← Add this line

    return otp



def validate_otp(key, otp):
    """
    Checks if OTP matches and is not expired.
    """
    if key not in OTPS:
        return False

    saved_otp, expiry = OTPS[key]

    # Expired?
    if time.time() > expiry:
        del OTPS[key]
        return False

    # Wrong?
    if saved_otp != str(otp):
        return False

    # Valid → remove to prevent reuse
    del OTPS[key]
    return True
