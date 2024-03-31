import uuid

from django.db.models import Q

from authentication.models import PractitionerPracticeCriteria
from utility.services.zipcodeapi import ZipCodeApi

from .models import UserBookingDetails


def recommend_providers(age, zipcode, day_care_is_needed):
    try:
        recommended_providers = []
        practitioner_criteria = PractitionerPracticeCriteria.objects.select_related(
            "user"
        ).filter(Q(minimum_age__lte=age) & Q(maximum_age__gte=age))

        practitioner_criteria = practitioner_criteria.filter(
            available_date_time__available_date_time__date=day_care_is_needed
        ).distinct()

        zipcodes = ZipCodeApi().get_close_zip_codes(zipcode)
        if not zipcodes["status"]:
            return {"status": False, "message": zipcodes["response"]}
        zipcodes = zipcodes["response"]

        practitioner_criteria = practitioner_criteria.filter(
            preferred_zip_codes__overlap=zipcodes
        )

        for criteria in practitioner_criteria:
            recommended_providers.append(criteria.user)

        if len(recommended_providers) == 0:
            return {"status": True, "message": []}

        return {"status": True, "message": recommended_providers}
    except Exception as err:
        print(f"recommend_providers error {err}")
        return {"status": False, "message": f"{err}"}


def generate_unique_id():
    code = uuid.uuid4()
    exists = UserBookingDetails.objects.filter(id=code).exists()
    while exists:
        code = uuid.uuid4()
        exists = UserBookingDetails.objects.filter(id=code).exists()
    return code
