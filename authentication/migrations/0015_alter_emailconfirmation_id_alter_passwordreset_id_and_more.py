# Generated by Django 4.2.9 on 2024-02-26 13:08

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "authentication",
            "0014_alter_emailconfirmation_id_alter_passwordreset_id_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="emailconfirmation",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("8c50d963-8b14-4706-ad96-f59aeeb1bcee"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="passwordreset",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("8c50d963-8b14-4706-ad96-f59aeeb1bcee"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="phonenumberverification",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("8c50d963-8b14-4706-ad96-f59aeeb1bcee"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="practitionerpracticecriteria",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("8c50d963-8b14-4706-ad96-f59aeeb1bcee"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="providerqualification",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("8c50d963-8b14-4706-ad96-f59aeeb1bcee"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="referral",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("8c50d963-8b14-4706-ad96-f59aeeb1bcee"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("b809e4a1-50da-4d88-991d-d451ee451410"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
