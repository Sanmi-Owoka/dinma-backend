# Generated by Django 4.2.9 on 2024-02-26 10:09

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserBookingDetails",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.UUID("a5e16901-ebfb-41d2-a1be-abb45c85aa91"),
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("symptom", models.CharField(blank=True, max_length=800, null=True)),
                ("date_care_is_needed", models.DateField(blank=True, null=True)),
                ("age_of_patient", models.IntegerField(blank=True, null=True)),
                ("zipcode", models.CharField(blank=True, max_length=800, null=True)),
                ("status", models.CharField()),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="patient_booking_details",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "practitioner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="practitioner_booking_details",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
                "abstract": False,
            },
        ),
    ]