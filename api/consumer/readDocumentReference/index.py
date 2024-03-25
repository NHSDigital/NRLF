from nrlf.core.decorators import request_handler
from nrlf.core.model import ReadDocumentReferencePathParams

from .read_document_reference import read_document_reference

handler = request_handler(path=ReadDocumentReferencePathParams)(read_document_reference)
