# Generated by Django 4.2.9 on 2024-02-26 10:09

import uuid

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "authentication",
            "0012_alter_emailconfirmation_id_alter_passwordreset_id_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="emailconfirmation",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("a5e16901-ebfb-41d2-a1be-abb45c85aa91"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="passwordreset",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("a5e16901-ebfb-41d2-a1be-abb45c85aa91"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="phonenumberverification",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("a5e16901-ebfb-41d2-a1be-abb45c85aa91"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="practitionerpracticecriteria",
            name="available_days",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.DateTimeField(blank=True, null=True), size=None
            ),
        ),
        migrations.AlterField(
            model_name="practitionerpracticecriteria",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("a5e16901-ebfb-41d2-a1be-abb45c85aa91"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="providerqualification",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("a5e16901-ebfb-41d2-a1be-abb45c85aa91"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="referral",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("a5e16901-ebfb-41d2-a1be-abb45c85aa91"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.UUIDField(
                default=uuid.UUID("6c490dcf-4e99-48f1-b4b9-2376d6921c7f"),
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
