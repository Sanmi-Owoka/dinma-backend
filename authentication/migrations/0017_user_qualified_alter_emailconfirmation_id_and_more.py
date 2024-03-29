# Generated by Django 4.2.9 on 2024-02-27 14:30

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "authentication",
            "0016_alter_emailconfirmation_id_alter_passwordreset_id_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="qualified",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="emailconfirmation",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("b4a3708e-a193-4271-9051-a8b784334cd7"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="passwordreset",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("b4a3708e-a193-4271-9051-a8b784334cd7"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="phonenumberverification",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("b4a3708e-a193-4271-9051-a8b784334cd7"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="practitionerpracticecriteria",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("b4a3708e-a193-4271-9051-a8b784334cd7"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="providerqualification",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("b4a3708e-a193-4271-9051-a8b784334cd7"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="referral",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("b4a3708e-a193-4271-9051-a8b784334cd7"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("0b3f46b8-a855-4811-802a-0ea4bab40c5c"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
