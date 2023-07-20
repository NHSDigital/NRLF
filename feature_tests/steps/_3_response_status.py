from dataclasses import asdict

from feature_tests.common.constants import Outcomes
from feature_tests.common.decorators import then
from feature_tests.common.models import Context, TestConfig


@then("the operation is {outcome}")
def assert_operation_successful(context: Context, outcome: str):
    test_config: TestConfig = context.test_config
    result = test_config.response.success()
    expected_result = Outcomes._member_map_.get(outcome)
    if expected_result is None:
        raise ValueError(
            f"Outcome must be one of {Outcomes._member_names_}, got {outcome}"
        )
    assert result is expected_result.value, (
        test_config.request,
        asdict(test_config.response),
    )


@then("the status is {outcome:d}")
def assert_status_outcome(context: Context, outcome: int):
    test_config: TestConfig = context.test_config
    actual = test_config.response.status_code
    assert actual == outcome, asdict(test_config.response)
