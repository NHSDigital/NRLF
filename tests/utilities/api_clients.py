import json

import requests
from pydantic import BaseModel

from nrlf.core.constants import PointerTypes
from nrlf.core.model import ConnectionMetadata


class ClientConfig(BaseModel):
    base_url: str
    auth_token: str = "TestToken"
    api_path: str = ""
    client_cert: tuple[str, str] | None = None
    connection_metadata: ConnectionMetadata | None = None
    custom_headers: dict[str, str] | None = {}


class SearchQuery:
    nhs_number: str = "UNSET"
    custodian: str | None = None
    pointer_type: PointerTypes | None = None

    def add_nhs_number(self, nhs_number: str):
        self.nhs_number = nhs_number
        return self

    def add_custodian(self, custodian: str):
        self.custodian = custodian
        return self

    def add_pointer_type(self, pointer_type: PointerTypes):
        self.pointer_type = pointer_type
        return self


class ConsumerTestClient:

    def __init__(self, config: ClientConfig):
        self.config = config
        self.api_url = f"{self.config.base_url}consumer{self.config.api_path}"

        self.request_headers = {
            "Authorization": f"Bearer {self.config.auth_token}",
            "X-Request-Id": "test-request-id",
        }

        if self.config.client_cert:
            # TODO-NOW - Fix deprecated dict usage
            connection_metadata = self.config.connection_metadata.dict(by_alias=True)
            client_rp_details = connection_metadata.pop("client_rp_details")
            self.request_headers.update(
                {
                    "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                    "NHSD-Client-RP-Details": json.dumps(client_rp_details),
                    "NHSD-Correlation-Id": "test-correlation-id",
                }
            )

        self.request_headers.update(self.config.custom_headers)

    def read(self, doc_ref_id: str):
        return requests.get(
            f"{self.api_url}/DocumentReference/{doc_ref_id}",
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    def count(self, params: dict[str, str]):
        return requests.get(
            f"{self.api_url}/DocumentReference/_count",
            params=params,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    def search(
        self,
        nhs_number: str | None = None,
        custodian: str | None = None,
        pointer_type: PointerTypes | None = None,
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

        return requests.get(
            f"{self.api_url}/DocumentReference",
            params=params,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    def search_post(
        self,
        nhs_number: str | None = None,
        custodian: str | None = None,
        pointer_type: PointerTypes | None = None,
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

        return requests.post(
            f"{self.api_url}/DocumentReference/_search",
            json=body,
            headers={
                "Content-Type": "application/json",
                **self.request_headers,
            },
            cert=self.config.client_cert,
        )

    def read_capability_statement(self):
        return requests.get(
            f"{self.api_url}/metadata",
            headers=self.request_headers,
            cert=self.config.client_cert,
        )


class ProducerTestClient:
    def __init__(self, config: ClientConfig):
        self.config = config
        self.api_url = f"{self.config.base_url}producer{self.config.api_path}"

        self.request_headers = {
            "Authorization": f"Bearer {self.config.auth_token}",
            "X-Request-Id": "test-request-id",
        }

        if self.config.client_cert:
            # TODO-NOW - Fix deprecated dict usage
            connection_metadata = self.config.connection_metadata.dict(by_alias=True)
            client_rp_details = connection_metadata.pop("client_rp_details")
            self.request_headers.update(
                {
                    "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                    "NHSD-Client-RP-Details": json.dumps(client_rp_details),
                    "NHSD-Correlation-Id": "test-correlation-id",
                }
            )

        self.request_headers.update(self.config.custom_headers)

    def create(self, doc_ref):
        return requests.post(
            f"{self.api_url}/DocumentReference",
            json=doc_ref,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    def create_text(self, doc_ref):
        return requests.post(
            f"{self.api_url}/DocumentReference",
            data=doc_ref,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    def upsert(self, doc_ref):
        return requests.put(
            f"{self.api_url}/DocumentReference",
            json=doc_ref,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    def update(self, doc_ref, doc_ref_id: str):
        return requests.put(
            f"{self.api_url}/DocumentReference/{doc_ref_id}",
            json=doc_ref,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    def delete(self, doc_ref_id: str):
        return requests.delete(
            f"{self.api_url}/DocumentReference/{doc_ref_id}",
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    def read(self, doc_ref_id: str):
        return requests.get(
            f"{self.api_url}/DocumentReference/{doc_ref_id}",
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    def search(
        self,
        nhs_number: str | None = None,
        pointer_type: PointerTypes | None = None,
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

        return requests.get(
            f"{self.api_url}/DocumentReference",
            params=params,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    def search_post(
        self,
        nhs_number: str | None = None,
        pointer_type: PointerTypes | None = None,
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

        return requests.post(
            f"{self.api_url}/DocumentReference/_search",
            json=body,
            headers={
                "Content-Type": "application/json",
                **self.request_headers,
            },
            cert=self.config.client_cert,
        )

    def read_capability_statement(self):
        return requests.get(
            f"{self.api_url}/metadata",
            headers=self.request_headers,
            cert=self.config.client_cert,
        )
