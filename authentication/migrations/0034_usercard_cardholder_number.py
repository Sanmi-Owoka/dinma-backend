# Generated by Django 4.2.9 on 2024-05-29 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0033_useraccountdetails"),
    ]

    operations = [
        migrations.AddField(
            model_name="usercard",
            name="cardholder_number",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
