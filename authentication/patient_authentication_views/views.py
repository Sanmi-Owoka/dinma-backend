import datetime

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.patient_authentication_serializers.serializers import (
    CreatePatientProfileSerializer,
    PatientLoginSerializer,
)
from utility.functools import (  # check_fields_required,; convert_success_message,;
    convert_serializer_errors_from_dict_to_list,
    convert_to_error_message,
    convert_to_success_message_serialized_data,
    decrypt_user_data,
    encrypt,
    get_specific_user_with_email,
)

from ..models import User


class PatientAuthenticationViewSet(GenericViewSet):
    queryset = User.objects.all()

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    @action(methods=["get"], detail=False, url_name="patient_details")
    def patient_details(self, request):
        try:
            user = request.user
            get_user = get_specific_user_with_email(user.email)
            if not get_user["status"]:
                return Response(
                    convert_to_error_message(get_user["response"]),
                    status=status.HTTP_404_NOT_FOUND,
                )
            get_user = get_user["response"]
            output_response = decrypt_user_data(get_user)
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

            output_response = decrypt_user_data(new_user)

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

    @action(
        methods=["POST"],
        detail=False,
        url_name="patient_Login",
        permission_classes=[AllowAny],
        serializer_class=PatientLoginSerializer,
    )
    def patient_Login(self, request):
        try:
            serialized_input = self.get_serializer(data=request.data)
            if not serialized_input.is_valid():
                return Response(
                    convert_to_error_message(
                        convert_serializer_errors_from_dict_to_list(
                            serialized_input.errors
                        )
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            email = serialized_input.validated_data["email"]
            password = serialized_input.validated_data["password"]

            get_user = get_specific_user_with_email(email.lower())
            if not get_user["status"]:
                return Response(
                    convert_to_error_message(get_user["response"]),
                    status=status.HTTP_404_NOT_FOUND,
                )
            get_user = get_user["response"]

            if not get_user.check_password(password):
                return Response(
                    convert_to_error_message("Invalid password"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = decrypt_user_data(get_user)

            token = RefreshToken.for_user(get_user)
            response = {"user": user, "token": str(token.access_token)}

            return Response(
                convert_to_success_message_serialized_data(response),
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
