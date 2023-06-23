from importlib.metadata import version

from behave import given as behave_given

from feature_tests.common.decorators import given
from feature_tests.common.models import Context
from nrlf.core.validators import json_loads


@behave_given('version "{version_number}" of "{package_name}" has been installed')
def given_package_installed(context: Context, version_number: str, package_name: str):
    pkg_version = version(package_name)
    assert pkg_version == version_number, (
        f"Version '{pkg_version}' of {package_name} has been installed, "
        f"but {version_number} was requested"
    )


@given(
    '{actor_type} "{actor}" has an NRL Document Pointer from {template_name} template'
)
def given_producer_has_nrl_document_pointer(
    context: Context, actor_type: str, actor: str, template_name: str
):
    nrl_document_pointer = context.test_config.templates[template_name].render(
        context.table
    )
    context.test_config.rendered_templates[template_name] = json_loads(
        nrl_document_pointer
    )
