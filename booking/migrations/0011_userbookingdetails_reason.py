# Generated by Django 4.2.9 on 2024-03-21 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0010_userbookingdetails_date_time_of_care_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="userbookingdetails",
            name="reason",
            field=models.CharField(blank=True, max_length=800, null=True),
        ),
    ]
