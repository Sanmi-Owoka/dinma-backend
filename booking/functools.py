from authentication.models import PractitionerPracticeCriteria
from utility.services.zipcodeapi import ZipCodeApi


def recommend_providers(age, zipcode):
    try:
        recommended_providers = []
        practitioner_criteria = PractitionerPracticeCriteria.objects.select_related(
            "user"
        ).filter(minimum_age__gte=age, maximum_age__lte=age)
        zipcodes = ZipCodeApi().get_close_zip_codes(zipcode)
        if not zipcodes["status"]:
            return {"status": False, "message": zipcodes["response"]}
        zipcodes = zipcodes["response"]
        practitioner_criteria = practitioner_criteria.filter(
            preferred_zip_codes__overlaps=zipcodes
        )
        recommended_providers.append(practitioner_criteria.user)
        if len(recommended_providers) == 0:
            return {"status": False, "message": "No Provider recommendations"}

        return {"status": True, "message": recommended_providers}
    except Exception as err:
        print(f"recommend_providers error {err}")
        return {"status": False, "message": f"{err}"}
