import datetime

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentication.models import (
    PractitionerAvailableDateTime,
    PractitionerPracticeCriteria,
    ProviderQualification,
    Referral,
    User,
)
from authentication.serializers.provider_authentication_serializers import (
    OnboardPractionerSerializer,
    PractitionerAvailableDateTimeSerializer,
    SimpleDecryptedProviderDetails,
)
from authentication.utils import start_schedule_background_tasks
from utility.helpers.functools import (
    base64_to_data,
    convert_serializer_errors_from_dict_to_list,
    convert_to_error_message,
    convert_to_success_message_serialized_data,
    decrypt_user_data,
    encrypt,
    paginate,
)

# from rest_framework_simplejwt.tokens import RefreshToken


@extend_schema(tags=["Practitioner authentication endpoints"])
class PractionerViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = OnboardPractionerSerializer

    def get_queryset(self):
        return User.objects.get(id=self.request.user.id)

    @action(
        methods=["POST"],
        detail=False,
        url_name="onboard_practioner",
        permission_classes=[AllowAny],
    )
    def onboard_practioner(self, request):
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

            check_user_exists = User.objects.filter(
                email=serialized_input.validated_data["email"].lower()
            )
            if check_user_exists.exists():
                return Response(
                    convert_to_error_message("User with this email already exists"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
                user_type="health_provider",
                social_security_number=serialized_input.validated_data[
                    "social_security_number"
                ],
            )

            try:
                validate_password(password=password, user=new_user)
            except ValidationError as err:
                return Response(
                    convert_to_error_message(err), status=status.HTTP_400_BAD_REQUEST
                )
            if request.data.get("photo"):
                new_user.photo = base64_to_data(request.data.get("photo"))

            if serialized_input.validated_data.get("referral_code"):
                referral_code = serialized_input.validated_data["referral_code"]
                from_user = User.objects.filter(username=referral_code)

                if not from_user.exists():
                    return Response(
                        {convert_to_error_message("Invalid referral code")},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    Referral.objects.create(
                        from_user=from_user.first(),
                        to_user=new_user,
                        type="practitioner",
                        reference_code=referral_code,
                    )

            age_range = serialized_input.validated_data["age_range"].capitalize()
            if age_range not in ["Pediatrician", "Adult", "Both"]:
                return Response(
                    convert_to_error_message(
                        f"you entered {age_range}, age range choices are Pediatrician and Adult"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            new_user.set_password(password)
            new_user.save()

            new_provider_qualification = ProviderQualification.objects.create(
                user=new_user,
                practioner_type=serialized_input.validated_data["practioner_type"],
                credential_title=serialized_input.validated_data["credential_title"],
                NPI=serialized_input.validated_data["NPI"],
                CAQH=serialized_input.validated_data["CAQH"],
                licensed_states=serialized_input.validated_data["licensed_states"],
            )
            new_provider_qualification.save()

            if age_range == "Pediatrician":
                maximum_age = 18
                minimum_age = 0
            elif age_range == "Adult":
                maximum_age = 100
                minimum_age = 18
            else:
                maximum_age = 100
                minimum_age = 0
            new_provider_criteria = PractitionerPracticeCriteria.objects.create(
                user=new_user,
                practice_name=serialized_input.validated_data["practice_name"],
                max_distance=serialized_input.validated_data["max_distance"],
                preferred_zip_codes=serialized_input.validated_data[
                    "preferred_zip_codes"
                ],
                available_days=serialized_input.validated_data["available_days"],
                age_range=serialized_input.validated_data["age_range"],
                minimum_age=minimum_age,
                maximum_age=maximum_age,
            )

            new_provider_criteria.save()

            start_schedule_background_tasks(
                days_and_time=serialized_input.validated_data["available_days"],
                provider_criteria=new_provider_criteria,
            )

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
        methods=["GET"],
        detail=False,
        url_name="Get all health providers",
        permission_classes=[AllowAny],
        serializer_class=SimpleDecryptedProviderDetails,
    )
    def get_all_health_providers(self, request):
        try:
            all_providers = User.objects.filter(
                user_type="health_provider",
            )
            return Response(
                convert_to_success_message_serialized_data(
                    paginate(
                        all_providers,
                        int(request.query_params.get("page", 1)),
                        self.get_serializer,
                        {"request": request},
                        int(request.query_params.get("limit", 10)),
                    )
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["POST"],
        detail=False,
        url_name="create availability",
        serializer_class=PractitionerAvailableDateTimeSerializer,
    )
    def create_availability(self, request):
        try:
            user = self.get_queryset()

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
            practice_criteria = PractitionerPracticeCriteria.objects.get(user=user)

            practice_criteria.available_days = []
            practice_criteria.save()

            PractitionerAvailableDateTime.objects.filter(
                provider_criteria=practice_criteria
            ).delete()

            start_schedule_background_tasks(
                days_and_time=serialized_input.validated_data["available_days"],
                provider_criteria=practice_criteria,
            )
            practice_criteria.available_days = serialized_input.validated_data[
                "available_days"
            ]
            practice_criteria.save()

            output_response = SimpleDecryptedProviderDetails(user).data

            return Response(
                convert_to_success_message_serialized_data(output_response),
                status=status.HTTP_201_CREATED,
            )

        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["GET"],
        detail=False,
        url_name="Get available dates",
        permission_classes=[AllowAny],
    )
    def get_available_days(self, request):
        try:
            user = self.get_queryset()
            practice_criteria = PractitionerPracticeCriteria.objects.get(user=user)
            return Response(
                convert_to_success_message_serialized_data(
                    practice_criteria.available_days
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="email", description="booking status", type=str, required=False
            ),
        ]
    )
    @action(
        methods=["GET"], detail=False, serializer_class=SimpleDecryptedProviderDetails
    )
    def get_health_provider_details(self, request):
        try:
            email = request.query_params.get("email", None)

            provider = User.objects.filter(email=email)
            if not provider.exists():
                return Response(
                    convert_to_error_message("No provider found"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            provider = provider.first()
            output_response = self.get_serializer(provider)

            return Response(
                convert_to_success_message_serialized_data(output_response.data),
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )
