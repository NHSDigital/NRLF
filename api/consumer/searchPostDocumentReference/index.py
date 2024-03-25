from nrlf.core.decorators import request_handler
from nrlf.core.model import ConsumerRequestParams

from .search_post_document_reference import search_post_document_reference

handler = request_handler(body=ConsumerRequestParams)(search_post_document_reference)
