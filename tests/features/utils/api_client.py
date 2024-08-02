import json
from abc import ABC
from typing import Literal

import requests
from behave.runner import Context
from pydantic import BaseModel

from nrlf.core.model import ConnectionMetadata

PointerTypeCodes = Literal[
    "736253002",  # Mental Health Crisis Plan
    "887701000000100",  # Emergency Healthcare Plan
    "861421000000109",  # End of Life Coordination Summary
    "1382601000000107",  # ReSPECT form
    "1363501000000100",  # Royal College of Physicians NEWS2
    "325691000000100",  # Contingency plan
    "736373009",  # End of life care plan
    "16521000000101",  # Lloyd George record folder
    "736366004",  # Advanced Care Plan
    "735324008",  # Treatment Escalation Plan
]

default_request_headers = {
    "Authorization": "Bearer TestToken",
    "X-Request-Id": "test-request-id",
    "NHSD-Correlation-Id": "test-correlation-id",
}


class ClientConfig(BaseModel):
    base_url: str
    client_cert: tuple[str, str]
    connection_metadata: ConnectionMetadata


class SearchQuery:
    nhs_number: str = "UNSET"
    custodian: str | None = None
    pointer_type: PointerTypeCodes | None = None

    def add_nhs_number(self, nhs_number: str):
        self.nhs_number = nhs_number
        return self

    def add_custodian(self, custodian: str):
        self.custodian = custodian
        return self

    def add_pointer_type(self, pointer_type: PointerTypeCodes):
        self.pointer_type = pointer_type
        return self


class APIClient(ABC):
    def __init__(self, config: ClientConfig):
        self.config = config

    @classmethod
    def from_context(cls, context: Context, ods_code: str):
        ods_code_parts = ods_code.split(".", 1)
        ods_code_extension = None
        if len(ods_code_parts) == 2:
            ods_code_extension = ods_code_parts[1]

        return cls(
            config=ClientConfig(
                base_url=context.base_url,
                client_cert=context.client_cert,
                connection_metadata=ConnectionMetadata.parse_obj(
                    {
                        "nrl.ods-code": ods_code_parts[0],
                        "nrl.ods-code-extension": ods_code_extension,
                        "nrl.permissions": [],
                        "nrl.app-id": context.application.app_id,
                        "client_rp_details": {
                            "developer.app.name": context.application.app_name,
                            "developer.app.id": context.application.app_id,
                        },
                    }
                ),
            )
        )


class ConsumerClient(APIClient):
    def read(self, doc_ref_id: str):
        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.get(
            f"{self.config.base_url}consumer/DocumentReference/{doc_ref_id}",
            headers={
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )

    def count(self, params: dict[str, str]):
        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.get(
            f"{self.config.base_url}consumer/DocumentReference/_count",
            params=params,
            headers={
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )

    def search(
        self,
        nhs_number: str | None = None,
        custodian: str | None = None,
        pointer_type: PointerTypeCodes | None = None,
        extra_params: dict[str, str] | None = None,
    ):
        params = {**(extra_params or {})}

        if nhs_number:
            params["subject:identifier"] = (
                "https://fhir.nhs.uk/Id/nhs-number|" + nhs_number
            )

        if custodian:
            params["custodian:identifier"] = (
                "https://fhir.nhs.uk/Id/ods-organization-code|" + custodian
            )

        if pointer_type:
            if "|" in pointer_type:
                params["type"] = pointer_type
            else:
                params["type"] = f"http://snomed.info/sct|{pointer_type}"

        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.get(
            f"{self.config.base_url}consumer/DocumentReference",
            params=params,
            headers={
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )

    def search_post(
        self,
        nhs_number: str | None = None,
        custodian: str | None = None,
        pointer_type: PointerTypeCodes | None = None,
        extra_fields: dict[str, str] | None = None,
    ):
        body = {**(extra_fields or {})}

        if nhs_number:
            body["subject:identifier"] = (
                "https://fhir.nhs.uk/Id/nhs-number|" + nhs_number
            )

        if custodian:
            body["custodian:identifier"] = (
                "https://fhir.nhs.uk/Id/ods-organization-code|" + custodian
            )

        if pointer_type:
            if "|" in pointer_type:
                body["type"] = pointer_type
            else:
                body["type"] = f"http://snomed.info/sct|{pointer_type}"

        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.post(
            f"{self.config.base_url}consumer/DocumentReference/_search",
            json=body,
            headers={
                "Content-Type": "application/json",
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )


class ProducerClient(APIClient):
    def create(self, doc_ref):
        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.post(
            f"{self.config.base_url}producer/DocumentReference",
            json=doc_ref,
            headers={
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )

    def create_text(self, doc_ref):
        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.post(
            f"{self.config.base_url}producer/DocumentReference",
            data=doc_ref,
            headers={
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )

    def upsert(self, doc_ref):
        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.put(
            f"{self.config.base_url}producer/DocumentReference",
            json=doc_ref,
            headers={
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )

    def update(self, doc_ref, doc_ref_id: str):
        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.put(
            f"{self.config.base_url}producer/DocumentReference/{doc_ref_id}",
            json=doc_ref,
            headers={
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )

    def delete(self, doc_ref_id: str):
        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.delete(
            f"{self.config.base_url}producer/DocumentReference/{doc_ref_id}",
            headers={
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )

    def read(self, doc_ref_id: str):
        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.get(
            f"{self.config.base_url}producer/DocumentReference/{doc_ref_id}",
            headers={
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )

    def search(
        self,
        nhs_number: str | None = None,
        pointer_type: PointerTypeCodes | None = None,
        extra_params: dict[str, str] | None = None,
    ):
        params = {**(extra_params or {})}

        if nhs_number:
            params["subject:identifier"] = (
                "https://fhir.nhs.uk/Id/nhs-number|" + nhs_number
            )

        if pointer_type:
            if "|" in pointer_type:
                params["type"] = pointer_type
            else:
                params["type"] = f"http://snomed.info/sct|{pointer_type}"

        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.get(
            f"{self.config.base_url}producer/DocumentReference",
            params=params,
            headers={
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )

    def search_post(
        self,
        nhs_number: str | None = None,
        pointer_type: PointerTypeCodes | None = None,
        extra_fields: dict[str, str] | None = None,
    ):
        body = {**(extra_fields or {})}

        if nhs_number:
            body["subject:identifier"] = (
                "https://fhir.nhs.uk/Id/nhs-number|" + nhs_number
            )

        if pointer_type:
            if "|" in pointer_type:
                body["type"] = pointer_type
            else:
                body["type"] = f"http://snomed.info/sct|{pointer_type}"

        connection_metadata = self.config.connection_metadata.dict(by_alias=True)
        client_rp_details = connection_metadata.pop("client_rp_details")

        return requests.post(
            f"{self.config.base_url}consumer/DocumentReference/_search",
            json=body,
            headers={
                **default_request_headers,
                "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                "NHSD-Client-RP-Details": json.dumps(client_rp_details),
            },
            cert=self.config.client_cert,
        )
