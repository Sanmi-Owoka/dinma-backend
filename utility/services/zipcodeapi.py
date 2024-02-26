import requests
from django.conf import settings


class ZipCodeApi:
    def __init__(self):
        self.base_url = settings.ZIP_CODE_API_BASE_URL
        self.test_api_key = settings.ZIP_CODE_API_TEST_API_KEY

    def get_close_zip_codes(self, zip_code) -> dict:
        try:
            url = f"{self.base_url}rest/{self.test_api_key}/radius.json/{zip_code}/15/mile"
            response = requests.get(url)

            if response.status_code != 200:
                error_msg = response.json()["error_msg"]
                return {
                    "status": False,
                    "response": f"{error_msg}",
                }
            all_zip_codes = response.json()["zip_codes"]
            zip_code_list = [zip_code["zip_code"] for zip_code in all_zip_codes]
            return {"status": True, "response": zip_code_list}

        except Exception as e:
            print("Get close zip codes exception", e)
            return {"status": False, "response": f"{e}"}
