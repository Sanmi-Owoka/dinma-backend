import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

client = stripe.http_client.RequestsClient()
stripe.default_http_client = client


def stripe_handle_exception(f):
    def decorated_func(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught

            print("Status is: %s" % e.http_status)
            print("Code is: %s" % e.code)
            # param is '' in this case
            print("Param is: %s" % e.param)
            print("Message is: %s" % e.user_message)

            return {"status": "failure", "message": f"CardError-{e}"}
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            return {
                "status": "failure",
                "exception": "RateLimitError",
                "message": f"{e}",
            }
        except stripe.error.InvalidRequestError as e:
            print(f"InvalidRequestError {e}")
            # Invalid parameters were supplied to Stripe's API

            return {
                "status": "failure",
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            print(f"AuthenticationError {e}")
            return {
                "status": "failure",
                "exception": "AuthenticationError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            print(f"APIConnectionError {e}")
            return {
                "status": "failure",
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            print(f"StripeError {e}")
            return {"status": "failure", "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            return {
                "status": "failure",
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    return decorated_func


class StripeHelper:
    def __init__(self):
        self.live_api_key = settings.STRIPE_LIVE_SECRET_KEY
        self.test_api_key = settings.STRIPE_TEST_SECRET_KEY
        # self.helper = stripe.api_key(self.test_api_key)

    def create_payment_method(
        self, card_number: str, exp_month: int, exp_year: int, cvc: str
    ) -> dict:
        try:
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": f"{card_number}",
                    "exp_month": exp_month,
                    "exp_year": exp_year,
                    "cvc": f"{cvc}",
                },
            )
            return {"status": True, "data": payment_method}

        except stripe._error.CardError as e:
            return {"status": False, "exception": "CardError", "message": f"{e}"}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def create_customer(self, customer_id: str, **kwargs):
        try:
            customer = stripe.Customer.create(id=str(customer_id), **kwargs)

            return {"status": True, "data": customer}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def delete_customer(self, customer_id: str):
        try:
            customer = stripe.Customer.delete(id=str(customer_id))

            return {"status": True, "data": customer}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def retrieve_customer(self, customer_id: str):
        try:
            customer = stripe.Customer.retrieve(str(customer_id))

            return {"status": True, "data": customer}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def setup_intent(self, customer_id: str, pm_id: str):
        try:
            intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method=pm_id,
            )

            return {"status": True, "data": intent}

        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def retrieve_setup_intent(self, id: str):
        try:
            retrieve_intent = stripe.SetupIntent.retrieve(str(id))

            return {"status": True, "data": retrieve_intent}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def confirm_setup_intent(self, id: str):
        try:
            confirm_intent = stripe.SetupIntent.confirm(id)

            return {"status": True, "data": confirm_intent}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def fetch_payment_methods(self, customer_id: str, type: str):
        try:
            methods = stripe.Customer.list_payment_methods(
                customer=customer_id,
                type=type,
            )

            return {"status": True, "data": methods}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def get_customer_payment_method(self, customer_id, pm_id):
        try:
            p_method = stripe.Customer.retrieve_payment_method(
                str(customer_id), str(pm_id)
            )

            return {"status": True, "data": p_method}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def retrieve_payment_method(self, pm_id):
        try:
            pm_method = stripe.PaymentMethod.retrieve(str(pm_id))

            return {"status": True, "data": pm_method}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def create_payment_intent(
        self, customer_id: str, amount: int, currency: str = "usd"
    ):
        try:
            print(f"amount was {amount} and now {amount*100}")
            intent = stripe.PaymentIntent.create(
                customer=str(customer_id),
                amount=int(amount) * 100,
                currency=currency,
                # payment_method_types=["card"],
                automatic_payment_methods={"enabled": True},
            )
            print(f"intent object {intent}")
            return {"status": True, "data": intent}
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught

            print("Status is: %s" % e.http_status)
            print("Code is: %s" % e.code)
            # param is '' in this case
            print("Param is: %s" % e.param)
            print("Message is: %s" % e.user_message)

            return {"status": False, "exception": "CardError", "message": f"{e}"}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def off_session_payment_intent(
        self, customer_id: str, amount: int, currency: str = "usd"
    ):
        try:
            print(f"amount was {amount} and now {amount*100}")
            intent = stripe.PaymentIntent.create(
                customer=str(customer_id),
                setup_future_usage="off_session",
                amount=int(amount) * 100,
                currency=currency,
                automatic_payment_methods={"enabled": True},
            )
            print(f"intent object {intent}")
            return {"status": True, "data": intent}
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught

            print("Status is: %s" % e.http_status)
            print("Code is: %s" % e.code)
            # param is '' in this case
            print("Param is: %s" % e.param)
            print("Message is: %s" % e.user_message)

            return {"status": False, "exception": "CardError", "message": f"{e}"}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def retrieve_payment_intent(self, id):
        try:
            intent = stripe.PaymentIntent.retrieve(id)

            return {"status": True, "data": intent}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def charge_payment_method(
        self,
        customer_id: str,
        pm_id: str,
        amount: int,
        currency: str = "usd",
    ):
        try:
            charge = stripe.PaymentIntent.create(
                amount=int(amount) * 100,
                currency=currency,
                automatic_payment_methods={"enabled": True},
                customer=str(customer_id),
                payment_method=str(pm_id),
                off_session=True,
                confirm=True,
            )

            return {"status": True, "data": charge}
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught

            print("Status is: %s" % e.http_status)
            print("Code is: %s" % e.code)
            # param is '' in this case
            print("Param is: %s" % e.param)
            print("Message is: %s" % e.user_message)

            return {"status": False, "exception": "CardError", "message": f"{e}"}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }

    def create_card(self, customer_id):
        try:
            pass
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught

            print("Status is: %s" % e.http_status)
            print("Code is: %s" % e.code)
            # param is '' in this case
            print("Param is: %s" % e.param)
            print("Message is: %s" % e.user_message)

            return {"status": False, "exception": "CardError", "message": f"{e}"}
        except stripe.error.RateLimitError as e:
            return {"status": False, "exception": "RateLimitError", "message": f"{e}"}
        except stripe.error.InvalidRequestError as e:
            return {
                "status": False,
                "exception": "InvalidRequestError",
                "message": f"{e}",
            }
        except stripe.error.APIConnectionError as e:
            return {
                "status": False,
                "exception": "APIConnectionError",
                "message": f"{e}",
            }
        except stripe.error.StripeError as e:
            return {"status": False, "exception": "StripeError", "message": f"{e}"}
        except Exception as e:
            return {
                "status": False,
                "exception": "Out of Scope Exception",
                "message": f"{e}",
            }
