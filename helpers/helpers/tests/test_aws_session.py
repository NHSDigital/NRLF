import pytest

from helpers.aws_session import new_aws_session


@pytest.mark.integration
def test_new_aws_session():
    session = new_aws_session()
    sts = session.client("sts")
    response = sts.get_caller_identity()
    assert "assumed-role/terraform" in response["Arn"]
