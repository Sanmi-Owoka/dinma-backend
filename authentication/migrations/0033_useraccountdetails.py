# Generated by Django 4.2.9 on 2024-05-17 20:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0032_usercard_payment_method_id_usercard_setup_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserAccountDetails",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bank_name", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "account_number",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "routing_number",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_account_details",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
