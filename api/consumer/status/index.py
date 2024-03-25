from nrlf.core.decorators import request_handler

from .status import status

handler = request_handler(skip_request_verification=True)(status)
