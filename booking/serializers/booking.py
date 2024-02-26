from rest_framework import serializers

from booking.models import UserBookingDetails


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
        ]
