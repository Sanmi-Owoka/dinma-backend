from django.contrib import admin

from .models import (
    GeneralBookingDetails,
    UserBookingDetails,
    UserBookingRequestTimeFrame,
)


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


@admin.register(GeneralBookingDetails)
class GeneralBookingDetailsAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "price_per_consultation",
    ]


@admin.register(UserBookingRequestTimeFrame)
class UserBookingRequestTimeFrameAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "booking",
        "booking_timeframe",
        "created_at",
        "updated_at",
    ]
    search_fields = ["booking__patient__email", "booking__practitioner__email"]
