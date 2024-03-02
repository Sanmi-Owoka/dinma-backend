import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentication.models import User
from authentication.serializers.provider_authentication_serializers import (
    SimpleDecryptedProviderDetails,
)
from booking.functools import generate_unique_id, recommend_providers
from booking.models import UserBookingDetails
from booking.serializers.booking_serializer import BookingSerializer
from utility.helpers.functools import (  # decrypt_simple_data,; decrypt_user_data,; encrypt,
    convert_serializer_errors_from_dict_to_list,
    convert_to_error_message,
    convert_to_success_message_serialized_data,
    paginate,
)


@extend_schema(tags=["Booking endpoints"])
class BookingViewSet(GenericViewSet):
    queryset = UserBookingDetails.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = BookingSerializer

    def get_queryset(self):
        if self.request.user.user_type == "patient":
            return UserBookingDetails.objects.filter(patient=self.request.user)
        else:
            return UserBookingDetails.objects.filter(practitioner=self.request.user)

    @action(
        methods=["POST"],
        detail=False,
        url_name="booking request",
        serializer_class=BookingSerializer,
    )
    def booking_request(self, request):
        try:
            today = datetime.datetime.now()

            user = request.user
            logged_in_user = User.objects.get(id=user.id)
            if logged_in_user.user_type == "health_provider":
                return Response(
                    convert_to_error_message(
                        "You are not authorized to book a health provider"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
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
            day_care_is_needed = serialized_input.validated_data["date_care_is_needed"]
            if day_care_is_needed > today.date():
                return Response(
                    convert_to_error_message("you can not pick a date less than today"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            age = serialized_input.validated_data["age_of_patient"]
            zipcode = serialized_input.validated_data["zipcode"]

            # create Booking details
            booking_details = UserBookingDetails(
                id=generate_unique_id(),
                patient=logged_in_user,
                date_care_is_needed=day_care_is_needed,
                symptom=serialized_input.validated_data["symptom"],
                age_of_patient=age,
                zipcode=zipcode,
                status="requested",
            )
            booking_details.save()

            get_providers = recommend_providers(age, zipcode)
            if not get_providers["status"]:
                return Response(
                    convert_to_error_message(get_providers["message"]),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            providers = get_providers["message"]

            return Response(
                convert_to_success_message_serialized_data(
                    paginate(
                        providers,
                        int(request.query_params.get("page", 1)),
                        SimpleDecryptedProviderDetails,
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
