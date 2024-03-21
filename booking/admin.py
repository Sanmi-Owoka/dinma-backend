from django.contrib import admin

from .models import UserBookingDetails


@admin.register(UserBookingDetails)
class UserBookingDetailsAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "patient",
        "practitioner",
        "symptom",
        "date_care_is_needed",
        "age_of_patient",
        "zipcode",
        "status",
        "created_at",
        "updated_at",
    ]
    search_fields = ["patient__email", "practitioner__email"]
