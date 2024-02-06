from rest_framework import serializers

from authentication.models import User


class OnboardPractionerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        required=True, max_length=50, trim_whitespace=True
    )
    last_name = serializers.CharField(
        required=True, max_length=50, trim_whitespace=True
    )
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(
        required=True, max_length=20, trim_whitespace=True
    )
    address = serializers.CharField(required=True, max_length=150, trim_whitespace=True)
    date_of_birth = serializers.CharField(
        required=True, max_length=150, trim_whitespace=True
    )
    gender = serializers.CharField(required=True, max_length=50, trim_whitespace=True)
    city = serializers.CharField(required=True, max_length=50, trim_whitespace=True)
    state = serializers.CharField(required=True, max_length=50, trim_whitespace=True)
    preferred_communication = serializers.CharField(
        required=True, max_length=255, trim_whitespace=True
    )
    languages_spoken = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(
            required=True, max_length=255, trim_whitespace=True
        ),
    )

    #   Practitioner Credentials
    practioner_type = serializers.CharField(
        allow_blank=True, max_length=50, trim_whitespace=True
    )
    credential_title = serializers.CharField(
        allow_blank=True, max_length=50, trim_whitespace=True
    )

    NPI = serializers.CharField(required=True, max_length=200, trim_whitespace=True)
    CAQH = serializers.CharField(required=True, max_length=200, trim_whitespace=True)
    licensed_states = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(
            required=True, max_length=255, trim_whitespace=True
        ),
    )

    # Practitioner Criteria
    practice_name = serializers.CharField(
        required=True, max_length=255, trim_whitespace=True
    )
    max_distance = serializers.IntegerField(min_value=0)
    preferred_zip_codes = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(
            required=False, max_length=255, trim_whitespace=True
        ),
    )
    available_days = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(
            required=False, max_length=255, trim_whitespace=True
        ),
    )
    price_per_consultation = serializers.DecimalField(max_digits=12, decimal_places=2)
    minimum_age = serializers.IntegerField(min_value=0)
    maximum_age = serializers.IntegerField(min_value=0)

    # Password
    password = serializers.CharField(
        required=True,
        max_length=150,
        min_length=4,
        trim_whitespace=True,
        write_only=True,
    )
    confirm_password = serializers.CharField(
        required=True,
        max_length=150,
        min_length=4,
        trim_whitespace=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "address",
            "date_of_birth",
            "gender",
            "city",
            "state",
            "preferred_communication",
            "languages_spoken",
            # practitioner credentials
            "practioner_type",
            "credential_title",
            "NPI",
            "CAQH",
            "licensed_states",
            # practitioner criteria
            "practice_name",
            "max_distance",
            "preferred_zip_codes",
            "available_days",
            "price_per_consultation",
            "minimum_age",
            "maximum_age",
            # password
            "password",
            "confirm_password",
        ]
        read_only_fields = [
            "id",
            "date_joined",
        ]
