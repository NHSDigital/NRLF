# import os
# from importlib import import_module
# from unittest import mock
#
# import pytest
# from lambda_utils.tests.unit.utils import (
#     make_aws_event,
#     throw_item_not_found_error,
#     throw_validation_error,
# )
#
# ENDPOINTS = [
#     "consumer.readDocumentReference",
#     "consumer.searchDocumentReference",
#     "consumer.searchViaPostDocumentReference",
#     "producer.createDocumentReference",
#     "producer.deleteDocumentReference",
#     "producer.readDocumentReference",
#     "producer.searchDocumentReference",
#     "producer.updateDocumentReference",
# ]
#
#
# @mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
# @pytest.mark.parametrize("event", [(make_aws_event()), (make_aws_event(version="2"))])
# @pytest.mark.parametrize("endpoint", ENDPOINTS)
# def test_handler_returns_200(endpoint: str, event: dict):
#     index = import_module(f"api.{endpoint}.index")
#     response = index.handler(event)
#     assert response["statusCode"] == 200
#
#
# @mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
# @mock.patch("lambda_utils.pipeline._get_steps")
# @pytest.mark.parametrize("step", [(throw_validation_error, throw_item_not_found_error)])
# @pytest.mark.parametrize("event", [(make_aws_event())])
# @pytest.mark.parametrize("endpoint", ENDPOINTS)
# def test_handler_returns_400(mocked__get_steps, endpoint: str, event: dict, step):
#     mocked__get_steps.return_value = [step]
#
#     index = import_module(f"api.{endpoint}.index")
#     response = index.handler(event)
#     assert response["statusCode"] == 400
#
#
# @mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
# @pytest.mark.parametrize("event", [(None)])
# @pytest.mark.parametrize("endpoint", ENDPOINTS)
# def test_handler_returns_500(endpoint: str, event: dict):
#     index = import_module(f"api.{endpoint}.index")
#     response = index.handler(event)
#     assert response["statusCode"] == 500
