# Generated by Django 4.2.9 on 2024-05-17 12:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0029_alter_insurancedetails_insured_date_of_birth"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserCard",
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
                ("last4_digit", models.CharField(blank=True, max_length=10, null=True)),
                ("exp_month", models.CharField(blank=True, max_length=2, null=True)),
                ("exp_year", models.CharField(blank=True, max_length=4, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_card",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
