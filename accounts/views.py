import random
from datetime import datetime, timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from utils.email_service import send_email
from .models import TemporaryRegistration, User
import os
from google_auth_oauthlib.flow import Flow
from utils.google_calendar import SCOPES
import random
from datetime import datetime, timedelta

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

OTP_EXPIRY_SECONDS = 300


def is_otp_expired(temp_reg):
    return timezone.now() > temp_reg.otp_created_at + timedelta(seconds=OTP_EXPIRY_SECONDS)


def home(request):
    return render(request, "home.html")


def user_login(request, role):
    if request.user.is_authenticated:
        if request.user.role == "doctor":
            return redirect("/doctor/dashboard/")
        return redirect("/patient/dashboard/")

    if request.method == "POST":
        identifier = request.POST.get("identifier")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=identifier)
            username = user_obj.username
        except User.DoesNotExist:
            username = identifier

        user = authenticate(request, username=username, password=password)

        if user:
            if user.role != role:
                return render(request, "login.html", {
                    "role": role,
                    "error": "Invalid credentials",
                })

            login(request, user)

            if role == "doctor":
                return redirect("/doctor/dashboard/")
            return redirect("/patient/dashboard/")

        return render(request, "login.html", {
            "role": role,
            "error": "Invalid username/email or password",
        })

    return render(request, "login.html", {"role": role})


def register(request, role):
    if request.user.is_authenticated:
        if request.user.role == "doctor":
            return redirect("/doctor/dashboard/")
        return redirect("/patient/dashboard/")

    if role not in ["doctor", "patient"]:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        full_name = request.POST.get("full_name")
        gender = request.POST.get("gender")
        dob = request.POST.get("dob")
        mobile = request.POST.get("mobile")

        qualification = request.POST.get("qualification")
        specialization = request.POST.get("specialization")
        practicing_year_from = request.POST.get("practicing_year_from")
        license_number = request.POST.get("license_number")

        blood_group = request.POST.get("blood_group")

        if password != confirm_password:
            return render(request, "register.html", {
                "role": role,
                "error": "Passwords do not match. Please try again.",
            })

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {
                "role": role,
                "error": "Username already taken. Please choose a different username.",
            })

        if User.objects.filter(email=email).exists():
            return render(request, "register.html", {
                "role": role,
                "error": "Email already registered. Please use a different email or try logging in.",
            })

        if TemporaryRegistration.objects.filter(email=email).exists():
            temp_reg = TemporaryRegistration.objects.get(email=email)

            if is_otp_expired(temp_reg):
                temp_reg.delete()
            else:
                return render(request, "register.html", {
                    "role": role,
                    "error": "OTP verification pending for this email. Please check your email and verify.",
                })

        if role == "doctor":
            try:
                practicing_year_from = int(practicing_year_from)
            except (TypeError, ValueError):
                return render(request, "register.html", {
                    "role": role,
                    "error": "Please enter a valid year when you started practicing.",
                })

            current_year = timezone.now().year

            if practicing_year_from > current_year or practicing_year_from < 1900:
                return render(request, "register.html", {
                    "role": role,
                    "error": "Please enter a valid practicing year between 1900 and the current year.",
                })
        else:
            practicing_year_from = None

        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return render(request, "register.html", {
                "role": role,
                "error": "Please enter a valid date of birth.",
            })

        if dob_date > timezone.now().date():
            return render(request, "register.html", {
                "role": role,
                "error": "Date of birth cannot be in the future.",
            })

        otp = str(random.randint(10000, 99999))
        print("Generated OTP:", otp)

        hashed_password = make_password(password)

        temp_reg = TemporaryRegistration.objects.create(
            email=email,
            username=username,
            password=hashed_password,
            otp=otp,
            role=role,
            full_name=full_name,
            gender=gender,
            date_of_birth=dob_date,
            mobile_number=mobile,
            qualification=qualification,
            specialization=specialization,
            practicing_year_from=practicing_year_from,
            license_number=license_number,
            blood_group=blood_group,
        )

        verify_url = request.build_absolute_uri(
            reverse("verify_otp", kwargs={"role": role, "email": email})
        )

        otp_message = f"""Your OTP for Mini Hospital Management System registration is: {otp}

To verify your registration, open the link below:

{verify_url}

This OTP is valid for {OTP_EXPIRY_SECONDS} seconds.

If you did not request this, please ignore this email.

Best Regards,
Mini Hospital Management System Team"""

        try:
            result = send_email(
                email,
                "OTP for HMS Registration",
                otp_message,
            )

            if not result:
                temp_reg.delete()
                return render(request, "register.html", {
                    "role": role,
                    "error": "Failed to send OTP email. Please try again.",
                })

        except Exception as e:
            temp_reg.delete()
            return render(request, "register.html", {
                "role": role,
                "error": str(e),
            })

        return redirect(reverse("verify_otp", kwargs={"role": role, "email": email}))

    return render(request, "register.html", {"role": role})


def verify_otp(request, role, email):
    if request.user.is_authenticated:
        if request.user.role == "doctor":
            return redirect("/doctor/dashboard/")
        return redirect("/patient/dashboard/")

    try:
        temp_reg = TemporaryRegistration.objects.get(email=email)
    except TemporaryRegistration.DoesNotExist:
        return render(request, "otp_verify.html", {
            "role": role,
            "email": email,
            "error": "No pending registration found for this email.",
        })

    otp_age = timezone.now() - temp_reg.otp_created_at
    remaining_seconds = max(0, OTP_EXPIRY_SECONDS - int(otp_age.total_seconds()))

    if remaining_seconds == 0:
        temp_reg.delete()
        return render(request, "otp_verify.html", {
            "role": role,
            "email": email,
            "error": "OTP has expired. Please register again.",
            "remaining_seconds": remaining_seconds,
        })

    if request.method == "POST":
        otp_entered = request.POST.get("otp", "").strip()

        if not otp_entered.isdigit() or len(otp_entered) != 5:
            return render(request, "otp_verify.html", {
                "role": role,
                "email": email,
                "error": "OTP is wrong. Please try again.",
                "remaining_seconds": remaining_seconds,
            })

        if otp_entered == temp_reg.otp:
            user = User.objects.create(
                username=temp_reg.username,
                email=temp_reg.email,
                role=temp_reg.role,
                full_name=temp_reg.full_name,
                gender=temp_reg.gender,
                date_of_birth=temp_reg.date_of_birth,
                mobile_number=temp_reg.mobile_number,
                qualification=temp_reg.qualification,
                specialization=temp_reg.specialization,
                practicing_year_from=temp_reg.practicing_year_from,
                license_number=temp_reg.license_number,
                blood_group=temp_reg.blood_group,
                password=temp_reg.password,
            )

            temp_reg.delete()

            role_title = "Doctor" if role == "doctor" else "Patient"

            welcome_message = f"""Welcome to Mini Hospital Management System (HMS)

Dear {user.full_name},

We are pleased to inform you that your account has been successfully created as a {role_title}.

--- ACCOUNT DETAILS ---
Username: {user.username}
Email: {user.email}
Role: {role_title}

--- NEXT STEPS ---
{"Please log in to create your availability slots and start accepting patient appointments." if role == "doctor" else "You can now log in and book appointments with our experienced doctors."}

To log in, visit: http://localhost:8001/login/{role}/

Best Regards,
Mini Hospital Management System Team"""

            try:
                send_email(
                    user.email,
                    f"Welcome to HMS - {role_title} Account Created",
                    welcome_message,
                )
            except Exception as e:
                print(f"Error sending welcome email: {str(e)}")

            return redirect(reverse("login", kwargs={"role": role}))

        return render(request, "otp_verify.html", {
            "role": role,
            "email": email,
            "error": "OTP is wrong. Enter correct OTP.",
            "remaining_seconds": remaining_seconds,
        })

    return render(request, "otp_verify.html", {
        "role": role,
        "email": email,
        "remaining_seconds": remaining_seconds,
    })


def resend_otp(request, role, email):
    try:
        temp_reg = TemporaryRegistration.objects.get(email=email)
    except TemporaryRegistration.DoesNotExist:
        return render(request, "otp_verify.html", {
            "role": role,
            "email": email,
            "error": "No pending registration found for this email.",
        })

    otp_age = timezone.now() - temp_reg.otp_created_at

    if otp_age < timedelta(seconds=OTP_EXPIRY_SECONDS):
        remaining = int((timedelta(seconds=OTP_EXPIRY_SECONDS) - otp_age).total_seconds())

        return render(request, "otp_verify.html", {
            "role": role,
            "email": email,
            "error": f"OTP is still valid. Please wait {remaining} seconds before requesting a new OTP.",
            "remaining_seconds": remaining,
        })

    temp_reg.delete()

    return render(request, "otp_verify.html", {
        "role": role,
        "email": email,
        "error": "OTP has expired. Please register again.",
        "remaining_seconds": 0,
    })


def logout_view(request):
    logout(request)
    return redirect("home")


def google_connect(request):
    if not request.user.is_authenticated:
        return redirect("home")

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")],
            }
        },
        scopes=SCOPES,
    )

    flow.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    
    request.session["google_oauth_state"] = state

    
    request.session["google_code_verifier"] = flow.code_verifier

    request.session.modified = True

    print("Generated OAuth State:", state)
    print("Generated Code Verifier:", flow.code_verifier)

    return redirect(authorization_url)


def google_callback(request):
    if not request.user.is_authenticated:
        return redirect("home")

    
    session_state = request.session.get("google_oauth_state")
    code_verifier = request.session.get("google_code_verifier")

    
    returned_state = request.GET.get("state")

    print("Session State:", session_state)
    print("Returned State:", returned_state)

    
    if not session_state:
        print("OAuth session expired")
        return redirect("home")

    
    if session_state != returned_state:
        print("OAuth state mismatch")
        return redirect("home")

    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")],
                }
            },
            scopes=SCOPES,
            state=session_state,
        )

        flow.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

        
        flow.code_verifier = code_verifier

        
        flow.fetch_token(
            authorization_response=request.build_absolute_uri()
        )

        credentials = flow.credentials

        print("ACCESS TOKEN:", credentials.token)
        print("REFRESH TOKEN:", credentials.refresh_token)

        
        request.user.google_access_token = credentials.token
        request.user.google_refresh_token = credentials.refresh_token
        request.user.google_token_expiry = credentials.expiry

        request.user.save(update_fields=[
            "google_access_token",
            "google_refresh_token",
            "google_token_expiry",
        ])

        
        request.session.pop("google_oauth_state", None)
        request.session.pop("google_code_verifier", None)

        print("Google Calendar connected successfully")

    except Exception as e:
        print("Google OAuth Error:", str(e))
        return redirect("home")

    if request.user.role == "doctor":
        return redirect("doctor_dashboard")

    return redirect("patient_dashboard")