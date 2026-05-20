import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)

EMAIL_SERVICE_URL = os.getenv(
    "EMAIL_SERVICE_URL",
    "http://localhost:3000/dev/send-email",
)


def send_email(email, subject, message):
    try:
        response = requests.post(
            EMAIL_SERVICE_URL,
            json={
                "trigger": "CUSTOM_EMAIL",
                "to": email,
                "data": {
                    "subject": subject,
                    "message": message,
                },
            },
            timeout=40,
        )

        if response.status_code == 200:
            logger.info("Email sent successfully to %s", email)
            return True

        logger.error(
            "Email service failed for %s. Status: %s Response: %s",
            email,
            response.status_code,
            response.text,
        )
        return False

    except requests.RequestException as error:
        logger.error("Email service connection error for %s: %s", email, error)
        return False
