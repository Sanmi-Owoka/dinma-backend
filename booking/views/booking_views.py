import datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.timezone import make_aware
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentication.models import (
    PractitionerAvailableDateTime,
    PractitionerPracticeCriteria,
    User,
)
from authentication.serializers.provider_authentication_serializers import (
    SimpleDecryptedProviderDetails,
)
from booking.functools import generate_unique_id, recommend_providers
from booking.models import UserBookingDetails
from booking.serializers.booking_serializer import (
    BookingSerializer,
    ConfirmBookingSerializer,
    CreateBookingSerializer,
    GetProviderBookingSerializer,
)
from utility.helpers.functools import (  # decrypt_simple_data,; decrypt_user_data,; encrypt,
    convert_serializer_errors_from_dict_to_list,
    convert_success_message,
    convert_to_error_message,
    convert_to_success_message_serialized_data,
    paginate,
    success_booking_response,
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
            if day_care_is_needed < today.date():
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

            get_providers = recommend_providers(age, zipcode, day_care_is_needed)
            if not get_providers["status"]:
                return Response(
                    convert_to_error_message(get_providers["message"]),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            booking_details.save()

            providers = get_providers["message"]

            return Response(
                success_booking_response(
                    booking_id=booking_details.id,
                    serialized_data=paginate(
                        providers,
                        int(request.query_params.get("page", 1)),
                        SimpleDecryptedProviderDetails,
                        {"request": request},
                        int(request.query_params.get("limit", 10)),
                    ),
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["PUT"],
        detail=False,
        url_name="create booking request",
        serializer_class=CreateBookingSerializer,
    )
    def finalize_booking(self, request):
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

            practitioner_email = serialized_input.validated_data.get(
                "practitioner_email"
            )
            date_time_of_care = serialized_input.validated_data.get("date_time_of_care")
            booking_id = serialized_input.validated_data.get("booking_id")

            if date_time_of_care < make_aware(today):
                return Response(
                    convert_to_error_message("you can not pick a date less than today"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get provider details
            provider = User.objects.filter(email=practitioner_email)
            if not provider.exists():
                return Response(
                    convert_to_error_message(
                        f"No provider found with email {practitioner_email}"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            provider = provider.first()
            fullname = f"{provider.first_name} {provider.last_name}"
            if provider.user_type != "health_provider":
                return Response(
                    convert_to_error_message(
                        f"The provider with email {practitioner_email} is not a health provider"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            practitioner_criteria = PractitionerPracticeCriteria.objects.filter(
                user=provider
            )
            if not practitioner_criteria.exists():
                return Response(
                    convert_to_error_message(
                        "An error occurred, Please contact support"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            practitioner_criteria = practitioner_criteria.first()

            if date_time_of_care not in practitioner_criteria.available_days:
                return Response(
                    convert_to_error_message(
                        f"The date {date_time_of_care} is not available"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get booking details
            booking_details = UserBookingDetails.objects.filter(id=booking_id)
            if not booking_details.exists():
                return Response(
                    convert_to_error_message(f"No booking found with id {booking_id}"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            booking_details = booking_details.first()
            if booking_details.status != "requested":
                return Response(
                    convert_to_error_message(
                        f"The booking with id {booking_id} is not requested"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if booking_details.patient != logged_in_user:
                return Response(
                    convert_to_error_message(
                        f"The booking with id {booking_id} is not yours"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Update booking details with practitioner and date time of care
            booking_details.practitioner = provider
            booking_details.date_time_of_care = date_time_of_care
            booking_details.status = "pending"
            booking_details.save()

            # try:
            subject = "Inhouse Visit Booking Request"
            from_email = settings.DEFAULT_FROM_EMAIL
            body = render_to_string(
                "email/practitioner_booking_request.html",
                {
                    "fullname": fullname,
                    "date_time_of_care": date_time_of_care,
                    "age_of_patient": booking_details.age_of_patient,
                    "zipcode": booking_details.zipcode,
                },
            )
            message = EmailMessage(
                subject,
                body,
                to=[provider.email],
                from_email=from_email,
            )
            message.content_subtype = "html"
            message.send(fail_silently=True)

            response_data = self.get_serializer(booking_details).data
            return Response(
                convert_to_success_message_serialized_data(response_data),
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["GET"],
        detail=False,
        url_name="get_all_practitioner_bookings",
        serializer_class=GetProviderBookingSerializer,
    )
    def get_all_practitioner_bookings(self, request):
        try:
            user = request.user
            logged_in_user = User.objects.get(id=user.id)

            if logged_in_user.user_type != "health_provider":
                return Response(
                    convert_to_error_message(
                        "You are not authorized for this function"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            booking_details = UserBookingDetails.objects.filter(
                practitioner=logged_in_user
            )
            return Response(
                convert_to_success_message_serialized_data(
                    serialized_data=paginate(
                        booking_details,
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
        methods=["GET"],
        detail=False,
        url_name="get_all_patient_bookings",
        serializer_class=CreateBookingSerializer,
    )
    def get_all_patient_bookings(self, request):
        try:
            user = request.user
            logged_in_user = User.objects.get(id=user.id)
            if logged_in_user.user_type != "patient":
                return Response(
                    convert_to_error_message(
                        "user is not authorized for this function"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            booking_details = UserBookingDetails.objects.filter(patient=logged_in_user)
            return Response(
                convert_to_success_message_serialized_data(
                    serialized_data=paginate(
                        booking_details,
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
        url_name="accept_booking_request",
        serializer_class=ConfirmBookingSerializer,
    )
    def accept_booking_request(self, request):
        try:
            user = request.user
            logged_in_user = User.objects.get(id=user.id)
            if logged_in_user.user_type == "patient":
                return Response(
                    convert_to_error_message(
                        "You are not authorized for this function"
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

            booking_id = serialized_input.validated_data.get("booking_id")
            booking_details = UserBookingDetails.objects.filter(id=booking_id)
            if not booking_details.exists():
                return Response(
                    convert_to_error_message(f"No booking found with id {booking_id}"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            booking_details = booking_details.first()
            if booking_details.status != "pending":
                return Response(
                    convert_to_error_message(
                        f"The booking with id {booking_id} is not pending"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if booking_details.practitioner != logged_in_user:
                return Response(
                    convert_to_error_message(
                        f"The booking with id {booking_id} does not exists"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            provider_criteria = PractitionerPracticeCriteria.objects.filter(
                user=logged_in_user
            )
            if not provider_criteria.exists():
                return Response(
                    convert_to_error_message(
                        "An error occurred, Please contact support"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            provider_criteria = provider_criteria.first()

            patient = booking_details.patient
            fullname = f"{patient.first_name} {patient.last_name}"
            date_time_of_care = booking_details.date_time_of_care

            booking_details.status = "accepted"

            provider_criteria.available_days.remove(booking_details.date_time_of_care)
            provider_criteria.save()

            PractitionerAvailableDateTime.objects.filter(
                provider_criteria=provider_criteria,
                available_date_time=booking_details.date_time_of_care,
            ).delete()

            booking_details.save()

            # try:
            subject = "Booking Request Confirmed"
            from_email = settings.DEFAULT_FROM_EMAIL
            body = render_to_string(
                "email/confirmed_booking_request.html",
                {
                    "fullname": fullname,
                    "date_time_of_care": date_time_of_care,
                    "age_of_patient": booking_details.age_of_patient,
                    "zipcode": booking_details.zipcode,
                },
            )
            message = EmailMessage(
                subject,
                body,
                to=[patient.email],
                from_email=from_email,
                bcc=[logged_in_user.email],
            )
            message.content_subtype = "html"
            message.send(fail_silently=True)

            return Response(
                convert_success_message("Booking had been successfully confirmed")
            )

        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )
