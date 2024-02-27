from django.db import models

from authentication.base_model import BaseModel
from authentication.models import User


class UserBookingDetails(BaseModel):
    BOOKING_STATUS_CHOICES = (
        ("requested", "requested"),
        ("accepted", "accepted"),
        ("rejected", "rejected"),
        ("failed", "failed"),
        ("succeeded", "succeeded"),
    )
    patient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="patient_booking_details"
    )
    practitioner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="practitioner_booking_details"
    )
    symptom = models.CharField(max_length=800, null=True, blank=True)
    date_care_is_needed = models.DateField(null=True, blank=True)
    age_of_patient = models.IntegerField(null=True, blank=True)
    zipcode = models.CharField(max_length=800, null=True, blank=True)
    status = models.CharField(
        choices=BOOKING_STATUS_CHOICES, max_length=200, null=True, blank=True
    )
