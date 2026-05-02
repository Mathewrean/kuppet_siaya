from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .authentication import (
    OTP_EXPIRY_MINUTES,
    begin_email_otp_flow,
    build_default_password,
    clear_auth_flow,
    clear_otp_challenge,
    get_account_initialization_user_id,
    get_otp_challenge,
    has_registered_email,
    mask_email_address,
    start_account_initialization,
    validate_otp_code,
)
from .models import CustomUser, LegacyTeacher, School, SubCounty


def register(request):
    if request.method == "POST":
        tsc_number = request.POST["tsc_number"]
        email = request.POST.get("email", "").strip() or None
        phone_number = request.POST.get("phone_number", "")
        sub_county = request.POST.get("sub_county", "")
        school = request.POST.get("school", "")

        try:
            teacher = LegacyTeacher.objects.using("legacy").get(tsc_number=tsc_number)
            first_name = teacher.full_name.split()[0]
            last_name = " ".join(teacher.full_name.split()[1:]) if len(teacher.full_name.split()) > 1 else ""
        except LegacyTeacher.DoesNotExist:
            messages.error(request, "TSC Number not found. Contact your Sub-county Representative.")
            return redirect("register")

        if CustomUser.objects.filter(tsc_number=tsc_number).exists():
            messages.error(request, "TSC number already registered.")
            return redirect("register")

        if email and CustomUser.objects.filter(email__iexact=email).exists():
            messages.error(request, "That email address is already in use.")
            return redirect("register")

        CustomUser.objects.create_user(
            tsc_number=tsc_number,
            email=email,
            password=request.POST["password"],
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            sub_county=sub_county,
            school=school,
            is_active=False,
        )
        messages.success(request, "Registration successful. Please wait for approval.")
        return redirect("login")

    return render(request, "accounts/register.html")


def login_view(request):
    if request.method == "POST":
        tsc_number = request.POST["tsc_number"].strip()
        password = request.POST["password"]

        try:
            existing_user = CustomUser.objects.get(tsc_number=tsc_number)
        except CustomUser.DoesNotExist:
            existing_user = None

        if existing_user and (existing_user.approval_status != "APPROVED" or not existing_user.is_active):
            messages.error(request, "Account not approved yet.")
        elif existing_user and not has_registered_email(existing_user):
            user = authenticate(request, tsc_number=tsc_number, password=password)
            if user is not None:
                clear_otp_challenge(request)
                start_account_initialization(request, existing_user.pk)
                return redirect("initialize_account")
            messages.error(request, "Invalid TSC number or password.")
        else:
            user = authenticate(request, tsc_number=tsc_number, password=password)
            if user is None:
                if existing_user and has_registered_email(existing_user):
                    default_password = build_default_password(
                        existing_user.first_name or existing_user.last_name or "Member",
                        existing_user.tsc_number,
                    )
                    if password == default_password:
                        messages.error(
                            request,
                            "This account has already been initialized. Use your current password, then complete OTP verification.",
                        )
                    else:
                        messages.error(request, "Invalid TSC number or password.")
                else:
                    messages.error(request, "Invalid TSC number or password.")
            else:
                try:
                    begin_email_otp_flow(
                        request,
                        purpose="login",
                        user=user,
                        email=user.email,
                    )
                except Exception:
                    messages.error(
                        request,
                        "We could not send a verification code right now. Please try again in a moment.",
                    )
                    return render(request, "accounts/login.html")

                messages.success(
                    request,
                    f"A verification code has been sent to {mask_email_address(user.email)}.",
                )
                return redirect("otp_verify")

    return render(request, "accounts/login.html")


def initialize_account(request):
    user_id = get_account_initialization_user_id(request)
    if not user_id:
        messages.info(request, "Use your first-time password to start account setup.")
        return redirect("login")

    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        clear_auth_flow(request)
        messages.error(request, "Account setup could not be completed. Please sign in again.")
        return redirect("login")

    if user.approval_status != "APPROVED" or not user.is_active:
        clear_auth_flow(request)
        messages.error(request, "Account not approved yet.")
        return redirect("login")

    if has_registered_email(user):
        clear_auth_flow(request)
        messages.info(request, "Your account is already initialized. Please sign in to continue.")
        return redirect("login")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        confirm_email = request.POST.get("confirm_email", "").strip()

        try:
            validate_email(email)
            validate_email(confirm_email)
        except ValidationError:
            messages.error(request, "Enter a valid email address in both fields.")
            return render(request, "accounts/initialize_account.html", {"member": user})

        normalized_email = CustomUser.objects.normalize_email(email)
        normalized_confirm_email = CustomUser.objects.normalize_email(confirm_email)

        if normalized_email.lower() != normalized_confirm_email.lower():
            messages.error(request, "Email addresses do not match.")
            return render(request, "accounts/initialize_account.html", {"member": user})

        if CustomUser.objects.filter(email__iexact=normalized_email).exclude(pk=user.pk).exists():
            messages.error(request, "That email address is already in use.")
            return render(request, "accounts/initialize_account.html", {"member": user})

        try:
            begin_email_otp_flow(
                request,
                purpose="initialize",
                user=user,
                email=normalized_email,
            )
        except Exception:
            messages.error(
                request,
                "We could not send a verification code right now. Please try again in a moment.",
            )
            return render(request, "accounts/initialize_account.html", {"member": user})

        messages.success(
            request,
            f"A verification code has been sent to {mask_email_address(normalized_email)}.",
        )
        return redirect("otp_verify")

    return render(request, "accounts/initialize_account.html", {"member": user})


def otp_verify(request):
    challenge = get_otp_challenge(request)
    if challenge is None:
        messages.info(request, "Use your TSC number and password to sign in.")
        return redirect("login")

    try:
        user = CustomUser.objects.get(pk=challenge["user_id"])
    except CustomUser.DoesNotExist:
        clear_auth_flow(request)
        messages.error(request, "This verification request is no longer valid. Please sign in again.")
        return redirect("login")

    if user.approval_status != "APPROVED" or not user.is_active:
        clear_auth_flow(request)
        messages.error(request, "Account not approved yet.")
        return redirect("login")

    if request.method == "POST":
        submitted_otp = request.POST.get("otp", "").strip()
        challenge, error_code = validate_otp_code(request, submitted_otp)

        if error_code == "missing":
            messages.info(request, "Use your TSC number and password to sign in.")
            return redirect("login")

        if error_code == "expired":
            messages.error(request, "The verification code expired. Request a new code to continue.")
            if challenge["purpose"] == "initialize":
                return redirect("initialize_account")
            return redirect("login")

        if error_code == "invalid":
            attempts_left = challenge.get("attempts_left", 0)
            if attempts_left > 0:
                messages.error(request, f"Invalid verification code. {attempts_left} attempt(s) remaining.")
            else:
                messages.error(request, "Too many invalid verification attempts. Please sign in again.")
                if challenge["purpose"] == "initialize":
                    return redirect("initialize_account")
                return redirect("login")
        else:
            if challenge["purpose"] == "initialize":
                pending_email = challenge["email"]
                if CustomUser.objects.filter(email__iexact=pending_email).exclude(pk=user.pk).exists():
                    clear_auth_flow(request)
                    messages.error(request, "That email address is already in use.")
                    return redirect("initialize_account")
                user.email = pending_email
                user.save(update_fields=["email"])
                clear_auth_flow(request)
                login(request, user)
                messages.success(request, "Email verified successfully.")
                return redirect("dashboard")

            clear_auth_flow(request)
            login(request, user)
            messages.success(request, "Login verified successfully.")
            return redirect("dashboard")

    active_challenge = get_otp_challenge(request) or challenge
    purpose = active_challenge["purpose"]
    return render(
        request,
        "accounts/otp_verify.html",
        {
            "otp_purpose": purpose,
            "otp_destination": mask_email_address(active_challenge["email"]),
            "otp_expiry_minutes": OTP_EXPIRY_MINUTES,
        },
    )


def sub_counties_api(request):
    sub_counties = SubCounty.objects.all().values("id", "name")
    return JsonResponse(list(sub_counties), safe=False)


def schools_api(request):
    sub_county_id = request.GET.get("sub_county")
    schools = School.objects.filter(sub_county_id=sub_county_id).values("id", "name")
    return JsonResponse(list(schools), safe=False)


def logout_view(request):
    clear_auth_flow(request)
    logout(request)
    return redirect("home")


def verify_tsc(request):
    tsc_number = request.GET.get("tsc")
    try:
        teacher = LegacyTeacher.objects.using("legacy").get(tsc_number=tsc_number)
        data = {
            "exists": True,
            "first_name": teacher.full_name.split()[0],
            "last_name": " ".join(teacher.full_name.split()[1:]) if len(teacher.full_name.split()) > 1 else "",
        }
    except LegacyTeacher.DoesNotExist:
        data = {"exists": False}
    return JsonResponse(data)
