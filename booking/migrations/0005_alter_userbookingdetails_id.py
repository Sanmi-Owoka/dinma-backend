# Generated by Django 4.2.9 on 2024-02-27 14:30

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0004_alter_userbookingdetails_date_care_is_needed_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userbookingdetails",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("b4a3708e-a193-4271-9051-a8b784334cd7"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
