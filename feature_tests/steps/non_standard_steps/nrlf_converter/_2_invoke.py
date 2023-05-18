import json

from nrlf.core.validators import json_loads

from feature_tests.common.constants import FhirType
from feature_tests.common.decorators import when
from feature_tests.common.models import Context, Response

NOT_A_REAL_FAILURE_CODE = 1000


GHERKIN_STRIPS_THIS_CHARACTER_SEQUENCE_FOR_SOME_REASON = "$'"
GHERKIN_LINTER_REPLACES_THIS_CHARACTER = ("\\", "\\\\")


def run_nrl_to_r4(document_pointer, nhs_number):
    from nrlf_converter import BadRelatesTo, CustodianError, ValidationError, nrl_to_r4

    document_reference, response = None, Response(body="")
    try:
        document_reference = nrl_to_r4(
            document_pointer=document_pointer,
            nhs_number=nhs_number,
        )
    except (ValidationError, CustodianError, BadRelatesTo) as error:
        response = Response(
            status_code=NOT_A_REAL_FAILURE_CODE,
            body=json.dumps(
                {
                    "error_type": type(error).__name__,
                    "error_message": str(error)
                    .strip()
                    .replace(GHERKIN_STRIPS_THIS_CHARACTER_SEQUENCE_FOR_SOME_REASON, "")
                    .replace(*GHERKIN_LINTER_REPLACES_THIS_CHARACTER),
                }
            ),
        )
    return document_reference, response


@when(
    '{actor_type} "{actor}" uses {package} to convert {nrl_template_name} '
    'with NHS Number "{nhs_number}" into a DocumentReference according to '
    "the {template_name} template",
)
def producers_converts_nrl_to_r4(
    context: Context,
    actor_type: str,
    actor: str,
    package: str,
    nrl_template_name: str,
    nhs_number: str,
    template_name: str,
):
    document_reference, context.test_config.response = run_nrl_to_r4(
        document_pointer=context.test_config.rendered_templates[nrl_template_name],
        nhs_number=nhs_number,
    )
    if document_reference:
        rendered_doc_ref = context.test_config.templates[template_name].render(
            table=context.table, fhir_type=FhirType.DocumentReference
        )
        assert document_reference == json_loads(rendered_doc_ref), json.dumps(
            {
                "actual": document_reference,
                "expected": json_loads(rendered_doc_ref),
            },
            indent=4,
        )
        context.test_config.rendered_templates[template_name] = rendered_doc_ref


@when(
    '{actor_type} "{actor}" uses {package} to convert {template_name} '
    'with NHS Number "{nhs_number}" into a DocumentReference',
)
def producers_converts_nrl_to_r4(
    context: Context,
    actor_type: str,
    actor: str,
    package: str,
    template_name: str,
    nhs_number: str,
):
    _, context.test_config.response = run_nrl_to_r4(
        document_pointer=context.test_config.rendered_templates[template_name],
        nhs_number=nhs_number,
    )
