import random
import string
import threading

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from authentication.models import (
    EmailConfirmation,
    PhoneNumberVerification,
    PractitionerAvailableDateTime,
    PractitionerPracticeCriteria,
)

# import time


def generate_code(num):
    return "".join(random.choice(string.digits) for i in range(num))


def generate_unique_code():
    code = generate_code(6)
    exists = EmailConfirmation.objects.filter(token=code).exists()
    while exists:
        code = generate_code(6)
        exists = EmailConfirmation.objects.filter(token=code).exists()
    return code


def generate_phone_unique_code():
    code = generate_code(6)
    exists = PhoneNumberVerification.objects.filter(token=code).exists()
    while exists:
        code = generate_code(6)
        exists = PhoneNumberVerification.objects.filter(token=code).exists()
    return code


def send_email_verification(to_email, token):
    try:
        # send otp to user email
        subject = "Email verification"
        from_email = settings.DEFAULT_FROM_EMAIL
        body = render_to_string(
            "email/email_verification.html",
            {"token": token},
        )
        message = EmailMessage(
            subject,
            body,
            to=[to_email],
            from_email=from_email,
        )
        message.content_subtype = "html"
        message.send(fail_silently=False)
        print("email was sent")
    except Exception as e:
        print("error", e)
        pass


def create_provider_available_days(
    days_and_time: list, provider_criteria: PractitionerPracticeCriteria
):
    try:
        for day_and_time in days_and_time:
            provider_available_date_time = PractitionerAvailableDateTime.objects.create(
                provider_criteria=provider_criteria,
                available_date_time=day_and_time,
            )
            provider_available_date_time.save()
    except Exception as e:
        print("error", e)
        pass


def start_schedule_background_tasks(days_and_time, provider_criteria):
    # Create and start a new thread
    thread = threading.Thread(
        target=create_provider_available_days(days_and_time, provider_criteria)
    )
    thread.start()
