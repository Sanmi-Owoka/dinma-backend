import random
import string

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from authentication.models import EmailConfirmation


def generate_code(num):
    return "".join(random.choice(string.digits) for i in range(num))


def generate_unique_code():
    code = generate_code(6)
    exists = EmailConfirmation.objects.filter(token=code).exists()
    while exists:
        code = generate_code(6)
        exists = EmailConfirmation.objects.filter(token=code).exists()
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
