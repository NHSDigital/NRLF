import json

from lambda_pipeline.types import LambdaContext
from lambda_utils.tests.unit.utils import make_aws_event


def update_supersede_targets_in_fhir_json(context, fhir_json: dict):
    supersede_targets = [
        row["value"] for row in context.table if row["property"] == "$target"
    ]
    if supersede_targets:
        fhir_json["relatesTo"] *= len(supersede_targets)
        for relatesTo, target in zip(fhir_json["relatesTo"], supersede_targets):
            relatesTo["target"]["identifier"]["value"] = target


def render_template_document(context) -> str:
    template_text = context.template_document
    for row in context.table:
        if row["property"] == "$target":
            continue
        template_text = template_text.replace(f'${row["property"]}', row["value"])
    return template_text


def run_lambda_handler_locally(context, handler) -> dict:
    body = render_template_document(context)
    context.sent_document = json.dumps(json.loads(body))
    event = make_aws_event(body=body)
    lambda_context = LambdaContext()
    return handler(event, lambda_context)
