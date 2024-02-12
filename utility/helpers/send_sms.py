from utility.services.twilio import Twilio


def send_plain_SMS(to, body):
    try:
        # check_twilio_balance = Twilio().get_balance()
        # if int(check_twilio_balance["balance"]):
        new_Twilio_SMS = Twilio().send_sms(to, body)
        print("New Twilio SMS sent", new_Twilio_SMS)
        # return True
        if new_Twilio_SMS["status"]:
            return {"status": True}
        else:
            return {"status": False, "message": new_Twilio_SMS["message"]}
    except Exception as e:
        print("sendPlainSMS Exception", e)
        # return False
        return {"status": False, "message": f"{e}"}
