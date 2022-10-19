from layer.lambda_utils.lambda_utils.header_config import AcceptHeader as BaseAcceptHeader

class AcceptHeader(BaseAcceptHeader):
    pass

def get_version_from_header(event) -> str:
    accept_header = AcceptHeader(event)
    return accept_header.version