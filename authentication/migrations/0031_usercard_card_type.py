# Generated by Django 4.2.9 on 2024-05-17 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0030_usercard"),
    ]

    operations = [
        migrations.AddField(
            model_name="usercard",
            name="card_type",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]