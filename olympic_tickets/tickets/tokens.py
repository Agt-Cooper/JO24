from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

_signer = TimestampSigner(salt="jo24-email-verify-v1")

def make_email_token(user):
    # on signe "<id>:<email>"
    payload = f"{user.id}:{user.email}"
    return _signer.sign(payload)

def read_email_token(token, max_age_seconds=3*24*3600):  # 3 jours
    try:
        unsigned = _signer.unsign(token, max_age=max_age_seconds)
        user_id_str, email = unsigned.split(":", 1)
        return int(user_id_str), email
    except (BadSignature, SignatureExpired, ValueError):
        return None, None
