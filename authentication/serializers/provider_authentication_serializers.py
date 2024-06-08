import datetime

from django.db import transaction
from django.utils.timezone import make_aware
from rest_framework import serializers

from authentication.models import (
    PractitionerAvailableDateTime,
    PractitionerPracticeCriteria,
    ProviderQualification,
    User,
    UserAccountDetails,
)
from utility.helpers.functools import decrypt

# Getting the current date


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

    speciality = serializers.CharField(
        allow_blank=True, max_length=255, trim_whitespace=True
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
    age_range = serializers.CharField(
        required=True, max_length=255, trim_whitespace=True
    )

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
            "speciality",
            "NPI",
            "CAQH",
            "licensed_states",
            # practitioner criteria
            "practice_name",
            "max_distance",
            "preferred_zip_codes",
            "available_days",
            "age_range",
            # password
            "password",
            "confirm_password",
            "referral_code",
            "username",
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
            "minimum_age",
        ]
        read_only_fiields = [
            "id",
            "practice_name",
            "max_distance",
            "preferred_zip_codes",
            "available_days",
            "minimum_age",
        ]


class ProviderQualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderQualification
        fields = "__all__"


class SimpleDecryptedProviderDetails(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    licensed_states = serializers.SerializerMethodField()
    practice_criteria = serializers.SerializerMethodField()
    provider_qualification = serializers.SerializerMethodField()

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
            "provider_qualification",
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
            "provider_qualification",
        ]

    def to_representation(self, instance: User):
        current_date = make_aware(datetime.datetime.now())
        response = super().to_representation(instance)
        # print(dict(response))
        serialized_data = dict(response)
        practice_criteria: str = serialized_data["practice_criteria"]["id"]

        request = self.context.get("request")
        if request:
            if request.data.get("date_care_is_needed"):
                date_care_is_needed = request.data["date_care_is_needed"]
                date_time_obj = (
                    PractitionerAvailableDateTime.objects.filter(
                        provider_criteria__id=practice_criteria,
                        available_date_time__date=date_care_is_needed,
                    )
                    .values_list("available_date_time", flat=True)
                    .distinct()
                )
                date_time_list = list(date_time_obj)
                response["available_date_time"] = date_time_list

        available_days = (
            PractitionerAvailableDateTime.objects.filter(
                provider_criteria__id=practice_criteria,
                available_date_time__gte=current_date,
            )
            .values_list("available_date_time", flat=True)
            .distinct()
        )

        # print(available_days)
        response["practice_criteria"]["available_days"] = list(available_days)
        return response

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
            if instance.photo:
                return self.context["request"].build_absolute_uri(instance.photo.url)
            else:
                return None
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

    def get_provider_qualification(self, instance):
        try:
            get_provider_qualification = ProviderQualification.objects.get(
                user=instance
            )
            return ProviderQualificationSerializer(get_provider_qualification).data
        except Exception as e:
            print("Error", e)
            return None


class PractitionerAvailableDateTimeSerializer(serializers.Serializer):
    available_days = serializers.ListField(
        child=serializers.CharField(
            required=False, max_length=255, trim_whitespace=True, write_only=True
        )
    )


class UpdateProviderSerializer(serializers.ModelSerializer):
    practioner_type = serializers.CharField(
        required=False, max_length=255, allow_blank=True
    )
    credential_title = serializers.CharField(
        required=False, max_length=255, allow_blank=True
    )
    NPI = serializers.CharField(required=False, max_length=255, allow_blank=True)
    CAQH = serializers.CharField(required=False, max_length=255, allow_blank=True)
    licensed_states = serializers.ListField(
        child=serializers.CharField(required=False, max_length=255, allow_blank=True)
    )
    preferred_zip_codes = serializers.ListField(
        child=serializers.CharField(required=False, max_length=255, allow_blank=True)
    )
    age_range = serializers.CharField(required=False, max_length=255, allow_blank=True)

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
            "date_joined",
            # provider qualiification
            "practioner_type",
            "credential_title",
            "NPI",
            "CAQH",
            "licensed_states",
            # provider criteria
            "preferred_zip_codes",
            "age_range",
        ]

        read_only_fields = [
            "id",
            "email",
            "phone_number",
            "date_joined",
        ]


class EditPractionerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    preferred_communication = serializers.CharField(required=False, allow_blank=True)
    languages_spoken = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(
            required=False, max_length=255, trim_whitespace=True
        ),
    )

    #   Practitioner Credentials
    practioner_type = serializers.CharField(required=False, allow_blank=True)
    credential_title = serializers.CharField(required=False, allow_blank=True)
    speciality = serializers.CharField(required=False, allow_blank=True)

    licensed_states = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(
            required=False, max_length=255, trim_whitespace=True
        ),
    )

    # Practitioner Criteria
    practice_name = serializers.CharField(required=False, allow_blank=True)

    max_distance = serializers.IntegerField()
    preferred_zip_codes = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(
            required=False, max_length=255, trim_whitespace=True
        ),
    )
    age_range = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
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
            "speciality",
            "licensed_states",
            # practitioner criteria
            "practice_name",
            "max_distance",
            "preferred_zip_codes",
            "age_range",
        ]
        read_only_fields = ["id", "date_joined", "username"]

    def to_representation(self, instance: User):
        current_date = make_aware(datetime.datetime.now())
        response = super().to_representation(instance)
        # print(dict(response))
        serialized_data = dict(response)
        practice_criteria: str = serialized_data["practice_criteria"]["id"]
        available_days = (
            PractitionerAvailableDateTime.objects.filter(
                provider_criteria__id=practice_criteria,
                available_date_time__gte=current_date,
            )
            .values_list("available_date_time", flat=True)
            .distinct()
        )

        # print(available_days)
        response["practice_criteria"]["available_days"] = list(available_days)
        return response

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
            if instance.photo:
                return self.context["request"].build_absolute_uri(instance.photo.url)
            else:
                return None
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

    def get_practice_qualification(self, instance):
        try:
            get_practice_qualification = ProviderQualification.objects.get(
                user=instance
            )
            return {
                "practioner_type": get_practice_qualification.practioner_type,
                "credential_title": get_practice_qualification.credential_title,
                "licensed_states": get_practice_qualification.licensed_states,
            }
        except Exception as e:
            print("Error", e)
            return None


class UserAccountDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccountDetails
        fields = "__all__"
        read_only_fields = [
            "user",
        ]

    def to_representation(self, instance):
        if isinstance(instance, tuple):
            instance = instance[0]
        response = super().to_representation(instance)
        response["user"] = self.context["request"].user.id
        return response

    def create(self, validated_data):
        request = self.context["request"]
        print(request)
        validated_data["user"] = request.user
        return UserAccountDetails.objects.get_or_create(**validated_data)

    @transaction.atomic()
    def update(self, validated_data):
        user_account_details = UserAccountDetails.objects.filter(
            user=self.context["request"].user
        ).update(**validated_data)
        return user_account_details
