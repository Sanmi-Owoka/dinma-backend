import datetime
import json

import requests
from django.conf import settings

from ..helpers.functools import parse_dollar_string_to_number, remove_percentage


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

            return {"status": True, "response": response.json()}

        except Exception as e:
            print("pverify verify insurance error", e)
            return {
                "status": False,
                "response": f"{e}",
            }

    def complete_insurance_verification(
        self, obj: dict, patient_relationship: str
    ) -> dict:
        try:
            amount_billed = 350
            data = obj["HBPC_Deductible_OOP_Summary"]
            # IndividualDeductibleInNet = data["IndividualDeductibleInNet"]
            # IndividualDeductibleOutNet = data["IndividualDeductibleOutNet"]
            # IndividualDeductibleRemainingInNet = data[
            #     "IndividualDeductibleRemainingInNet"
            # ]
            IndividualDeductibleRemainingOutNet = parse_dollar_string_to_number(
                data["IndividualDeductibleRemainingOutNet"]["Value"]
            )
            IndividualOOPRemainingOutNet = parse_dollar_string_to_number(
                data["IndividualOOPRemainingOutNet"]["Value"]
            )
            FamilyDeductibleOutNet = parse_dollar_string_to_number(
                data["FamilyDeductibleOutNet"]["Value"]
            )
            FamilyOOPRemainingOutNet = parse_dollar_string_to_number(
                data["FamilyOOPRemainingOutNet"]["Value"]
            )

            UrgentCareSummary = obj["UrgentCareSummary"]
            ServiceCoveredOutNet = UrgentCareSummary["ServiceCoveredOutNet"]
            CoPayOutNet = parse_dollar_string_to_number(
                UrgentCareSummary["CoPayOutNet"]["Value"]
            )
            CoInsOutNet = remove_percentage(UrgentCareSummary["CoInsOutNet"]["Value"])

            if ServiceCoveredOutNet == "yes":
                if patient_relationship == "self":
                    if IndividualDeductibleRemainingOutNet >= amount_billed:
                        self_pay = amount_billed
                        if IndividualOOPRemainingOutNet <= self_pay:
                            self_pay = IndividualOOPRemainingOutNet
                            insurance_coverage = amount_billed - self_pay
                            return {
                                "status": "success",
                                "amount": self_pay,
                                "insurance_coverage": insurance_coverage,
                            }
                        else:
                            insurance_coverage = 0
                            return {
                                "status": "success",
                                "amount": self_pay,
                                "insurance_coverage": insurance_coverage,
                            }
                    else:
                        self_pay = IndividualDeductibleRemainingOutNet + CoPayOutNet
                        if self_pay < amount_billed:
                            self_pay = (
                                self_pay
                                + (amount_billed - self_pay) * CoInsOutNet / 100
                            )
                            insurance_coverage = amount_billed - self_pay
                            if IndividualOOPRemainingOutNet <= self_pay:
                                self_pay = IndividualOOPRemainingOutNet
                                insurance_coverage = amount_billed - self_pay
                                return {
                                    "status": "success",
                                    "amount": self_pay,
                                    "insurance_coverage": insurance_coverage,
                                }
                            else:
                                return {
                                    "status": "success",
                                    "amount": self_pay,
                                    "insurance_coverage": insurance_coverage,
                                }
                        else:
                            self_pay = amount_billed
                            insurance_coverage = 0
                            return {
                                "status": "success",
                                "amount": self_pay,
                                "insurance_coverage": insurance_coverage,
                            }

                    # if IndividualOOPRemainingOutNet <= self_pay:
                    #     self_pay = IndividualOOPRemainingOutNet
                    #     insurance_coverage = amount_billed - self_pay
                    #     return {
                    #         "status": "success",
                    #         "amount": self_pay,
                    #         "insurance_coverage": insurance_coverage
                    #     }

                else:
                    if FamilyDeductibleOutNet >= amount_billed:
                        self_pay = amount_billed
                        insurance_coverage = 0
                        if FamilyOOPRemainingOutNet <= self_pay:
                            self_pay = FamilyOOPRemainingOutNet
                            insurance_coverage = amount_billed - self_pay
                            return {
                                "status": "success",
                                "amount": self_pay,
                                "insurance_coverage": insurance_coverage,
                            }
                        else:
                            return {
                                "status": "success",
                                "amount": self_pay,
                                "insurance_coverage": insurance_coverage,
                            }

                    else:
                        self_pay = FamilyDeductibleOutNet + CoPayOutNet
                        if self_pay < amount_billed:
                            self_pay = (
                                FamilyDeductibleOutNet
                                + (amount_billed - FamilyDeductibleOutNet)
                                * CoInsOutNet
                                / 100
                            )
                            insurance_coverage = amount_billed - self_pay
                            if FamilyOOPRemainingOutNet <= self_pay:
                                self_pay = FamilyOOPRemainingOutNet
                                insurance_coverage = amount_billed - self_pay
                                return {
                                    "status": "success",
                                    "amount": self_pay,
                                    "insurance_coverage": insurance_coverage,
                                }
                            else:
                                return {
                                    "status": "success",
                                    "amount": self_pay,
                                    "insurance_coverage": insurance_coverage,
                                }

                        else:
                            self_pay = amount_billed
                            insurance_coverage = 0
                            return {
                                "status": "success",
                                "amount": self_pay,
                                "insurance_coverage": insurance_coverage,
                            }

                    # if FamilyOOPRemainingOutNet <= self_pay:
                    #     self_pay = FamilyOOPRemainingOutNet
                    #     insurance_coverage = amount_billed - self_pay
                    #     return {
                    #         "status": "success",
                    #         "amount": self_pay,
                    #         "insurance_coverage": insurance_coverage
                    #     }

            else:
                self_pay = amount_billed
                insurance_coverage = 0
                return {
                    "status": "success",
                    "amount": self_pay,
                    "insurance_coverage": insurance_coverage,
                }
        except Exception as e:
            print("pverify verify insurance error", e)
            return {
                "status": "failure",
                "response": f"{e}",
            }
