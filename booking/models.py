from django.db import models

from authentication.base_model import BaseModel
from authentication.models import User


class UserBookingDetails(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_booking_details"
    )
    symptom = models.CharField(max_length=800, null=True, blank=True)
    date_care_is_needed = models.DateField(null=True, blank=True)
    age_of_patient = models.IntegerField(null=True, blank=True)
    zipcode = models.CharField(max_length=800, null=True, blank=True)
