import logging
import re
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.dateparse import parse_datetime


logger = logging.getLogger(__name__)

ACCOUNT_INIT_SESSION_KEY = "accounts_pending_initialization_user_id"
OTP_SESSION_KEY = "accounts_pending_otp"
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


def normalize_name(value):
    return " ".join((value or "").replace("\xa0", " ").split())


def build_password_seed(name_value):
    for token in normalize_name(name_value).split():
        cleaned_token = re.sub(r"[^0-9A-Za-z]", "", token)
        if cleaned_token:
            candidate = cleaned_token.capitalize()
            if len(candidate) >= 3:
                return candidate
            return f"{candidate}Member"
    return "Member"


def format_default_password(password_seed, tsc_number):
    suffix = tsc_number[-4:] if len(tsc_number) >= 4 else tsc_number.zfill(4)
    return f"{password_seed}@{suffix}"


def build_default_password(name_value, tsc_number):
    return format_default_password(build_password_seed(name_value), tsc_number)


def is_placeholder_email(email, tsc_number=""):
    normalized_email = (email or "").strip().lower()
    normalized_tsc = (tsc_number or "").strip().lower()
    if not normalized_email:
        return False

    if normalized_tsc and normalized_email == f"{normalized_tsc}@kuppetsiaya.or.ke":
        return True

    return False


def has_registered_email(user):
    email = (user.email or "").strip()
    return bool(email) and not is_placeholder_email(email, user.tsc_number)


def mask_email_address(email):
    local_part, separator, domain = (email or "").partition("@")
    if not separator:
        return email

    if len(local_part) <= 2:
        masked_local = f"{local_part[:1]}*"
    else:
        masked_local = f"{local_part[:1]}{'*' * (len(local_part) - 2)}{local_part[-1:]}"

    domain_name, dot, suffix = domain.partition(".")
    if not dot:
        masked_domain = domain_name[:1] + "*" * max(len(domain_name) - 1, 1)
    else:
        masked_domain = f"{domain_name[:1]}{'*' * max(len(domain_name) - 1, 1)}{dot}{suffix}"

    return f"{masked_local}@{masked_domain}"


def start_account_initialization(request, user_id):
    request.session[ACCOUNT_INIT_SESSION_KEY] = user_id
    request.session.modified = True


def get_account_initialization_user_id(request):
    return request.session.get(ACCOUNT_INIT_SESSION_KEY)


def clear_account_initialization(request):
    request.session.pop(ACCOUNT_INIT_SESSION_KEY, None)
    request.session.modified = True


def clear_otp_challenge(request):
    request.session.pop(OTP_SESSION_KEY, None)
    request.session.modified = True


def clear_auth_flow(request):
    clear_account_initialization(request)
    clear_otp_challenge(request)


def _save_otp_challenge(request, challenge):
    request.session[OTP_SESSION_KEY] = challenge
    request.session.modified = True


def get_otp_challenge(request):
    return request.session.get(OTP_SESSION_KEY)


def generate_otp_code():
    return "".join(str(secrets.randbelow(10)) for _ in range(OTP_LENGTH))


def send_otp_email(user, email, otp_code, purpose):
    greeting_name = user.first_name.split()[0] if (user.first_name or "").strip() else "Member"
    action_label = "verify your email address" if purpose == "initialize" else "complete your sign in"
    subject = (
        "Verify your KUPPET Siaya email address"
        if purpose == "initialize"
        else "Your KUPPET Siaya login verification code"
    )
    message = (
        f"Dear {greeting_name},\n\n"
        f"Use this one-time password to {action_label}: {otp_code}\n\n"
        f"The code expires in {OTP_EXPIRY_MINUTES} minutes.\n"
        "If you did not request this code, please ignore this email."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def begin_email_otp_flow(request, *, purpose, user, email):
    otp_code = generate_otp_code()
    challenge = {
        "purpose": purpose,
        "user_id": user.pk,
        "email": email,
        "otp_hash": make_password(otp_code),
        "expires_at": (timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat(),
        "attempts_left": OTP_MAX_ATTEMPTS,
    }
    _save_otp_challenge(request, challenge)

    try:
        send_otp_email(user, email, otp_code, purpose)
    except Exception:
        clear_otp_challenge(request)
        logger.exception("Failed to send %s OTP for user %s", purpose, user.pk)
        raise


def _register_invalid_attempt(request, challenge):
    attempts_left = max(int(challenge.get("attempts_left", OTP_MAX_ATTEMPTS)) - 1, 0)
    if attempts_left == 0:
        clear_otp_challenge(request)
        return 0

    challenge["attempts_left"] = attempts_left
    _save_otp_challenge(request, challenge)
    return attempts_left


def validate_otp_code(request, submitted_code):
    challenge = get_otp_challenge(request)
    if challenge is None:
        return None, "missing"

    expires_at = parse_datetime(challenge.get("expires_at", ""))
    if expires_at is None or timezone.now() > expires_at:
        clear_otp_challenge(request)
        return challenge, "expired"

    if not submitted_code.isdigit() or len(submitted_code) != OTP_LENGTH:
        challenge["attempts_left"] = _register_invalid_attempt(request, challenge)
        return challenge, "invalid"

    if not check_password(submitted_code, challenge.get("otp_hash", "")):
        challenge["attempts_left"] = _register_invalid_attempt(request, challenge)
        return challenge, "invalid"

    return challenge, None
