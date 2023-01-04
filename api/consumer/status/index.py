from lambda_utils.pipeline import render_response
from lambda_utils.status_endpoint import execute_steps


def handler(event, context=None) -> dict[str, str]:
    status_code, result = execute_steps(
        index_path=__file__, event=event, context=context
    )
    return render_response(status_code, result)
