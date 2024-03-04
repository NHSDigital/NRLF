from functools import wraps
from typing import Callable

from behave import given as _given
from behave import then as _then
from behave import when as _when
from behave.runner import Context

from feature_tests.common.constants import ALLOWED_TERMS, ActorType
from feature_tests.common.models import BaseRequest, TestConfig


def _assert_request_is_ready(request: BaseRequest):
    if type(request) is BaseRequest:
        raise Exception(
            "This Request not ready, you must call "
            "'given_permissions_for_types' first"
            "in order to initialise the Request."
        )


def _assert_consistent_action(provided_action: str, expected_action: str):
    if (
        provided_action not in expected_action
        and expected_action not in provided_action
    ):
        raise Exception(
            f"Action {provided_action} provided in this step "
            f"is not the same as the Action {expected_action} expected "
            "from the Scenario initialisation."
        )


def _assert_consistent_actor(provided_actor: str, expected_actor: str):
    if provided_actor != expected_actor:
        raise Exception(
            f"Actor {provided_actor} provided in this step "
            f"is not the same as the Actor {expected_actor} expected "
            "from the Scenario initialisation."
        )


def _assert_consistent_actor_type(
    provided_actor_type: ActorType, expected_actor_type: ActorType
):
    if provided_actor_type is not expected_actor_type:
        raise Exception(
            f"ActorType {provided_actor_type.name} provided in this step "
            f"is not the same as the ActorType {expected_actor_type.name} expected "
            "from the Scenario initialisation."
        )


def _assert_allowed_terms(**kwargs):
    for k in kwargs:
        if k not in ALLOWED_TERMS:
            raise ValueError(
                f"Term '{k}' is not allowed. Allowed terms are {ALLOWED_TERMS}"
            )


def _step_checks(context: Context, **kwargs):
    test_config: TestConfig = context.test_config
    _assert_request_is_ready(request=test_config.request)
    _assert_allowed_terms(**kwargs)

    actor_type = ActorType._member_map_.get(kwargs.get("actor_type"))
    if actor_type is not None:
        _assert_consistent_actor_type(
            provided_actor_type=actor_type,
            expected_actor_type=test_config.actor_context.actor_type,
        )

    actor = kwargs.get("actor")
    if actor is not None:
        _assert_consistent_actor(
            provided_actor=actor, expected_actor=test_config.actor_context.actor
        )

    action = kwargs.get("action")
    if action is not None:
        _assert_consistent_action(
            provided_action=action,
            expected_action=test_config.actor_context.action.name,
        )


def _behave_decorator_with_checks(
    description: str, behave_decorator: Callable, **kwargs_overrides
) -> Callable:
    _deco = behave_decorator(description)

    def deco(fn):
        @wraps(fn)
        def wrapper(context, **kwargs):
            _step_checks(context=context, **{**kwargs, **kwargs_overrides})
            return fn(context, **kwargs)

        return _deco(wrapper)

    return deco


def when(description: str, **kwargs_overrides):
    return _behave_decorator_with_checks(
        description=description, behave_decorator=_when, **kwargs_overrides
    )


def then(description: str):
    return _behave_decorator_with_checks(
        description=description, behave_decorator=_then
    )


def given(description: str):
    return _behave_decorator_with_checks(
        description=description, behave_decorator=_given
    )
