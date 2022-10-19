import moto
import json
from datetime import datetime as dt
from nrlf.core.model import DocumentPointer, fhir_to_core
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data
import pytest
from nrlf.core.repository import Repository


def test_create():
    # Arrange
    document_reference = json.dumps(read_test_data("nrlf"))
    api_version = 1
    core_model = fhir_to_core(document=document_reference, api_version=api_version)
    repository = Repository("document-pointer")
    print(core_model)

    # Act
    repository.create(item=core_model.dict())

    # Assert
    assert True == False


def test_read():
    pass


def test_update():
    pass


def test_delete():
    pass


def test_search():
    pass
