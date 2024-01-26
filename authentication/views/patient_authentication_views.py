import datetime
import uuid

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import PasswordReset, User
from authentication.serializers.patient_authentication_serializers import (
    ChangePasswordSerializer,
    CreatePatientProfileSerializer,
    ForgotPasswordSerializer,
    PatientLoginSerializer,
)
from utility.functools import (
    check_fields_required,
    convert_serializer_errors_from_dict_to_list,
    convert_success_message,
    convert_to_error_message,
    convert_to_success_message_serialized_data,
    decrypt,
    decrypt_user_data,
    encrypt,
    get_specific_user_with_email,
)


class PatientAuthenticationViewSet(GenericViewSet):
    queryset = User.objects.all()
    serializer_class = CreatePatientProfileSerializer

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
            user_dob_date = datetime.datetime.strptime(date_of_birth, "%d-%m-%Y").date()

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

            if get_user.user_type != "patient":
                return Response(
                    convert_to_error_message("User not authorized to login"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

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

    @action(
        methods=["POST"],
        detail=False,
        url_name="change_password",
        permission_classes=[AllowAny],
        serializer_class=ChangePasswordSerializer,
    )
    def patient_change_password(self, request):
        try:
            #  Get the user object
            user_id = request.user.id
            user = User.objects.get(id=user_id)

            serialized_input = self.get_serializer(data=request.data)
            if not serialized_input.is_valid():
                return Response(
                    convert_to_error_message(serialized_input.errors),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get Input variables
            existing_password = serialized_input.validated_data["existing_password"]
            new_password = serialized_input.validated_data["new_password"]
            confirm_password = serialized_input.validated_data["confirm_password"]

            check_password_valid = user.check_password(existing_password)
            if not check_password_valid:
                return Response(
                    convert_to_error_message("Invalid password entered"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if new_password != confirm_password:
                return Response(
                    convert_to_error_message(
                        "Password Mismatch, check your new password and confirm password entered"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check user's previous password
            if existing_password == new_password:
                return Response(
                    convert_to_error_message(
                        "New password is the same with existing password"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate user's password with django validators
            try:
                validate_password(password=new_password, user=user)
            except ValidationError as err:
                return Response(
                    convert_to_error_message(err), status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(new_password)
            user.save()

            return Response(
                convert_success_message("Password updated successfully"),
                status=status.HTTP_200_OK,
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
        url_name="user_forgot_password_request",
        permission_classes=[AllowAny],
    )
    def forgot_password_request(self, request):
        try:
            email = request.data["email"]
            check_required = check_fields_required({"email": email})
            if not check_required["status"]:
                return Response(
                    convert_to_error_message(check_required["response"]),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            get_user = get_specific_user_with_email(email.lower())
            if not get_user["status"]:
                return Response(
                    convert_to_error_message(get_user["response"]),
                    status=status.HTTP_404_NOT_FOUND,
                )
            user = get_user["response"]

            token = "{}".format(uuid.uuid4().int >> 90)
            token = token[:6]
            PasswordReset.objects.filter(user=user).delete()
            get = PasswordReset.objects.create(user=user, token=token)

            # try:
            subject = "Password Reset code"
            from_email = settings.DEFAULT_FROM_EMAIL
            body = render_to_string(
                "email/password_reset.html",
                {
                    "token": token,
                    "first_name": decrypt(user.first_name),
                    "last_name": decrypt(user.last_name),
                },
            )
            message = EmailMessage(
                subject,
                body,
                to=[user.email],
                from_email=from_email,
            )
            message.content_subtype = "html"
            message.send(fail_silently=True)
            get.sent = True
            get.save()

            response = {
                "message": "Password Reset request successful",
                "token": token,
            }

            return Response(
                convert_to_success_message_serialized_data(response),
                status=status.HTTP_200_OK,
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
        url_name="confirm_forgot_password",
        serializer_class=ForgotPasswordSerializer,
        permission_classes=[AllowAny],
    )
    def confirm_forgot_password(self, request):
        try:
            serialized_input = self.get_serializer(data=request.data)
            if not serialized_input.is_valid():
                return Response(
                    convert_to_error_message(serialized_input.errors),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = serialized_input.validated_data["token"]
            new_password = serialized_input.validated_data["new_password"]
            confirm_password = serialized_input.validated_data["confirm_password"]

            get_record_of_password_reset = PasswordReset.objects.get(token=token)
            user = get_record_of_password_reset.user

            if new_password != confirm_password:
                return Response(
                    convert_to_error_message(
                        "Password Mismatch, check your new password and confirm password entered"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate user's password with django validators
            try:
                validate_password(password=new_password, user=user)
            except ValidationError as err:
                return Response(
                    convert_to_error_message(err), status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(new_password)
            user.save()

            get_record_of_password_reset.delete()

            return Response(
                convert_success_message("Password updated successfully"),
                status=status.HTTP_200_OK,
            )

        except PasswordReset.DoesNotExist:
            return Response(convert_to_error_message("Invalid Token entered"))

        except KeyError as e:
            return Response(
                convert_to_error_message(f"{e}"), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["PUT"],
        detail=False,
        url_name="edit_patient_profile",
        permission_classes=[IsAuthenticated],
    )
    def edit_patient_profile(self, request):
        try:
            logged_in_user = User.objects.get(id=request.user.id)

            if request.data.get("first_name"):
                logged_in_user.first_name = encrypt(
                    request.data.get("first_name").capitalize().strip()
                )
            if request.data.get("last_name"):
                logged_in_user.last_name = encrypt(
                    request.data.get("last_name").capitalize().strip()
                )
            if request.data.get("address"):
                logged_in_user.address = encrypt(
                    request.data.get("address").lower().strip()
                )
            if request.data.get("date_of_birth"):
                date_of_birth = request.data.get("date_of_birth")
                user_dob_date = datetime.datetime.strptime(
                    date_of_birth, "%d-%m-%Y"
                ).date()
                logged_in_user.date_of_birth = user_dob_date
            if request.data.get("gender"):
                logged_in_user.gender = request.data.get("gender").lower().strip()
            if request.data.get("city"):
                logged_in_user.city = encrypt(
                    request.data.get("city").capitalize().strip()
                )
            if request.data.get("state"):
                logged_in_user.state = request.data.get("state").capitalize().strip()
            if request.data.get("country"):
                logged_in_user.country = (
                    request.data.get("country").capitalize().strip()
                )
            if request.data.get("language_spoken"):
                logged_in_user.language_spoken = request.data.get(
                    "language_spoken"
                ).strip()
            if request.data.get("preferred_language"):
                logged_in_user.preferred_language = request.data.get(
                    "preferred_language"
                )

            # save partial update
            logged_in_user.save()
            response = decrypt_user_data(logged_in_user)
            return Response(
                convert_to_success_message_serialized_data(response),
                status=status.HTTP_200_OK,
            )

        except KeyError as e:
            return Response(
                convert_to_error_message(f"{e}"), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )
