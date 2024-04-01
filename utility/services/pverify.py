import datetime
import json

import requests
from django.conf import settings


class Pverify:
    def __init__(self):
        self.base_url = settings.PVERIFY_API_BASE_URL
        self.secret_key = settings.PVERIFY_API_CLIENT_SECRET
        self.client_id = settings.PVERIFY_API_CLIENT_ID

    def generate_token(self):
        try:
            url = self.base_url + "Token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            payload = {
                "Client_Id": self.client_id,
                "Client_Secret": self.secret_key,
                "grant_type": "client_credentials",
            }

            response = requests.post(url, headers=headers, data=payload)
            print(response.status_code, response.json())
            return response.json()["access_token"]
        except Exception as e:
            print("pverify generate toke Error", e)
            return None

    def verify_insurance(
        self,
        insurance_company_name: str,
        policy_number: str,
        dob: str,
        patient_relationship: str,
    ):
        try:
            today = datetime.datetime.now()
            url = self.base_url + "api/EligibilitySummary"

            headers = {
                "Authorization": f"Bearer {self.generate_token()}",
                "Client-API-Id": self.client_id,
                "Content-Type": "application/json",
            }
            start_date = today.strftime("%m/%d/%Y")

            if patient_relationship == "self":
                isSubscriberPatient = "True"
            else:
                isSubscriberPatient = "False"

            payload = {
                "payerCode": "00001",
                "payerName": insurance_company_name,
                "provider": {
                    "firstName": "",
                    "middleName": "",
                    "lastName": "RAPPE",
                    "npi": "1922249267",
                    "pin": "",
                },
                "subscriber": {
                    "firstName": "",
                    "dob": dob,
                    "lastName": "",
                    "memberID": policy_number,
                },
                "dependent": None,
                "isSubscriberPatient": isSubscriberPatient,
                "doS_StartDate": start_date,
                "doS_EndDate": start_date,
                "PracticeTypeCode": "23",
                "referenceId": "",
                "Location": "Georgia",
                "IncludeTextResponse": "false",
                "InternalId": "",
                "CustomerID": "",
            }

            response = requests.post(url, headers=headers, data=json.dumps(payload))

            if response.json()["APIResponseCode"] != "0":
                return {
                    "status": False,
                    "response": f"{response.json()['ErrorDescription']}",
                }

            return {"status": True, "response": "Gotten Insurance details successfully"}

        except Exception as e:
            print("pverify verify insurance error", e)
            return None
