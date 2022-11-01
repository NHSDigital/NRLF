import json

from lambda_pipeline.types import LambdaContext
from lambda_utils.tests.unit.utils import make_aws_event


def render_template_document(context) -> str:
    template_text = context.template_document
    for row in context.table:
        template_text = template_text.replace(f'${row["property"]}', row["value"])
    return template_text


def run_lambda_handler_locally(context, handler) -> dict:
    body = render_template_document(context)
    context.sent_document = json.dumps(json.loads(body))
    event = make_aws_event(body=body)
    lambda_context = LambdaContext()
    return handler(event, lambda_context)
