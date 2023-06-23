import os
from unittest import mock

from lambda_utils.tests.unit.status_test_utils import event  # noqa: F401
from lambda_utils.tests.unit.status_test_utils import SERVICE_UNAVAILABLE

BASE_FIELDS = {"ENVIRONMENT": "", "SPLUNK_INDEX": "", "SOURCE": ""}


@mock.patch.dict(os.environ, BASE_FIELDS, clear=True)
def test_status_fails_if_bad_config(event):
    from api.consumer.status.index import handler

    assert handler(event=event) == SERVICE_UNAVAILABLE
