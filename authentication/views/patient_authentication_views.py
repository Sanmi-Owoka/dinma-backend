import datetime
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import (
    EmailConfirmation,
    InsuranceDetails,
    PasswordReset,
    PhoneNumberVerification,
    User,
)
from authentication.serializers.patient_authentication_serializers import (
    ChangePasswordSerializer,
    CreatePatientProfileSerializer,
    ForgotPasswordSerializer,
    InsuranceDetailsSerializer,
    PatientLoginSerializer,
)
from authentication.utils import (
    generate_phone_unique_code,
    generate_unique_code,
    send_email_verification,
)
from utility.helpers.functools import (
    base64_to_data,
    check_fields_required,
    convert_serializer_errors_from_dict_to_list,
    convert_success_message,
    convert_to_error_message,
    convert_to_success_message_serialized_data,
    decrypt,
    decrypt_user_data,
    encrypt,
    generate_unique_id,
    get_specific_user_with_email,
)
from utility.helpers.send_sms import send_plain_SMS
from utility.services.pverify import Pverify


@extend_schema(tags=["Patient authentication endpoints"])
class PatientAuthenticationViewSet(GenericViewSet):
    queryset = User.objects.all()
    serializer_class = CreatePatientProfileSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    @action(methods=["GET"], detail=False, url_name="patient_details")
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

            output_response = decrypt_user_data(get_user, request)

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

            output_response = decrypt_user_data(new_user, request)

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

            # if get_user.user_type != "patient":
            #     return Response(
            #         convert_to_error_message("User not authorized to login"),
            #         status=status.HTTP_400_BAD_REQUEST,
            #     )

            if not get_user.check_password(password):
                return Response(
                    convert_to_error_message("Invalid password"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = decrypt_user_data(get_user, request)

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

            # Check if record of password reset has expired
            if get_record_of_password_reset.check_expire:
                get_record_of_password_reset.delete()
                return Response(
                    convert_to_error_message(
                        "Password reset link has expired, please request a new one"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
    def edit_profile(self, request):
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
            if request.data.get("language_spoken"):
                logged_in_user.language_spoken = request.data.get(
                    "language_spoken"
                ).strip()
            if request.data.get("preferred_language"):
                logged_in_user.preferred_language = request.data.get(
                    "preferred_language"
                )
            if request.data.get("photo"):
                logged_in_user.photo = base64_to_data(request.data.get("photo"))

            # save partial update
            logged_in_user.save()
            response = decrypt_user_data(logged_in_user, request)
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

    @action(detail=False, methods=["POST"], permission_classes=[AllowAny])
    def send_email_verification(self, request):
        try:
            email = request.data["email"]
            if not email:
                return Response(
                    convert_to_error_message("Email is required"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = generate_unique_code()

            # Check if email already verified
            check_email_verification = EmailConfirmation.objects.filter(
                email=email, is_verified=True
            )
            if check_email_verification.exists():
                return Response(
                    convert_to_error_message("Email already verified"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            EmailConfirmation.objects.filter(email=email).delete()
            email_confirmation_obj = EmailConfirmation.objects.create(
                email=email,
                token=token,
            )
            send_email_verification(email, token)
            email_confirmation_obj.sent = True
            email_confirmation_obj.save()
            return Response(
                convert_success_message("Email verification sent successfully"),
                status=status.HTTP_200_OK,
            )
        except KeyError as e:
            print("error", e)
            return Response(
                {"message": [f"{e} is required"]}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print("error", e)
            return Response({"message": [f"{e}"]}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["POST"], detail=False, permission_classes=[AllowAny])
    def confirm_email(self, request):
        try:
            token = request.data["token"]
            if not token:
                return Response(
                    convert_to_error_message("Token is required"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # check email confirmation with token
            confirm_email = EmailConfirmation.objects.filter(token=token)
            if not confirm_email.exists():
                return Response(
                    convert_to_error_message("Invalid Email verification code entered"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            confirm_email = confirm_email.first()

            # Check if token has expired
            if confirm_email.check_expire:
                return Response(
                    convert_to_error_message("token expired"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            confirm_email.is_verified = True
            confirm_email.save()

            return Response(
                convert_success_message("Email verified successfully"),
                status=status.HTTP_200_OK,
            )
        except KeyError as e:
            print("error", e)
            return Response(
                {"message": [f"{e} is required"]}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print("error", e)
            return Response({"message": [f"{e}"]}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["POST"], detail=False, permission_classes=[AllowAny])
    def send_phone_verification(self, request):
        try:
            phone_number = request.data["phone_number"]
            if not phone_number:
                return Response(
                    convert_to_error_message("Phone number is required"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = generate_phone_unique_code()

            check_phone_verification = PhoneNumberVerification.objects.filter(
                phone_number=phone_number,
                is_verified=True,
            )
            if check_phone_verification.exists():
                return Response(
                    convert_to_error_message("Phone number already verified"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            PhoneNumberVerification.objects.filter(phone_number=phone_number).delete()
            phone_verification_obj = PhoneNumberVerification.objects.create(
                id=generate_unique_id(PhoneNumberVerification),
                phone_number=phone_number,
                token=token,
            )
            message_text = f"Your Dinma confirmation code is {token}"
            new_message = send_plain_SMS(phone_number, message_text)
            print(new_message)
            phone_verification_obj.sent = True
            phone_verification_obj.save()
            return Response(
                convert_success_message("Phone number verification sent successfully"),
                status=status.HTTP_200_OK,
            )
        except KeyError as e:
            print("error", e)
            return Response(
                {"message": [f"{e} is required"]}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print("error", e)
            return Response({"message": [f"{e}"]}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["POST"], permission_classes=[AllowAny])
    def confirm_phone_number_verification(self, request):
        try:
            token = request.data["token"]
            if not token:
                return Response(
                    convert_to_error_message("Token is required"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # check email confirmation with token
            confirm_phone_verification = PhoneNumberVerification.objects.filter(
                token=token
            )
            if not confirm_phone_verification.exists():
                return Response(
                    convert_to_error_message("Invalid Phone verification code entered"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            confirm_phone_verification = confirm_phone_verification.first()

            # Check if token has expired
            if confirm_phone_verification.check_expire:
                return Response(
                    convert_to_error_message("token expired"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            confirm_phone_verification.is_verified = True
            confirm_phone_verification.save()

            return Response(
                convert_success_message("Phone number verified successfully"),
                status=status.HTTP_200_OK,
            )
        except KeyError as e:
            print("error", e)
            return Response(
                {"message": [f"{e} is required"]}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print("error", e)
            return Response({"message": [f"{e}"]}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["POST"],
        detail=False,
        serializer_class=InsuranceDetailsSerializer,
        permission_classes=[AllowAny],
    )
    def verify_patient_insurance(self, request):
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
            user_id = serialized_input.validated_data["user_id"]
            user = User.objects.filter(id=user_id)
            if not user.exists():
                return Response(
                    convert_to_error_message("User not found"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = user.first()

            check_insurance_details_exists = InsuranceDetails.objects.filter(
                user=user
            ).exists()
            if check_insurance_details_exists:
                return Response(
                    convert_to_error_message("User already has Insurance verified"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            insurance_company_name = serialized_input.validated_data[
                "insurance_company_name"
            ]
            insurance_phone_number = serialized_input.validated_data[
                "insurance_phone_number"
            ]
            insurance_policy_number = serialized_input.validated_data[
                "insurance_policy_number"
            ]
            insurance_group_number = serialized_input.validated_data[
                "insurance_group_number"
            ]
            insured_date_of_birth = serialized_input.validated_data[
                "insured_date_of_birth"
            ]
            patient_relationship = serialized_input.validated_data[
                "patient_relationship"
            ]

            dob_list = insured_date_of_birth.split("/")
            if len(dob_list) != 3:
                return Response(
                    convert_to_error_message("Invalid date of birth"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            dob = f"{dob_list[1]}/{dob_list[0]}/{dob_list[2]}"

            insurance_obj = Pverify().verify_insurance(
                insurance_company_name,
                insurance_policy_number,
                dob,
                patient_relationship,
            )

            if not insurance_obj["status"]:
                return Response(
                    convert_to_error_message(insurance_obj["response"]),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            get_insurance_total = Pverify().complete_insurance_verification(
                insurance_obj["response"], patient_relationship
            )
            if get_insurance_total["status"] == "failure":
                return Response(
                    convert_to_error_message(get_insurance_total["response"]),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            insurance_coverage = Decimal(get_insurance_total["insurance_coverage"])
            self_pay = Decimal(get_insurance_total["amount"])

            insurance_details_obj = InsuranceDetails.objects.create(
                user=user,
                insurance_company_name=insurance_company_name,
                insurance_phone_number=insurance_phone_number,
                insurance_policy_number=insurance_policy_number,
                insurance_group_number=insurance_group_number,
                insured_date_of_birth=insured_date_of_birth,
                patient_relationship=patient_relationship,
                self_pay=self_pay,
                insurance_coverage=insurance_coverage,
            )

            response = self.get_serializer(insurance_details_obj)
            return Response(
                convert_to_success_message_serialized_data(response.data),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print("error", e)
            return Response({"message": [f"{e}"]}, status=status.HTTP_400_BAD_REQUEST)
