import json

from feature_tests.common.decorators import then
from feature_tests.common.models import Context


@then('the response is a "nrlf_converter.{error_type}" with error message')
def the_response_is_nrlf_converter_error(context: Context, error_type: str):
    response = context.test_config.response.dict
    assert error_type == response["error_type"], (error_type, response["error_type"])

    assert response["error_message"] == context.text, json.dumps(
        {
            "expected": context.text,
            "actual": response["error_message"],
        },
        indent=4,
    )
