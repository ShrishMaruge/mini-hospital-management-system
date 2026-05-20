from django.conf import settings
from django.db import models

from doctors.models import Availability


class Booking(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("rejected", "Rejected"),
        ("canceled", "Canceled"),
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_bookings",
    )

    slot = models.OneToOneField(
        Availability,
        on_delete=models.CASCADE,
        related_name="booking",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending",
    )

  

    doctor_calendar_event_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    patient_calendar_event_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.patient} booked "
            f"{self.slot} - {self.status}"
        )


class RejectedBooking(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rejected_bookings",
    )

    slot = models.ForeignKey(
        Availability,
        on_delete=models.CASCADE,
        related_name="rejections",
    )

    rejected_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ("patient", "slot")

    def __str__(self):
        return f"{self.patient} rejected for {self.slot}"


class CancelledBooking(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cancelled_bookings",
    )

    slot = models.ForeignKey(
        Availability,
        on_delete=models.CASCADE,
        related_name="cancellations",
    )

    cancelled_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ("patient", "slot")

    def __str__(self):
        return f"{self.patient} cancelled {self.slot}"