from django.contrib.postgres.fields import ArrayField
from django.db import models

from authentication.base_model import BaseModel
from authentication.models import User


class UserBookingDetails(BaseModel):
    BOOKING_STATUS_CHOICES = (
        ("requested", "requested"),
        ("pending", "pending"),
        ("accepted", "accepted"),
        ("rejected", "rejected"),
        ("failed", "failed"),
        ("succeeded", "succeeded"),
    )
    patient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="patient_booking_details"
    )
    practitioner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="practitioner_booking_details",
        null=True,
        blank=True,
    )
    symptom = models.CharField(max_length=800, null=True, blank=True)
    date_care_is_needed = models.DateField(null=True, blank=True)
    age_of_patient = models.IntegerField(null=True, blank=True)
    zipcode = models.CharField(max_length=800, null=True, blank=True)
    status = models.CharField(
        choices=BOOKING_STATUS_CHOICES, max_length=200, null=True, blank=True
    )
    date_time_of_care = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=800, null=True, blank=True)

    eta = models.CharField(max_length=225, null=True, blank=True)


class UserBookingRequestTimeFrame(BaseModel):
    booking = models.ForeignKey(
        UserBookingDetails,
        on_delete=models.CASCADE,
        related_name="booking_request_timeframe",
    )
    booking_timeframe = ArrayField(
        models.DateTimeField(null=True, blank=True),
    )


class GeneralBookingDetails(models.Model):
    price_per_consultation = models.DecimalField(max_digits=12, decimal_places=2)
