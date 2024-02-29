from rest_framework import serializers

from authentication.models import (
    PractitionerPracticeCriteria,
    ProviderQualification,
    User,
)
from utility.helpers.functools import decrypt


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

    social_security_number = serializers.CharField(
        required=True, max_length=255, trim_whitespace=True
    )

    # referral_code
    referral_code = serializers.CharField(
        required=False,
        max_length=150,
        min_length=4,
        trim_whitespace=True,
        allow_blank=True,
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
            "referral_code",
            "username",
            "social_security_number",
        ]
        read_only_fields = ["id", "date_joined", "username"]


class PractitionerPracticeCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PractitionerPracticeCriteria
        fields = [
            "id",
            "practice_name",
            "max_distance",
            "preferred_zip_codes",
            "available_days",
            "price_per_consultation",
            "minimum_age",
        ]
        read_only_fiields = [
            "id",
            "practice_name",
            "max_distance",
            "preferred_zip_codes",
            "available_days",
            "price_per_consultation",
            "minimum_age",
        ]


class SimpleDecryptedProviderDetails(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    licensed_states = serializers.SerializerMethodField()
    practice_criteria = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "photo",
            "first_name",
            "last_name",
            "email",
            "gender",
            "preferred_communication",
            "languages_spoken",
            "user_type",
            "licensed_states",
            "practice_criteria",
        ]

        read_only_fields = [
            "id",
            "photo",
            "first_name",
            "last_name",
            "email",
            "gender",
            "user_type",
            "licensed_states",
            "practice_criteria",
        ]

    def get_first_name(self, instance):
        try:
            return decrypt(instance.first_name)
        except Exception as e:
            print("Error", e)
            return None

    def get_last_name(self, instance):
        try:
            return decrypt(instance.last_name)
        except Exception as e:
            print("Error", e)
            return None

    def get_photo(self, instance):
        try:
            return self.context["request"].build_absolute_uri(instance.photo.url)
        except Exception as e:
            print("Error", e)
            return None

    def get_licensed_states(self, instance):
        try:
            get_licensed_states = ProviderQualification.objects.get(
                user=instance
            ).licensed_states
            return get_licensed_states
        except Exception as e:
            print("Error", e)
            return None

    def get_practice_criteria(self, instance):
        try:
            get_practice_criteria = PractitionerPracticeCriteria.objects.get(
                user=instance
            )
            return PractitionerPracticeCriteriaSerializer(get_practice_criteria).data
        except Exception as e:
            print("Error", e)
            return None
