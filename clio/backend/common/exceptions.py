from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        data = {
            "error": True,
            "message": "",
            "details": response.data,
        }
        if isinstance(response.data, dict):
            data["message"] = response.data.get("detail", str(response.data))
        elif isinstance(response.data, list):
            data["message"] = response.data[0] if response.data else "Unknown error"
        else:
            data["message"] = str(response.data)
        response.data = data

    return response
