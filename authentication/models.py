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
    email_verified = models.BooleanField(default=False)

    # IF PROVIDER
    qualified = models.BooleanField(default=False)

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


class EmailConfirmation(BaseModel):
    email = models.EmailField(max_length=254, null=True)
    token = models.CharField(max_length=9, unique=True)
    sent = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    @property
    def check_expire(self):
        diff = timezone.now() - self.created_at
        days, seconds = diff.days, diff.seconds
        hours = days * 72 + seconds // 3600
        if hours < 0:
            return True
        else:
            return False


class PhoneNumberVerification(BaseModel):
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format:"
        " '+999999999'. Up to 15 digits allowed.",
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=800, null=True, blank=True
    )
    token = models.CharField(max_length=9, unique=True)
    is_verified = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)

    @property
    def check_expire(self):
        diff = timezone.now() - self.created_at
        days, seconds = diff.days, diff.seconds
        hours = days * 72 + seconds // 3600
        if hours < 0:
            return True
        else:
            return False


class ProviderQualification(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user_provider_qualification"
    )
    practioner_type = models.CharField(max_length=255, null=True, blank=True)
    credential_title = models.CharField(max_length=255, null=True, blank=True)
    NPI = models.CharField(max_length=255, null=True, blank=True)
    CAQH = models.CharField(max_length=255, null=True, blank=True)
    licensed_states = ArrayField(
        models.CharField(max_length=255, null=True, blank=True)
    )
    is_verified = models.BooleanField(default=False)


class PractitionerPracticeCriteria(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user_practice_criteria"
    )
    practice_name = models.CharField(max_length=255, null=True, blank=True)
    max_distance = models.PositiveIntegerField(null=True, blank=True)
    preferred_zip_codes = ArrayField(
        models.CharField(max_length=255, null=True, blank=True)
    )
    available_days = ArrayField(models.DateTimeField(null=True, blank=True))
    price_per_consultation = models.DecimalField(max_digits=12, decimal_places=2)
    minimum_age = models.PositiveIntegerField(null=True, blank=True)
    maximum_age = models.PositiveIntegerField(null=True, blank=True)


class Referral(BaseModel):
    REFERRAL_TYPES = (
        ("patient", "patient"),
        ("practitioner", "practitioner"),
    )
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="referee_user",
        null=True,
        blank=True,
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="referred_user",
    )
    reference_code = models.CharField(max_length=200, null=True)
    status = models.CharField(
        default="registered", max_length=200
    )  # registered and onboarded are the two status here
    type = models.CharField(
        choices=REFERRAL_TYPES, max_length=200, null=True, blank=True
    )
