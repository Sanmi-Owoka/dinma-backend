from django.conf import settings
from twilio.rest import Client


class Twilio:
    def __init__(self):

        self.accountSid = settings.TWILIO_ACCOUNT_SID
        self.authToken = settings.TWILIO_AUTH_TOKEN
        self.number = settings.TWILIO_NUMBER

    def get_balance(self):
        try:
            client = Client(self.accountSid, self.authToken)
            print(client.api.v2010.balance)
            balance_data = client.api.v2010.balance.fetch()
            balance = float(balance_data.balance)
            currency = balance_data.currency
            return {
                "status": True,
                "balance": balance,
                "currency": currency,
            }

        except Exception as e:
            print("Get Twilio balance exception", e)
            return {"status": False, "message": f"{e}"}

    def send_sms(self, to, body):
        try:
            client = Client(self.accountSid, self.authToken)
            new_message = client.messages.create(body=body, to=to, from_=self.number)
            print(new_message.sid)
            return {"status": True}
        except Exception as e:
            print("sendSMS Twilio Exception", e)
            return {"status": False, "message": f"{e}"}
