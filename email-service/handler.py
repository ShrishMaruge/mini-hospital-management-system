import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


def send_smtp_email(to_email, subject, message):
    if not SENDER_EMAIL:
        raise ValueError("SENDER_EMAIL is missing")

    if not SENDER_PASSWORD:
        raise ValueError("SENDER_PASSWORD is missing")

    password = SENDER_PASSWORD.replace(" ", "")

    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(message)

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(SENDER_EMAIL, password)
        smtp.send_message(msg)


def build_email(trigger, data):
    if trigger == "CUSTOM_EMAIL":
        return data.get("subject", "HMS Notification"), data.get("message", "")

    if trigger == "OTP_VERIFICATION":
        subject = "OTP for HMS Registration"
        message = f"""Hello {data.get("username", "")},

Your OTP for Mini Hospital Management System registration is:

{data.get("otp", "")}

Best Regards,
Mini Hospital Management System Team"""
        return subject, message

    if trigger == "SIGNUP_WELCOME":
        subject = "Welcome to HMS"
        message = f"""Hello {data.get("username", "")},

Welcome to Mini Hospital Management System.
Your account has been created successfully.

Best Regards,
Mini Hospital Management System Team"""
        return subject, message

    if trigger == "BOOKING_CONFIRMATION":
        subject = "Appointment Booking Confirmation"
        message = f"""Hello,

Your appointment has been confirmed.

Doctor: Dr. {data.get("doctor_name", "")}
Patient: {data.get("patient_name", "")}
Date: {data.get("date", "")}
Time: {data.get("start_time", "")} to {data.get("end_time", "")}

Best Regards,
Mini Hospital Management System Team"""
        return subject, message

    raise ValueError("Invalid trigger")


def send_email_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        trigger = body.get("trigger")
        to_email = body.get("to")
        data = body.get("data", {})

        print("Trigger:", trigger)
        print("To:", to_email)
        print("Sender exists:", bool(SENDER_EMAIL))
        print("Password exists:", bool(SENDER_PASSWORD))

        if not trigger:
            return {"statusCode": 400, "body": json.dumps({"error": "trigger is required"})}

        if not to_email:
            return {"statusCode": 400, "body": json.dumps({"error": "to email is required"})}

        subject, message = build_email(trigger, data)
        send_smtp_email(to_email, subject, message)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Email sent successfully"}),
        }

    except Exception as error:
        print("Email service error:", str(error))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(error)}),
        }
