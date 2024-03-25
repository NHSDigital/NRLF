from nrlf.core.decorators import request_handler
from nrlf.core.model import CountRequestParams

from .count_document_reference import count_document_reference

handler = request_handler(params=CountRequestParams)(count_document_reference)
