# Generated by Django 4.2.9 on 2024-02-29 19:26

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0017_user_qualified_alter_emailconfirmation_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="social_security_number",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name="emailconfirmation",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("6e388fda-b31a-47c4-a86c-8352e25ea4f4"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="passwordreset",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("6e388fda-b31a-47c4-a86c-8352e25ea4f4"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="phonenumberverification",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("6e388fda-b31a-47c4-a86c-8352e25ea4f4"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="practitionerpracticecriteria",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("6e388fda-b31a-47c4-a86c-8352e25ea4f4"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="providerqualification",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("6e388fda-b31a-47c4-a86c-8352e25ea4f4"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="referral",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("6e388fda-b31a-47c4-a86c-8352e25ea4f4"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("fc9b1005-adb0-4145-8f1e-b31fc93e0345"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]