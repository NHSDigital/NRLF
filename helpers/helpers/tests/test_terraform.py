import pytest

from helpers.terraform import get_terraform_json


@pytest.mark.integration
def test_get_terraform_json():
    tf_json = get_terraform_json()
    assert type(tf_json) is dict
    assert len(tf_json) > 0
