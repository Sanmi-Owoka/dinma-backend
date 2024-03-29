# Generated by Django 4.2.9 on 2024-02-12 21:00

import uuid

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0009_emailconfirmation_is_verified_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="phonenumberverification",
            name="phone_number",
            field=models.CharField(
                blank=True,
                max_length=800,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
                        regex="^\\+?1?\\d{9,15}$",
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="phonenumberverification",
            name="sent",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="emailconfirmation",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("2d956164-e095-4d23-96c3-d9238ac006b3"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="passwordreset",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("2d956164-e095-4d23-96c3-d9238ac006b3"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="phonenumberverification",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("2d956164-e095-4d23-96c3-d9238ac006b3"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="practitionerpracticecriteria",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("2d956164-e095-4d23-96c3-d9238ac006b3"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="providerqualification",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("2d956164-e095-4d23-96c3-d9238ac006b3"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("97f2745d-c48a-46ac-8f30-fdd78593a8e5"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
