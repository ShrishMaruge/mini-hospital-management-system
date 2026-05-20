from django.urls import path
from . import views


urlpatterns = [
    path("dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path("create-slot/", views.create_slot, name="create_slot"),
    path("delete-slot/<int:slot_id>/", views.delete_slot, name="delete_slot"),
    path("edit-slot/<int:slot_id>/", views.edit_slot, name="edit_slot"),

    path(
        "cancel-booking/<int:booking_id>/",
        views.cancel_booking_by_doctor,
        name="cancel_booking_by_doctor",
    ),
    path(
        "accept-appointment/<int:booking_id>/",
        views.accept_appointment,
        name="accept_appointment",
    ),
    path(
        "reject-appointment/<int:booking_id>/",
        views.reject_appointment,
        name="reject_appointment",
    ),
]
