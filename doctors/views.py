from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from appointments.models import Booking, RejectedBooking
from utils.email_service import send_email
from utils.google_calendar import create_calendar_event
from .models import Availability


@login_required
def doctor_dashboard(request):
    if request.user.role != "doctor":
        return redirect("home")

    slots = Availability.objects.filter(
        doctor=request.user,
        date__gte=date.today(),
    ).order_by("date", "start_time")

    bookings = Booking.objects.filter(
        slot__doctor=request.user,
    ).exclude(
        status="canceled",
    ).select_related("patient", "slot")

    slots_by_date = {}

    for slot in slots:
        if not slot.is_booked:
            date_key = str(slot.date)

            if date_key not in slots_by_date:
                slots_by_date[date_key] = []

            slots_by_date[date_key].append(slot)

    context = {
        "slots_by_date": slots_by_date,
        "bookings": bookings,
        "doctor_experience": request.user.experience,
    }

    return render(request, "doctor_dashboard.html", context)


@login_required
def create_slot(request):
    if request.user.role != "doctor":
        return redirect("home")

    if request.method == "POST":
        date_str = request.POST.get("date")
        start = request.POST.get("start")
        end = request.POST.get("end")
        duration = request.POST.get("duration", "")

        try:
            slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start, "%H:%M").time()
            end_time = datetime.strptime(end, "%H:%M").time()
        except (TypeError, ValueError):
            return render(request, "create_slot.html", {
                "error": "Please enter a valid date and time.",
            })

        if slot_date < date.today():
            return render(request, "create_slot.html", {
                "error": "Cannot create slots for past dates. Please select a future date.",
            })

        if start_time >= end_time:
            return render(request, "create_slot.html", {
                "error": "Start time must be before end time.",
            })

        overlap = Availability.objects.filter(
            doctor=request.user,
            date=slot_date,
            start_time__lt=end_time,
            end_time__gt=start_time,
        )

        if overlap.exists():
            return render(request, "create_slot.html", {
                "error": "Cannot create this slot - it overlaps with an existing slot at this time.",
            })

        if duration == "":
            Availability.objects.create(
                doctor=request.user,
                date=slot_date,
                start_time=start_time,
                end_time=end_time,
            )
        else:
            try:
                duration = int(duration)
            except (TypeError, ValueError):
                return render(request, "create_slot.html", {
                    "error": "Please enter a valid slot duration.",
                })

            if duration <= 0:
                return render(request, "create_slot.html", {
                    "error": "Duration must be greater than zero.",
                })

            start_dt = datetime.combine(slot_date, start_time)
            end_dt = datetime.combine(slot_date, end_time)

            current = start_dt

            while current < end_dt:
                next_time = current + timedelta(minutes=duration)

                if next_time > end_dt:
                    break

                Availability.objects.create(
                    doctor=request.user,
                    date=slot_date,
                    start_time=current.time(),
                    end_time=next_time.time(),
                )

                current = next_time

        return redirect("doctor_dashboard")

    return render(request, "create_slot.html")


@login_required
def delete_slot(request, slot_id):
    if request.user.role != "doctor":
        return redirect("home")

    slot = get_object_or_404(
        Availability,
        id=slot_id,
        doctor=request.user,
    )

    if slot.is_booked:
        booking = Booking.objects.filter(slot=slot).first()

        if booking:
            send_email(
                booking.patient.email,
                "Appointment Cancelled by Doctor",
                f"Hello {booking.patient.full_name},\n\n"
                f"We regret to inform you that your appointment with Dr. {slot.doctor.full_name} "
                f"scheduled for {slot.date.strftime('%d %B %Y')} at {slot.start_time.strftime('%I:%M %p')} "
                f"has been cancelled by the doctor due to unavailability.\n\n"
                f"Please feel free to book another available slot.\n\n"
                f"We apologize for any inconvenience caused.\n\n"
                f"Best Regards,\nMini Hospital Management System",
            )

            booking.delete()

    slot.delete()

    return redirect("doctor_dashboard")


@login_required
def edit_slot(request, slot_id):
    if request.user.role != "doctor":
        return redirect("home")

    slot = get_object_or_404(
        Availability,
        id=slot_id,
        doctor=request.user,
    )

    if slot.is_booked:
        return render(request, "edit_slot.html", {
            "slot": slot,
            "error": "Booked slots cannot be edited.",
        })

    if request.method == "POST":
        new_date = request.POST.get("date")
        new_start = request.POST.get("start")
        new_end = request.POST.get("end")

        try:
            slot_date = datetime.strptime(new_date, "%Y-%m-%d").date()
            start_time = datetime.strptime(new_start, "%H:%M").time()
            end_time = datetime.strptime(new_end, "%H:%M").time()
        except (TypeError, ValueError):
            return render(request, "edit_slot.html", {
                "slot": slot,
                "error": "Please enter a valid date and time.",
            })

        if slot_date < date.today():
            return render(request, "edit_slot.html", {
                "slot": slot,
                "error": "Cannot edit slots to past dates. Please select a future date.",
            })

        if start_time >= end_time:
            return render(request, "edit_slot.html", {
                "slot": slot,
                "error": "Start time must be before end time.",
            })

        overlap = Availability.objects.filter(
            doctor=request.user,
            date=slot_date,
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exclude(id=slot_id)

        if overlap.exists():
            return render(request, "edit_slot.html", {
                "slot": slot,
                "error": "Cannot update slot - overlaps with another existing slot at this time.",
            })

        slot.date = slot_date
        slot.start_time = start_time
        slot.end_time = end_time

        slot.save(update_fields=[
            "date",
            "start_time",
            "end_time",
        ])

        return redirect("doctor_dashboard")

    return render(request, "edit_slot.html", {"slot": slot})


@login_required
def cancel_booking_by_doctor(request, booking_id):
    if request.user.role != "doctor":
        return redirect("home")

    booking = get_object_or_404(
        Booking.objects.select_related("patient", "slot", "slot__doctor"),
        id=booking_id,
        slot__doctor=request.user,
    )

    slot = booking.slot

    if booking.status == "confirmed":

        patient_email = booking.patient.email
        patient_name = booking.patient.full_name
        doctor_name = slot.doctor.full_name
        appointment_date = slot.date.strftime("%d %B %Y")
        appointment_time = slot.start_time.strftime("%I:%M %p")

        booking.delete()

        slot.is_booked = False
        slot.save(update_fields=["is_booked"])

        send_email(
            patient_email,
            "Appointment Cancelled by Doctor",
            f"Hello {patient_name},\n\n"
            f"Your appointment with Dr. {doctor_name} scheduled for "
            f"{appointment_date} at {appointment_time} "
            f"has been cancelled by the doctor.\n\n"
            f"The slot is now available and can be rebooked.\n\n"
            f"Best Regards,\nMini Hospital Management System",
        )

    return redirect("doctor_dashboard")


@login_required
def accept_appointment(request, booking_id):

    if request.user.role != "doctor":
        return redirect("home")

    booking = get_object_or_404(
        Booking.objects.select_related(
            "patient",
            "slot",
            "slot__doctor",
        ),
        id=booking_id,
        slot__doctor=request.user,
    )

    slot = booking.slot

    

    booking.status = "confirmed"

    booking.save(update_fields=[
        "status"
    ])

    slot.is_booked = True

    slot.save(update_fields=[
        "is_booked"
    ])

   

    doctor_event_id = None
    patient_event_id = None

    

    try:

        doctor_event_id = create_calendar_event(
            user=slot.doctor,

            title=f"Appointment with {booking.patient.full_name}",

            description=(
                f"Appointment Confirmed\n\n"
                f"Patient Name: {booking.patient.full_name}\n"
                f"Patient Email: {booking.patient.email}\n"
                f"Patient Mobile: {booking.patient.mobile_number}"
            ),

            slot=slot,

            attendee_email=booking.patient.email,
        )

        print("Doctor Calendar Event Created")

    except Exception as e:

        print("Doctor Calendar Error:", str(e))

   

    try:

        patient_event_id = create_calendar_event(
            user=booking.patient,

            title=f"Appointment with Dr. {slot.doctor.full_name}",

            description=(
                f"Appointment Confirmed\n\n"
                f"Doctor Name: Dr. {slot.doctor.full_name}\n"
                f"Doctor Email: {slot.doctor.email}\n"
                f"Specialization: {slot.doctor.specialization}"
            ),

            slot=slot,

            attendee_email=slot.doctor.email,
        )

        print("Patient Calendar Event Created")

    except Exception as e:

        print("Patient Calendar Error:", str(e))

    

    booking.doctor_calendar_event_id = doctor_event_id
    booking.patient_calendar_event_id = patient_event_id

    booking.save(update_fields=[
        "doctor_calendar_event_id",
        "patient_calendar_event_id",
    ])

    
    send_email(
        booking.patient.email,

        "Appointment Confirmed",

        f"Hello {booking.patient.full_name},\n\n"
        f"Your appointment with Dr. {slot.doctor.full_name} "
        f"has been confirmed.\n\n"

        f"Appointment Details:\n"
        f"Date: {slot.date.strftime('%d %B %Y')}\n"
        f"Time: {slot.start_time.strftime('%I:%M %p')} "
        f"to {slot.end_time.strftime('%I:%M %p')}\n\n"

        f"A Google Calendar invitation has been sent.\n\n"

        f"Best Regards,\n"
        f"Mini Hospital Management System",
    )

    
    send_email(
        slot.doctor.email,

        "Appointment Confirmed",

        f"Dear Dr. {slot.doctor.full_name},\n\n"

        f"You confirmed the appointment with "
        f"{booking.patient.full_name}.\n\n"

        f"Appointment Details:\n"
        f"Date: {slot.date.strftime('%d %B %Y')}\n"
        f"Time: {slot.start_time.strftime('%I:%M %p')} "
        f"to {slot.end_time.strftime('%I:%M %p')}\n\n"

        f"Google Calendar updated successfully.\n\n"

        f"Best Regards,\n"
        f"Mini Hospital Management System",
    )

    return redirect("doctor_dashboard")


@login_required
def reject_appointment(request, booking_id):

    if request.user.role != "doctor":
        return redirect("home")

    booking = get_object_or_404(
        Booking.objects.select_related(
            "patient",
            "slot",
            "slot__doctor",
        ),
        id=booking_id,
        slot__doctor=request.user,
    )

    slot = booking.slot

    patient_email = booking.patient.email
    patient_name = booking.patient.full_name
    doctor_name = slot.doctor.full_name
    appointment_date = slot.date.strftime("%d %B %Y")
    appointment_time = slot.start_time.strftime("%I:%M %p")

    RejectedBooking.objects.get_or_create(
        patient=booking.patient,
        slot=slot,
    )

    booking.delete()

    slot.is_booked = False
    slot.save(update_fields=["is_booked"])

    send_email(
        patient_email,
        "Appointment Request Rejected",
        f"Hello {patient_name},\n\n"
        f"Your appointment request with Dr. {doctor_name} "
        f"for {appointment_date} at {appointment_time} "
        f"has been rejected.\n\n"
        f"Please book another available slot.\n\n"
        f"Best Regards,\nMini Hospital Management System",
    )

    return redirect("doctor_dashboard")