from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import redirect, render

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
        user = authenticate(request, tsc_number=tsc_number, password=password)

        if user is not None:
            if user.approval_status != "APPROVED" or not user.is_active:
                messages.error(request, "Account not approved yet.")
                return render(request, "accounts/login.html")

            login(request, user)
            return redirect("dashboard")

        try:
            existing_user = CustomUser.objects.get(tsc_number=tsc_number)
        except CustomUser.DoesNotExist:
            existing_user = None

        if existing_user and (existing_user.approval_status != "APPROVED" or not existing_user.is_active):
            messages.error(request, "Account not approved yet.")
        else:
            messages.error(request, "Invalid TSC number or password.")

    return render(request, "accounts/login.html")


def otp_verify(request):
    messages.info(request, "Use your TSC number and password to sign in.")
    return redirect("login")


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
