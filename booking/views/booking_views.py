import datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.timezone import make_aware
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
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
from booking.models import (
    GeneralBookingDetails,
    UserBookingDetails,
    UserBookingRequestTimeFrame,
)
from booking.serializers.booking_serializer import (  # GetProviderBookingSerializer,
    BookingSerializer,
    ConfirmBookingSerializer,
    CreateBookingSerializer,
    ListUserBookingsSerializer,
    RejectBookingSerializer,
    RescheduleBookingRequestSerializer,
)
from utility.helpers.functools import (  # decrypt_simple_data,; decrypt_user_data,; encrypt,
    convert_serializer_errors_from_dict_to_list,
    convert_success_message,
    convert_to_error_message,
    convert_to_success_message_serialized_data,
    decrypt,
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

            get_providers = recommend_providers(age, zipcode, day_care_is_needed)
            if not get_providers["status"]:
                return Response(
                    convert_to_error_message(get_providers["message"]),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if get_providers["message"] == []:
                return Response(
                    {
                        "status": "Success",
                        "message": "request successful",
                        "data": {"count": 0, "pages": 0, "result": [], "page": 0},
                    },
                    status=status.HTTP_200_OK,
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
            fullname = f"{decrypt(provider.first_name)} {decrypt(provider.last_name)}"
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

            if booking_details.status == "pending":
                return Response(
                    convert_to_error_message(
                        f"The booking with id {booking_id} is already requested"
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

            patient_fullname = (
                f"{decrypt(booking_details.patient.first_name)} "
                f"{decrypt(booking_details.patient.last_name)}"
            )

            # try:
            subject = "Inhouse Visit Booking Request"
            from_email = settings.DEFAULT_FROM_EMAIL
            body = render_to_string(
                "email/request-care.html",
                {
                    "fullname": fullname,
                    "patient_name": patient_fullname,
                    "date_time_of_care": date_time_of_care,
                    "age_of_patient": booking_details.age_of_patient,
                    "zipcode": booking_details.zipcode,
                    "symptoms": booking_details.symptom,
                    "address": decrypt(booking_details.patient.address),
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

    # @action(
    #     methods=["GET"],
    #     detail=False,
    #     url_name="get_all_practitioner_bookings",
    #     serializer_class=GetProviderBookingSerializer,
    # )
    # def get_all_practitioner_bookings(self, request):
    #     try:
    #         user = request.user
    #         logged_in_user = User.objects.get(id=user.id)
    #
    #         if logged_in_user.user_type != "health_provider":
    #             return Response(
    #                 convert_to_error_message(
    #                     "You are not authorized for this function"
    #                 ),
    #                 status=status.HTTP_400_BAD_REQUEST,
    #             )
    #         booking_details = UserBookingDetails.objects.filter(
    #             practitioner=logged_in_user
    #         )
    #         return Response(
    #             convert_to_success_message_serialized_data(
    #                 serialized_data=paginate(
    #                     booking_details,
    #                     int(request.query_params.get("page", 1)),
    #                     self.get_serializer,
    #                     {"request": request},
    #                     int(request.query_params.get("limit", 10)),
    #                 )
    #             ),
    #             status=status.HTTP_200_OK,
    #         )
    #     except Exception as err:
    #         return Response(
    #             convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
    #         )
    #
    # @action(
    #     methods=["GET"],
    #     detail=False,
    #     url_name="get_all_patient_bookings",
    #     serializer_class=CreateBookingSerializer,
    # )
    # def get_all_patient_bookings(self, request):
    #     try:
    #         user = request.user
    #         logged_in_user = User.objects.get(id=user.id)
    #         if logged_in_user.user_type != "patient":
    #             return Response(
    #                 convert_to_error_message(
    #                     "user is not authorized for this function"
    #                 ),
    #                 status=status.HTTP_400_BAD_REQUEST,
    #             )
    #
    #         booking_details = UserBookingDetails.objects.filter(patient=logged_in_user)
    #         return Response(
    #             convert_to_success_message_serialized_data(
    #                 serialized_data=paginate(
    #                     booking_details,
    #                     int(request.query_params.get("page", 1)),
    #                     self.get_serializer,
    #                     {"request": request},
    #                     int(request.query_params.get("limit", 10)),
    #                 )
    #             ),
    #             status=status.HTTP_200_OK,
    #         )
    #     except Exception as err:
    #         return Response(
    #             convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
    #         )

    @action(
        methods=["POST"],
        detail=False,
        url_name="accept_booking_request",
        serializer_class=ConfirmBookingSerializer,
        permission_classes=[AllowAny],
    )
    def accept_booking_request(self, request):
        try:
            serialized_input = self.get_serializer(data=request.data)
            if not serialized_input.is_valid():
                return Response(
                    convert_to_error_message(serialized_input.errors),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_email = serialized_input.validated_data.get("email")
            user = User.objects.filter(email=user_email)
            if not user.exists():
                return Response(
                    convert_to_error_message(f"No user found with email {user_email}"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = user.first()

            booking_id = serialized_input.validated_data.get("booking_id")

            booking_details = UserBookingDetails.objects.filter(id=booking_id)
            if not booking_details.exists():
                return HttpResponse("<h1>No booking found with id</h1>")

            booking_details = booking_details.first()
            if booking_details.status != "pending":
                return Response(
                    convert_to_error_message(
                        f"The booking with id {booking_id} is not pending"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if booking_details.practitioner != user:
                return Response(
                    convert_to_error_message(
                        f"The booking with id {booking_id} does not exists"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            provider_criteria = PractitionerPracticeCriteria.objects.filter(user=user)
            if not provider_criteria.exists():
                return Response(
                    convert_to_error_message(
                        "An error occurred, Please contact support"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            provider_criteria = provider_criteria.first()

            patient = booking_details.patient
            fullname = f"{decrypt(patient.first_name)} {decrypt(patient.last_name)}"
            date_time_of_care = booking_details.date_time_of_care

            booking_details.status = "accepted"

            provider_criteria.save()

            booking_timeframe = (
                PractitionerAvailableDateTime.objects.filter(
                    provider_criteria=provider_criteria,
                    available_date_time__year=booking_details.date_time_of_care.year,
                    available_date_time__month=booking_details.date_time_of_care.month,
                    available_date_time__day=booking_details.date_time_of_care.day,
                    available_date_time__hour=booking_details.date_time_of_care.hour,
                )
                .values_list("available_date_time", flat=True)
                .distinct()
            )

            # Add days been removed to the booking booking_timeframe
            create_booking_timeframe = UserBookingRequestTimeFrame.objects.create(
                booking=booking_details,
                booking_timeframe=list(booking_timeframe),
            )
            create_booking_timeframe.save()

            booking_details.save()

            PractitionerAvailableDateTime.objects.filter(
                provider_criteria=provider_criteria,
                available_date_time__year=booking_details.date_time_of_care.year,
                available_date_time__month=booking_details.date_time_of_care.month,
                available_date_time__day=booking_details.date_time_of_care.day,
                available_date_time__hour=booking_details.date_time_of_care.hour,
            ).delete()

            provider_name = f"{decrypt(user.first_name)} {decrypt(user.last_name)}"

            # try:
            subject = "Booking Request Confirmed"
            from_email = settings.DEFAULT_FROM_EMAIL
            body = render_to_string(
                "email/consulation-accepted.html",
                {
                    "fullname": fullname,
                    "date": date_time_of_care,
                    "provider_name": provider_name,
                },
            )
            message = EmailMessage(
                subject,
                body,
                to=[patient.email],
                from_email=from_email,
                bcc=[user.email],
            )
            message.content_subtype = "html"
            message.send(fail_silently=True)

            return Response(
                convert_success_message("Booking Request successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["POST"],
        detail=False,
        url_name="reject_booking_request",
        serializer_class=RejectBookingSerializer,
        permission_classes=[AllowAny],
    )
    def reject_booking_request(self, request):
        try:
            user_email = request.GET.get("email")
            user = User.objects.get(email=user_email)
            booking_id = request.GET.get("booking_id")

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

            if booking_details.practitioner != user:
                return Response(
                    convert_to_error_message(
                        f"The booking with id {booking_id} does not exists"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            patient = booking_details.patient
            fullname = f"{patient.first_name} {patient.last_name}"
            date_time_of_care = booking_details.date_time_of_care
            reason = "Provider Unavailable"

            booking_details.status = "rejected"
            booking_details.reason = reason
            booking_details.save()

            # try:
            subject = "Booking Request Rejected"
            from_email = settings.DEFAULT_FROM_EMAIL
            body = render_to_string(
                "email/reject_booking_request.html",
                {
                    "fullname": fullname,
                    "date_time_of_care": date_time_of_care,
                    "age_of_patient": booking_details.age_of_patient,
                    "zipcode": booking_details.zipcode,
                    "reason": reason,
                },
            )
            message = EmailMessage(
                subject,
                body,
                to=[patient.email],
                from_email=from_email,
                bcc=[user.email],
            )
            message.content_subtype = "html"
            message.send(fail_silently=True)

            return HttpResponse("<h1>Booking request Rejected successfully</h1>")
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status", description="booking status", type=str, required=False
            ),
        ]
    )
    @action(methods=["GET"], detail=False, serializer_class=ListUserBookingsSerializer)
    def get_patient_bookings(self, request):
        try:
            user = request.user
            booking_status = request.GET.get("status")
            logged_in_user = User.objects.get(id=user.id)
            if logged_in_user.user_type != "patient":
                return Response(
                    convert_to_error_message(
                        "user is not authorized for this function"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if booking_status:
                booking_status = booking_status.lower()
                status_choices = [
                    "pending",
                    "requested",
                    "accepted",
                    "rejected",
                    "failed",
                    "succeeded",
                ]
                if booking_status not in status_choices:
                    return Response(
                        convert_to_error_message(
                            f"Invalid status {booking_status}, status choices are {status_choices}"
                        ),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user_bookings = UserBookingDetails.objects.filter(
                    patient=logged_in_user, status=booking_status
                )
            else:
                user_bookings = UserBookingDetails.objects.filter(
                    patient=logged_in_user
                )
            return Response(
                convert_to_success_message_serialized_data(
                    paginate(
                        user_bookings,
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status", description="booking status", type=str, required=False
            ),
        ]
    )
    @action(methods=["GET"], detail=False, serializer_class=ListUserBookingsSerializer)
    def get_provider_bookings(self, request):
        try:
            user = request.user
            booking_status = request.GET.get("status")
            logged_in_user = User.objects.get(id=user.id)

            if logged_in_user.user_type != "health_provider":
                return Response(
                    convert_to_error_message(
                        "You are not authorized for this function"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if booking_status:
                status_choices = [
                    "pending",
                    "requested",
                    "accepted",
                    "rejected",
                    "failed",
                    "succeeded",
                ]
                if booking_status not in status_choices:
                    return Response(
                        convert_to_error_message(
                            f"Invalid status {booking_status}, status choices are {status_choices}"
                        ),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user_bookings = UserBookingDetails.objects.filter(
                    practitioner=logged_in_user, status=booking_status
                )
            else:
                user_bookings = UserBookingDetails.objects.filter(
                    practitioner=logged_in_user
                )
            return Response(
                convert_to_success_message_serialized_data(
                    paginate(
                        user_bookings,
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
        url_name="Cancel Patient Booking",
        serializer_class=RejectBookingSerializer,
    )
    def cancel_patient_booking(self, request):
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

            booking_id = serialized_input.validated_data["booking_id"]
            booking_details = UserBookingDetails.objects.filter(id=booking_id)
            if not booking_details.exists():
                return Response(
                    convert_to_error_message(f"No booking found with id {booking_id}"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            booking_details = booking_details.first()
            provider = booking_details.practitioner
            booking_details.status = "failed"
            booking_details.reason = serialized_input.validated_data["reason"]

            provider_criteria = PractitionerPracticeCriteria.objects.filter(
                user=provider
            )
            if not provider_criteria.exists():
                return Response(
                    convert_to_error_message(
                        "An error with Provider occurred please reach out to support team"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            provider_criteria = provider_criteria.first()

            # Add Timeframe back to provider datetime
            get_bookings_timeframe = UserBookingRequestTimeFrame.objects.filter(
                booking=booking_details,
            )
            if get_bookings_timeframe.exists():
                get_bookings_timeframe = (
                    get_bookings_timeframe.first().booking_timeframe
                )
                for timeframe in get_bookings_timeframe:
                    PractitionerAvailableDateTime.objects.create(
                        provider_criteria=provider_criteria,
                        available_date_time=timeframe,
                    )

            booking_details.save()
            return Response(
                convert_success_message("Booking has been cancelled"),
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["POST"],
        detail=False,
        url_name="get_reschedule_available_time",
        serializer_class=RescheduleBookingRequestSerializer,
    )
    def get_reschedule_available_time(self, request):
        try:
            logged_in_user = User.objects.get(id=request.user.id)
            if logged_in_user.user_type != "patient":
                return Response(
                    convert_to_error_message(
                        "user is not authorized for this function"
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

            booking_id = serialized_input.validated_data["booking_id"]
            booking_details = UserBookingDetails.objects.filter(id=booking_id)
            if not booking_details.exists():
                return Response(
                    convert_to_error_message(f"No booking found with id {booking_id}"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            booking_details = booking_details.first()

            provider = booking_details.practitioner
            if not provider:
                return Response(
                    convert_to_error_message(f"No provider found with id {booking_id}"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            pratice_criteria = PractitionerPracticeCriteria.objects.get(user=provider)
            if not pratice_criteria:
                return Response(
                    convert_to_error_message(
                        f"No practice criteria found with provider with email "
                        f"{provider.email}"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            day_care_is_needed = serialized_input.validated_data["day_care_is_needed"]

            get_available_date_times = PractitionerAvailableDateTime.objects.filter(
                provider_criteria=pratice_criteria,
                available_date_time__date=day_care_is_needed,
            )

            if not get_available_date_times.exists():
                return Response(
                    convert_to_error_message(
                        "No available date time found with provider on date entered"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            date_time_available: list = get_available_date_times.values_list(
                "available_date_time", flat=True
            )

            response = {
                "provider_email": provider.email,
                "available_date_time": date_time_available,
            }
            return Response(
                convert_to_success_message_serialized_data(response),
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["POST"],
        detail=False,
        url_name="reschedule_patient_booking",
        serializer_class=RescheduleBookingRequestSerializer,
    )
    def reschedule_patient_booking(self, request):
        try:
            logged_in_user = User.objects.get(id=request.user.id)
            if logged_in_user.user_type != "patient":
                return Response(
                    convert_to_error_message(
                        "user is not authorized for this function"
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            patient_fullname = f"{decrypt(logged_in_user.first_name)} {decrypt(logged_in_user.last_name)}"

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

            booking_id = serialized_input.validated_data["booking_id"]
            booking_details = UserBookingDetails.objects.filter(
                patient=logged_in_user, id=booking_id
            )
            if not booking_details.exists():
                return Response(
                    convert_to_error_message(f"No booking found with id {booking_id}"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            booking_details = booking_details.first()

            provider = booking_details.practitioner
            if not provider:
                return Response(
                    convert_to_error_message(f"No provider found with id {booking_id}"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            fullname = f"{decrypt(provider.first_name)} {decrypt(provider.last_name)}"

            date_time_care_is_needed = serialized_input.validated_data[
                "date_time_care_is_needed"
            ]
            booking_details.date_time_of_care = date_time_care_is_needed
            booking_details.date_care_is_needed = date_time_care_is_needed.date()
            booking_details.status = "requested"

            # try:
            subject = "Reschedule booking request"
            from_email = settings.DEFAULT_FROM_EMAIL
            body = render_to_string(
                "email/care-request.html",
                {
                    "fullname": fullname,
                    "patient_name": patient_fullname,
                    "date_time_of_care": date_time_care_is_needed,
                    "age_of_patient": booking_details.age_of_patient,
                    "zipcode": booking_details.zipcode,
                    "symptoms": booking_details.symptom,
                    "address": decrypt(booking_details.patient.address),
                },
            )
            message = EmailMessage(
                subject,
                body,
                to=[provider.email],
                from_email=from_email,
                bcc=[logged_in_user.email],
            )
            message.content_subtype = "html"
            message.send(fail_silently=True)
            booking_details.save()

            output_response = ListUserBookingsSerializer(booking_details)
            return Response(
                convert_to_success_message_serialized_data(output_response.data),
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["GET"],
        detail=False,
        url_name="get general booking details",
        permission_classes=[AllowAny],
    )
    def get_general_booking_details(self, request):
        try:
            get_general_booking_details = GeneralBookingDetails.objects.first()
            return Response(
                {
                    "price_per_consultation": get_general_booking_details.price_per_consultation
                },
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="time_frame", description="time_frame", type=str, required=False
            ),
        ]
    )
    @action(methods=["GET"], detail=False, permission_classes=[AllowAny])
    def test_hour_implementation(self, request):
        try:
            time_frame = request.GET.get("time_frame")
            time_frame = datetime.datetime.strptime(time_frame, "%Y-%m-%d %H:%M:%S")
            user = User.objects.get(email="blackcodingboy4@gmail.com")
            provider_criteria = PractitionerPracticeCriteria.objects.get(user=user)

            booking_timeframe = (
                PractitionerAvailableDateTime.objects.filter(
                    provider_criteria=provider_criteria,
                    available_date_time__year=time_frame.year,
                    available_date_time__month=time_frame.month,
                    available_date_time__day=time_frame.day,
                    available_date_time__hour=time_frame.hour,
                )
                .values_list("available_date_time", flat=True)
                .distinct()
            )

            return Response(
                convert_to_success_message_serialized_data(list(booking_timeframe)),
                status=status.HTTP_200_OK,
            )

        except Exception as err:
            return Response(
                convert_to_error_message(f"{err}"), status=status.HTTP_400_BAD_REQUEST
            )
