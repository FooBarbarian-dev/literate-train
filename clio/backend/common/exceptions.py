import logging

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("clio.exceptions")


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        logger.error("Unhandled exception in %s: %s", context.get("view"), exc, exc_info=True)
        return response

    logger.error("API error %s: %s", response.status_code, exc)
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
