import base64

from helpers.aws_session import new_aws_session


def get_ecr_password() -> str:
    session = new_aws_session()
    ecr = session.client("ecr")
    response = ecr.get_authorization_token()
    auth_token_64 = response["authorizationData"][0]["authorizationToken"]
    auth_token = base64.b64decode(auth_token_64).decode()
    user, password = auth_token.split(":")
    return password
