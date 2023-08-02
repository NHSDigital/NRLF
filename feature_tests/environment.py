from behave.model import Scenario

from feature_tests.common.config_setup import config_setup
from feature_tests.common.constants import TestMode
from feature_tests.common.models import Context, TestConfig


def before_all(context: Context):
    context.test_config = None
    context.request_collection = {}


def before_scenario(context: Context, scenario: Scenario):
    context.test_config = config_setup(context=context, scenario_name=scenario.name)
    if (
        "integration-only" in scenario.tags
        and context.test_config.mode is TestMode.LOCAL_TEST
    ):
        scenario.mark_skipped()


def after_scenario(context: Context, scenario: Scenario):
    test_config: TestConfig = context.test_config
    # for repository in test_config.repositories.values():
    #     repository.delete_all()

    try:
        (request,) = test_config.request.sent_requests
    except ValueError:
        pass
    else:
        context.request_collection[scenario.name] = request


def after_all(context: Context):
    # transform context.request_collection here into postman_collection
    pass
