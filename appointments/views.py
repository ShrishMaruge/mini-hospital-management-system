import logging
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from doctors.models import Availability
from utils.email_service import send_email
from .models import Booking, CancelledBooking, RejectedBooking


logger = logging.getLogger(__name__)


@login_required
def patient_dashboard(request):
    if request.user.role != "patient":
        return redirect("home")

    doctors = User.objects.filter(role="doctor")

    bookings = Booking.objects.filter(
        patient=request.user,
    ).exclude(
        status="canceled",
    ).select_related("slot", "slot__doctor")

    for doctor in doctors:
        if doctor.practicing_year_from:
            doctor.year_difference = datetime.now().year - doctor.practicing_year_from
        else:
            doctor.year_difference = None

    context = {
        "doctors": doctors,
        "bookings": bookings,
    }

    return render(request, "patient_dashboard.html", context)


@login_required
def doctor_slots(request, doctor_id):
    if request.user.role != "patient":
        return redirect("home")

    doctor = get_object_or_404(
        User,
        id=doctor_id,
        role="doctor",
    )

    slots = Availability.objects.filter(
        doctor=doctor,
        is_booked=False,
        date__gte=date.today(),
    ).exclude(
        id__in=RejectedBooking.objects.filter(
            patient=request.user,
        ).values("slot_id")
    ).order_by("date", "start_time")

    slots_by_date = {}

    for slot in slots:
        date_key = str(slot.date)

        if date_key not in slots_by_date:
            slots_by_date[date_key] = []

        slots_by_date[date_key].append(slot)

    context = {
        "slots_by_date": slots_by_date,
        "doctor": doctor,
    }

    return render(request, "doctor_slots.html", context)


@login_required
def book_slot(request, slot_id):
    if request.user.role != "patient":
        return redirect("home")

    if request.method != "POST":
        return redirect("patient_dashboard")

    slot = None

    try:
        with transaction.atomic():
            slot = Availability.objects.select_for_update().get(id=slot_id)

            if slot.is_booked:
                return render(request, "doctor_slots.html", {
                    "error": "This slot is already occupied. Please choose another slot.",
                    "doctor": slot.doctor,
                    "slots_by_date": {},
                })

            if Booking.objects.filter(patient=request.user, slot=slot).exists():
                return render(request, "doctor_slots.html", {
                    "error": "You have already booked this slot.",
                    "doctor": slot.doctor,
                    "slots_by_date": {},
                })

            Booking.objects.create(
                patient=request.user,
                slot=slot,
                status="pending",
            )

            slot.is_booked = True
            slot.save(update_fields=["is_booked"])

    except Availability.DoesNotExist:
        return redirect("patient_dashboard")

    except Exception as e:
        logger.exception("Error while booking slot: %s", e)

        return render(request, "doctor_slots.html", {
            "error": "This slot is no longer available. Please choose another slot.",
            "doctor": slot.doctor if slot else None,
            "slots_by_date": {},
        })

    send_email(
        request.user.email,
        "Appointment Request Submitted",
        f"Hello {request.user.full_name},\n\n"
        f"Your appointment request with Dr. {slot.doctor.full_name} has been submitted.\n"
        f"Date: {slot.date.strftime('%d %B %Y')}\n"
        f"Time: {slot.start_time.strftime('%I:%M %p')} to {slot.end_time.strftime('%I:%M %p')}\n\n"
        f"Status: Pending (waiting for doctor's approval)\n\n"
        f"You will receive an email once the doctor reviews your request.\n\n"
        f"Best Regards,\nMini Hospital Management System",
    )

    send_email(
        slot.doctor.email,
        "New Appointment Request",
        f"Dear Dr. {slot.doctor.full_name},\n\n"
        f"You have received a new appointment request from patient {request.user.full_name}.\n\n"
        f"Patient Details:\n"
        f"Name: {request.user.full_name}\n"
        f"Email: {request.user.email}\n"
        f"Mobile: {request.user.mobile_number}\n"
        f"Gender: {request.user.gender}\n\n"
        f"Appointment Details:\n"
        f"Date: {slot.date.strftime('%d %B %Y')}\n"
        f"Time: {slot.start_time.strftime('%I:%M %p')} to {slot.end_time.strftime('%I:%M %p')}\n\n"
        f"Please log in to your dashboard to accept or reject this appointment.\n\n"
        f"Best Regards,\nMini Hospital Management System",
    )

    return redirect("patient_dashboard")


@login_required
def cancel_booking(request, booking_id):
    if request.user.role != "patient":
        return redirect("home")

    booking = get_object_or_404(
        Booking.objects.select_related("slot", "slot__doctor", "patient"),
        id=booking_id,
        patient=request.user,
    )

    if booking.status == "confirmed":
        slot = booking.slot

        doctor_email = slot.doctor.email
        doctor_name = slot.doctor.full_name
        patient_name = booking.patient.full_name
        patient_email = booking.patient.email
        appointment_date = slot.date.strftime("%d %B %Y")
        appointment_time = slot.start_time.strftime("%I:%M %p")

        

        try:
            from utils.google_calendar import delete_google_calendar_event

            if booking.google_calendar_event_id:
                delete_google_calendar_event(
                    doctor=slot.doctor,
                    event_id=booking.google_calendar_event_id,
                )

        except Exception as e:
            logger.exception(
                "Error deleting Google Calendar event: %s",
                e,
            )

        

        CancelledBooking.objects.get_or_create(
            patient=request.user,
            slot=slot,
        )

        booking.delete()

        

        slot.is_booked = False
        slot.save(update_fields=["is_booked"])

        

        send_email(
            doctor_email,
            "Appointment Cancelled by Patient",
            f"Dear Dr. {doctor_name},\n\n"
            f"Patient {patient_name} has cancelled their confirmed appointment.\n\n"
            f"Appointment Details:\n"
            f"Date: {appointment_date}\n"
            f"Time: {appointment_time}\n\n"
            f"The slot is now available for other patients to book.\n\n"
            f"Best Regards,\nMini Hospital Management System",
        )

        

        send_email(
            patient_email,
            "Appointment Cancelled",
            f"Hello {patient_name},\n\n"
            f"Your appointment with Dr. {doctor_name} scheduled for "
            f"{appointment_date} at {appointment_time} "
            f"has been successfully cancelled.\n\n"
            f"The slot is now available and can be rebooked by you or other patients.\n\n"
            f"Best Regards,\nMini Hospital Management System",
        )

    return redirect("patient_dashboard")
