import base64
import json
import uuid

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone

from authentication.models import User


def encrypt(txt):
    try:
        # convert integer etc to string first
        txt = str(txt)
        # get the key from settings
        cipher_suite = Fernet(settings.ENCRYPT_KEY.encode())  # key should be byte
        # #input should be byte, so convert the text to byte
        encrypted_text = cipher_suite.encrypt(txt.encode("ascii"))
        # encode to urlsafe base64 format
        encrypted_text = base64.urlsafe_b64encode(encrypted_text).decode("ascii")
        return encrypted_text
    except Exception as e:
        # log the error if any
        print("encrypt error", e)
        return None


def decrypt(txt):
    try:
        # base64 decode
        txt = base64.urlsafe_b64decode(txt)
        cipher_suite = Fernet(settings.ENCRYPT_KEY.encode())
        decoded_text = cipher_suite.decrypt(txt).decode("ascii")
        return decoded_text
    except Exception as e:
        # log the error
        print("decrypt error", e)
        return None


def convert_serializer_errors_from_dict_to_list(input_dict: dict) -> list:
    serializer_error_arr = []
    for k, v in input_dict.items():
        serializer_error_arr.append(f"{k}: {v[0]}")
    return serializer_error_arr


def get_specific_user_with_email(email: str) -> dict:
    try:
        get_user: User = User.objects.get(email=email)
        return {"status": True, "response": get_user}
    except User.DoesNotExist:
        return {
            "status": False,
            "response": f"user with email: {email} does not exists",
        }


def check_fields_required(input_dict: dict) -> dict:
    for key, value in input_dict.items():
        if not value:
            return {"status": False, "response": f"{key} is required"}
    return {"status": True, "response": "all fields are present"}


def convert_to_error_message(message: any) -> dict:
    return {
        "status": "failure",
        "message": message,
        "data": "null",
    }


def convert_to_success_message_serialized_data(serialized_data: dict) -> dict:
    return {
        "status": "success",
        "message": "request successful",
        "data": serialized_data,
    }


def success_booking_response(serialized_data: dict, booking_id: str) -> dict:
    return {
        "status": "success",
        "message": "request successful",
        "booking_id": booking_id,
        "data": serialized_data,
    }


def convert_success_message(message: str) -> dict:
    return {"status": "success", "message": message, "data": "null"}


def decrypt_user_data(user_data: User, request) -> dict:
    if user_data.photo:
        photo = request.build_absolute_uri(user_data.photo.url)
    else:
        photo = None
    output_response = {
        "first_name": decrypt(user_data.first_name),
        "last_name": decrypt(user_data.last_name),
        "email": user_data.email,
        "phone_number": user_data.phone_number,
        "address": decrypt(user_data.address),
        "city": decrypt(user_data.city),
        "gender": user_data.gender,
        "state": user_data.state,
        "date_of_birth": user_data.date_of_birth.strftime("%d/%m/%Y"),
        "preferred_communication": user_data.preferred_communication,
        "languages_spoken": user_data.languages_spoken,
        "user_type": user_data.user_type,
        "date_joined": user_data.date_joined.strftime("%d/%m/%Y, %H:%M:%S"),
        "photo": photo,
    }
    return output_response


def decrypt_simple_data(user_data: User, request) -> dict:
    if user_data.photo:
        photo = request.build_absolute_uri(user_data.photo.url)
    else:
        photo = None
    output_response = {
        "first_name": decrypt(user_data.first_name),
        "last_name": decrypt(user_data.last_name),
        "email": user_data.email,
        "phone_number": user_data.phone_number,
        "gender": user_data.gender,
        "user_type": user_data.user_type,
        "photo": photo,
    }
    return output_response


def base64_to_data(base64_data):
    format, imgstr = base64_data.split(";base64,")
    ext = format.split("/")[-1]
    suffix = timezone.now().strftime("%y%m%d_%H%M%S")
    data = ContentFile(base64.b64decode(imgstr), name="upload{}.".format(suffix) + ext)
    return data


def generate_unique_id(model):
    generate_id = uuid.uuid4()
    exists = model.objects.filter(token=generate_id).exists()
    while exists:
        generate_id = uuid.uuid4()
        exists = model.objects.filter(token=generate_id).exists()
    return generate_id


def jsonify(data):
    return json.loads(JsonResponse(data, safe=False).content)


def paginate(query_set, page_num, serializer, context, page_size=10):
    pag_obj = Paginator(query_set, page_size)
    if page_num is None:
        page = 1
    else:
        page = page_num
    main_page = pag_obj.page(page)
    data = {
        "count": pag_obj.count,
        "pages": pag_obj.num_pages,
        "result": jsonify(
            serializer(main_page.object_list, many=True, context=context).data
        ),
        "page": page,
    }
    return data
