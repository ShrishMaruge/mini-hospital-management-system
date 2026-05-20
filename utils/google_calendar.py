import os
from datetime import datetime

from django.utils import timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]


def get_user_credentials(user):

    if not user.google_access_token:
        return None

    credentials = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES,
    )

    

    if credentials.expired and credentials.refresh_token:

        credentials.refresh(Request())

        user.google_access_token = credentials.token
        user.google_token_expiry = credentials.expiry

        user.save(update_fields=[
            "google_access_token",
            "google_token_expiry",
        ])

    return credentials


def create_calendar_event(
    user,
    title,
    description,
    slot,
    attendee_email=None,
):
    """
    Creates Google Calendar Event
    """

    credentials = get_user_credentials(user)

    if not credentials:
        print("No Google credentials found")
        return None

    try:

        service = build(
            "calendar",
            "v3",
            credentials=credentials,
        )

        start_datetime = timezone.make_aware(
            datetime.combine(
                slot.date,
                slot.start_time,
            )
        )

        end_datetime = timezone.make_aware(
            datetime.combine(
                slot.date,
                slot.end_time,
            )
        )

        event_body = {
            "summary": title,

            "description": description,

            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": "Asia/Kolkata",
            },

            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
        }

        

        if attendee_email:

            event_body["attendees"] = [
                {
                    "email": attendee_email
                }
            ]

        

        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            sendUpdates="all",
        ).execute()

        print("Google Calendar Event Created")

        return event.get("id")

    except Exception as e:

        print("Google Calendar Error:", str(e))

        return None