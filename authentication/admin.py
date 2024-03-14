from django.contrib import admin
from django.contrib.auth import admin as auth_admin

from .forms import UserChangeForm, UserCreationForm
from .models import (
    EmailConfirmation,
    PasswordReset,
    PhoneNumberVerification,
    PractitionerAvailableDateTime,
    PractitionerPracticeCriteria,
    ProviderQualification,
    User,
)

# @admin.register(User)
# class UserAdmin(auth_admin.UserAdmin):
#     list_display = [
#         "id",
#         "email",
#         "phone_number",
#         "username",
#         "date_of_birth",
#         "user_type",
#         "date_joined",
#     ]
#     search_fields = ["email", ]
#     list_filter = ["user_type", ]


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
        (
            "Avatar  info",
            {
                "fields": (
                    "date_of_birth",
                    "gender",
                    "address",
                    "city",
                    "state",
                    "country",
                    "preferred_communication",
                    "languages_spoken",
                    "user_type",
                )
            },
        ),
    ) + auth_admin.UserAdmin.fieldsets
    list_display = [
        "id",
        "email",
        "phone_number",
        "username",
        "date_of_birth",
        "user_type",
        "date_joined",
    ]

    search_fields = [
        "email",
    ]
    list_filter = [
        "user_type",
    ]


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ["user", "token"]
    search_fields = ["user__email"]


@admin.register(EmailConfirmation)
class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ["email", "token", "sent", "is_verified"]
    search_fields = ["email"]


@admin.register(ProviderQualification)
class ProviderQualificationAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "practioner_type",
        "credential_title",
        "NPI",
        "CAQH",
        "is_verified",
    ]
    search_fields = ["user__email"]


@admin.register(PractitionerAvailableDateTime)
class PractitionerAvailableDateTimeAdmin(admin.ModelAdmin):
    list_display = [
        "provider",
        "available_date_time",
    ]
    search_fields = ["provider__email"]


@admin.register(PractitionerPracticeCriteria)
class PractitionerPracticeCriteriaAdmin(admin.ModelAdmin):
    list_display = ["user", "practice_name", "max_distance", "age_range"]
    search_fields = ["provider__email"]


@admin.register(PhoneNumberVerification)
class PhoneNumberVerificationAdmin(admin.ModelAdmin):
    list_display = [
        "phone_number",
        "token",
        "sent",
        "is_verified",
    ]
    search_fields = ["phone_number"]
