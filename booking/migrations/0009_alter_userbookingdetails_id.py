# Generated by Django 4.2.9 on 2024-03-13 20:23

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0008_alter_userbookingdetails_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userbookingdetails",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False
            ),
        ),
    ]
