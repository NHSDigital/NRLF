from nrlf.core.decorators import request_handler
from nrlf.core.model import ConsumerRequestParams

from .search_document_reference import search_document_reference

handler = request_handler(params=ConsumerRequestParams)(search_document_reference)
