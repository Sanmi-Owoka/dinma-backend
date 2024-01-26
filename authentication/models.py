import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .base_model import BaseModel


def get_avatar_upload_path(instance, filename):
    return os.path.join("emails/{}/{}".format(instance.email, filename))


class User(AbstractUser):

    # added Photo Field
    photo = models.ImageField(null=True, upload_to=get_avatar_upload_path)
    USER_TYPE_CHOICES = (
        ("patient", "patient"),
        ("health_provider", "health_provider"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)
    first_name = models.CharField(max_length=800, null=True, blank=True)
    last_name = models.CharField(max_length=800, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, unique=True)
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format:"
        " '+999999999'. Up to 15 digits allowed.",
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=800, null=True, blank=True
    )
    date_of_birth = models.DateField(null=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=800, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)

    # OTHER DATA
    preferred_communication = models.CharField(max_length=255, null=True, blank=True)
    languages_spoken = ArrayField(
        models.CharField(max_length=255, null=True, blank=True)
    )

    # User Type
    user_type = models.CharField(
        max_length=50, choices=USER_TYPE_CHOICES, null=True, blank=True
    )

    class Meta:
        ordering = ["-date_joined"]


def set_username(sender, instance, **kwargs):
    if not instance.username:
        email = instance.email
        split_email = email.split("@")
        username = split_email[0]
        counter = 1
        while User.objects.filter(username=username).exists():
            username = username + str(counter)
            counter += 1
        instance.username = username
        return username


models.signals.pre_save.connect(set_username, sender=User)


class PasswordReset(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user_password_code"
    )
    token = models.CharField(max_length=9, unique=True)

    @property
    def check_expire(self):
        diff = timezone.now() - self.created_at
        days, seconds = diff.days, diff.seconds
        hours = days * 24 + seconds // 3600
        if hours > 4:
            return True
        else:
            return False


class EmailAddressVerification(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user_email_verification_code"
    )
    token = models.CharField(max_length=9, unique=True)
    is_verified = models.BooleanField(default=False)


class PhoneNumberVerification(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user_phone_verification_code"
    )
    token = models.CharField(max_length=9, unique=True)
    is_verified = models.BooleanField(default=False)
