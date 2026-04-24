from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import CustomUser, LegacyTeacher, School, SubCounty


def register(request):
    if request.method == "POST":
        tsc_number = request.POST["tsc_number"]
        email = request.POST["email"]
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
        tsc_number = request.POST["tsc_number"]
        email = request.POST["email"]

        try:
            user = CustomUser.objects.get(tsc_number=tsc_number, email=email)
            if user.is_active:
                import random

                otp = str(random.randint(100000, 999999))
                request.session["otp"] = otp
                request.session["user_id"] = user.id
                request.session["otp_timestamp"] = timezone.now().timestamp()

                send_mail(
                    "Your Login OTP",
                    f"Your OTP is: {otp}. It expires in 5 minutes.",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, "OTP sent to your email.")
                return redirect("otp_verify")

            messages.error(request, "Account not approved yet.")
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid TSC number or email.")

    return render(request, "accounts/login.html")


def otp_verify(request):
    if request.method == "POST":
        otp = request.POST["otp"]
        if "otp" in request.session and "user_id" in request.session:
            if timezone.now().timestamp() - request.session["otp_timestamp"] < 300:
                if request.session["otp"] == otp:
                    user = CustomUser.objects.get(id=request.session["user_id"])
                    login(request, user)
                    del request.session["otp"]
                    del request.session["user_id"]
                    del request.session["otp_timestamp"]
                    return redirect("dashboard")
                messages.error(request, "Invalid OTP.")
            else:
                messages.error(request, "OTP expired.")
        else:
            messages.error(request, "Session expired.")

    return render(request, "accounts/otp_verify.html")


def sub_counties_api(request):
    sub_counties = SubCounty.objects.all().values("id", "name")
    return JsonResponse(list(sub_counties), safe=False)


def schools_api(request):
    sub_county_id = request.GET.get("sub_county")
    schools = School.objects.filter(sub_county_id=sub_county_id).values("id", "name")
    return JsonResponse(list(schools), safe=False)


def logout_view(request):
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
