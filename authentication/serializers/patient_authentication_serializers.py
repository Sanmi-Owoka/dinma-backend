from rest_framework import serializers

from authentication.models import User
from utility.helpers.functools import decrypt


class CreatePatientProfileSerializer(serializers.ModelSerializer):
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
            "password",
            "confirm_password",
        ]
        read_only_fields = [
            "id",
            "date_joined",
        ]


class PatientLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, max_length=150, trim_whitespace=True
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
        ]


class ChangePasswordSerializer(serializers.ModelSerializer):
    existing_password = serializers.CharField(
        required=True,
        max_length=150,
        min_length=4,
        trim_whitespace=True,
        write_only=True,
    )
    new_password = serializers.CharField(
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
            "existing_password",
            "new_password",
            "confirm_password",
        ]


class ForgotPasswordSerializer(serializers.ModelSerializer):
    token = serializers.CharField(
        required=True,
        max_length=150,
        min_length=4,
        trim_whitespace=True,
        write_only=True,
    )
    new_password = serializers.CharField(
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
            "token",
            "new_password",
            "confirm_password",
        ]


class SimpleDecryptedUserDetails(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "photo",
            "first_name",
            "last_name",
            "email",
            "gender",
            "user_type,",
        ]

        read_only_fields = [
            "id",
            "photo",
            "first_name",
            "last_name",
            "email",
            "gender",
            "user_type,",
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
