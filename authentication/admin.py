from django.contrib import admin
from django.contrib.auth import admin as auth_admin

from .forms import UserChangeForm, UserCreationForm
from .models import User

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
