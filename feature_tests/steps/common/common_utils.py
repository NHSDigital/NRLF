import json
from copy import deepcopy

from lambda_pipeline.types import LambdaContext
from lambda_utils.logging_utils import generate_transaction_id
from lambda_utils.tests.unit.utils import make_aws_event


def update_supersede_targets_in_fhir_json(context, template_text: str) -> str:
    fhir_json = json.loads(template_text)
    supersede_targets = [
        row["value"] for row in context.table if row["property"] == "target"
    ]
    if supersede_targets:
        (_relatesTo,) = fhir_json.pop("relatesTo")
        fhir_json["relatesTo"] = [deepcopy(_relatesTo) for _ in supersede_targets]
        for relatesTo, target in zip(fhir_json["relatesTo"], supersede_targets):
            relatesTo["target"]["identifier"]["value"] = target
    return json.dumps(fhir_json)


def render_template(context) -> str:
    template_text = context.template
    for row in context.table:
        if row["property"] == "target":
            continue
        template_text = template_text.replace(f'${row["property"]}', row["value"])
    template_text = update_supersede_targets_in_fhir_json(context, template_text)
    return template_text


def uuid_headers(context) -> dict:
    uuid = generate_transaction_id()
    return {
        "x-correlation-id": f"{context.scenario.name} | {uuid}",
        "nhsd-correlation-id": uuid,
        "x-request-id": uuid,
    }


def authorisation_headers() -> dict:
    return {
        "Authorization": "letmein",
    }


def make_aws_authoriser_event(**kwargs) -> dict:
    event = make_aws_event(**kwargs)
    event.pop("isBase64Encoded")
    return event
