from rest_framework import serializers

from authentication.models import PractitionerPracticeCriteria
from authentication.serializers.provider_authentication_serializers import (
    SimpleDecryptedProviderDetails,
)
from booking.models import UserBookingDetails
from utility.helpers.functools import decrypt


class BookingSerializer(serializers.ModelSerializer):
    symptom = serializers.CharField(required=True, max_length=50, trim_whitespace=True)
    date_care_is_needed = serializers.DateField(required=True)
    age_of_patient = serializers.IntegerField(required=True)
    zipcode = serializers.CharField(required=True, max_length=50, trim_whitespace=True)

    class Meta:
        model = UserBookingDetails
        fields = [
            "symptom",
            "date_care_is_needed",
            "age_of_patient",
            "zipcode",
            "status",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
        ]


class CreateBookingSerializer(serializers.ModelSerializer):
    practitioner_email = serializers.EmailField(
        required=True, max_length=50, trim_whitespace=True, write_only=True
    )
    date_time_of_care = serializers.DateTimeField(required=True)
    booking_id = serializers.CharField(
        required=True, max_length=50, trim_whitespace=True, write_only=True
    )
    practitioner = serializers.SerializerMethodField()

    class Meta:
        model = UserBookingDetails
        fields = [
            "id",
            "practitioner_email",
            "date_time_of_care",
            "booking_id",
            "symptom",
            "date_care_is_needed",
            "age_of_patient",
            "zipcode",
            "status",
            "practitioner",
            "reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "practitioner",
            "symptom",
            "date_care_is_needed",
            "age_of_patient",
            "zipcode",
            "status",
            "reason",
            "created_at",
            "updated_at",
        ]

    def get_practitioner(self, instance):
        try:
            if instance.practitioner:
                return SimpleDecryptedProviderDetails(instance.practitioner).data
            else:
                return None
        except Exception as e:
            print(e)
            return None


class GetProviderBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBookingDetails
        fields = [
            "id",
            "date_care_is_needed",
            "age_of_patient",
            "zipcode",
            "status",
            "date_time_of_care",
            "reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "symptom",
            "date_care_is_needed",
            "age_of_patient",
            "zipcode",
            "status",
            "date_time_of_care",
            "reason",
            "created_at",
            "updated_at",
        ]


class ConfirmBookingSerializer(serializers.ModelSerializer):
    booking_id = serializers.CharField(
        required=True, max_length=50, trim_whitespace=True, write_only=True
    )

    class Meta:
        model = UserBookingDetails
        fields = [
            "booking_id",
            "id",
            "date_care_is_needed",
            "age_of_patient",
            "zipcode",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "symptom",
            "date_care_is_needed",
            "age_of_patient",
            "zipcode",
            "status",
            "created_at",
            "updated_at",
        ]


class RejectBookingSerializer(serializers.ModelSerializer):
    booking_id = serializers.CharField(
        required=True, max_length=50, trim_whitespace=True, write_only=True
    )
    reason = serializers.CharField(
        required=True,
        max_length=50,
        trim_whitespace=True,
    )

    class Meta:
        model = UserBookingDetails
        fields = [
            "booking_id",
            "reason",
            "id",
            "date_care_is_needed",
            "age_of_patient",
            "zipcode",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "symptom",
            "date_care_is_needed",
            "age_of_patient",
            "zipcode",
            "status",
            "created_at",
            "updated_at",
        ]


class ListUserBookingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBookingDetails
        fields = "__all__"

    def to_representation(self, instance: UserBookingDetails):
        response = super().to_representation(instance)

        response["patient"] = {
            "id": instance.patient.id,
            "first_name": decrypt(instance.patient.first_name),
            "last_name": decrypt(instance.patient.last_name),
            "email": instance.patient.email,
            "address": decrypt(instance.patient.address),
            "gender": instance.patient.gender,
        }
        if instance.patient.photo:
            response["patient"]["photo"] = instance.patient.photo.url
        response["patient"]["photo"] = None

        if instance.practitioner:
            criteria = PractitionerPracticeCriteria.objects.get(
                user=instance.practitioner
            )
            provider = {
                "id": instance.practitioner.id,
                "first_name": decrypt(instance.practitioner.first_name),
                "last_name": decrypt(instance.practitioner.last_name),
                "email": instance.practitioner.email,
                "gender": instance.practitioner.gender,
                "title": criteria.practice_name,
            }
            if instance.practitioner.photo:
                provider["photo"] = instance.practitioner.photo.url
            else:
                provider["photo"] = None
            response["practitioner"] = provider
        else:
            response["practitioner"] = None

        return response


class RescheduleBookingRequestSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField(required=True)
    day_care_is_needed = serializers.DateField(required=False)
    date_time_care_is_needed = serializers.DateTimeField(required=False)
