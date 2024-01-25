import datetime

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentication.patient_authentication_serializers.serializers import (
    CreatePatientProfileSerializer,
)
from utility.functools import (  # check_fields_required,; convert_success_message,; get_specific_user_with_email,
    convert_serializer_errors_from_dict_to_list,
    convert_to_error_message,
    convert_to_success_message_serialized_data,
    decrypt,
    encrypt,
)

from ..models import User


class PatientAuthenticationViewSet(GenericViewSet):
    queryset = User.objects.all()

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    @action(
        methods=["POST"],
        detail=False,
        url_name="create_patient_profile",
        permission_classes=[AllowAny],
        serializer_class=CreatePatientProfileSerializer,
    )
    def create_patient_profile(self, request):
        try:
            serialized_input = self.get_serializer(data=request.data)
            if not serialized_input.is_valid():
                return Response(
                    {
                        "message": "failure",
                        "data": "null",
                        "errors": convert_serializer_errors_from_dict_to_list(
                            serialized_input.errors
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            password = serialized_input.validated_data["password"]
            confirm_password = serialized_input.validated_data["confirm_password"]

            if password != confirm_password:
                return Response(
                    {
                        convert_to_error_message(
                            "Password and confirm password does not match"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            date_of_birth = serialized_input.validated_data["date_of_birth"]
            user_dob_date = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d").date()

            print(encrypt(serialized_input.validated_data["address"].capitalize()))
            new_user = User(
                first_name=encrypt(
                    serialized_input.validated_data["first_name"].capitalize()
                ),
                last_name=encrypt(
                    serialized_input.validated_data["last_name"].capitalize()
                ),
                email=serialized_input.validated_data["email"].lower(),
                phone_number=serialized_input.validated_data["phone_number"],
                address=encrypt(serialized_input.validated_data["address"].lower()),
                city=encrypt(serialized_input.validated_data["city"].capitalize()),
                country=serialized_input.validated_data["country"].capitalize(),
                gender=serialized_input.validated_data["gender"].lower(),
                state=serialized_input.validated_data["state"].capitalize(),
                date_of_birth=user_dob_date,
                preferred_communication=serialized_input.validated_data[
                    "preferred_communication"
                ].capitalize(),
                languages_spoken=serialized_input.validated_data["languages_spoken"],
                user_type="patient",
            )

            try:
                validate_password(password=password, user=new_user)
            except ValidationError as err:
                return Response(
                    convert_to_error_message(err), status=status.HTTP_400_BAD_REQUEST
                )

            new_user.set_password(password)
            new_user.save()

            output_response = {
                "first_name": decrypt(new_user.first_name),
                "last_name": decrypt(new_user.last_name),
                "email": new_user.email,
                "phone_number": new_user.phone_number,
                "address": decrypt(new_user.address),
                "city": decrypt(new_user.city),
                "country": new_user.country,
                "gender": new_user.gender,
                "state": new_user.state,
                "date_of_birth": new_user.date_of_birth.strftime("%d/%m/%Y"),
                "preferred_communication": new_user.preferred_communication,
                "user_type": new_user.user_type,
                "date_joined": new_user.date_joined.strftime("%d/%m/%Y, %H:%M:%S"),
            }

            print(output_response)
            return Response(
                convert_to_success_message_serialized_data(output_response),
                status=status.HTTP_201_CREATED,
            )

        except KeyError as e:
            return Response(
                convert_to_error_message(f"{e}"), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )
