import datetime

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentication.models import (
    PractitionerPracticeCriteria,
    ProviderQualification,
    User,
)
from authentication.serializers.provider_authentication_serializers import (
    OnboardPractionerSerializer,
)
from utility.helpers.functools import (
    convert_serializer_errors_from_dict_to_list,
    convert_to_error_message,
    convert_to_success_message_serialized_data,
    decrypt_user_data,
    encrypt,
)

# from rest_framework_simplejwt.tokens import RefreshToken


@extend_schema(tags=["Practitioner authentication endpoints"])
class PractionerViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = OnboardPractionerSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

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
                user_type="provider",
            )

            try:
                validate_password(password=password, user=new_user)
            except ValidationError as err:
                return Response(
                    convert_to_error_message(err), status=status.HTTP_400_BAD_REQUEST
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

            new_provider_criteria = PractitionerPracticeCriteria.objects.create(
                practice_name=serialized_input.validated_data["practice_name"],
                max_distance=serialized_input.validated_data["max_distance"],
                preferred_zip_codes=serialized_input.validated_data[
                    "preferred_zip_codes"
                ],
                available_days=serialized_input.validated_data["available_days"],
                price_per_consultation=serialized_input.validated_data[
                    "price_per_consultation"
                ],
                minimum_age=serialized_input.validated_data["minimum_age"],
                maximum_age=serialized_input.validated_data["maximum_age"],
            )

            new_provider_criteria.save()

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
