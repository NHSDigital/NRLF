from abc import ABC, abstractmethod
from typing import Any, Generic, Iterator, List, Optional, Type, TypeVar

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

from nrlf.core.types import DynamoDBServiceResource
from nrlf.core_nonpipeline.dynamodb.model import DocumentPointer, DynamoDBModel
from nrlf.core_nonpipeline.logger import logger

RepositoryModel = TypeVar("RepositoryModel", bound=DynamoDBModel)


class Repository(ABC, Generic[RepositoryModel]):
    ITEM_TYPE: Type[RepositoryModel]

    def __init__(
        self,
        dynamodb: Optional[DynamoDBServiceResource] = None,
        environment_prefix: str = "",
    ):
        self.dynamodb = dynamodb or boto3.resource("dynamodb")
        self.table_name = environment_prefix + self.ITEM_TYPE.kebab()
        self.table = self.dynamodb.Table(self.table_name)
        self._serialiser = TypeSerializer()
        self._deserialiser = TypeDeserializer()

    @abstractmethod
    def create(self, item: RepositoryModel) -> RepositoryModel:
        """
        Creates a new item in the DynamoDB table
        Should always return an updated version of the item (if applicable)
        """
        raise NotImplementedError()

    def _to_dynamodb_type(self, value: Any):
        return self._serialiser.serialize(value)

    def _from_dynamodb_type(self, value: Any):
        if value is None:
            return None

        return self._deserialiser.deserialize(value)


class DocumentPointerRepository(Repository[DocumentPointer]):
    ITEM_TYPE = DocumentPointer

    def create(self, item: DocumentPointer) -> DocumentPointer:
        """
        Create a DocumentPointer resource
        """
        self.table.put_item(
            Item=item.dict(),
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
        )

        return item

    def get_by_id(self, id_: str) -> Optional[DocumentPointer]:
        """
        Get a DocumentPointer resource by ID
        """
        producer_id, document_id = id_.split("-", 1)
        ods_code_parts = producer_id.split(".")
        partition_key = "D#" + "#".join([*ods_code_parts, document_id])
        return self.get(partition_key)

    def get(self, partition_key: str) -> Optional[DocumentPointer]:
        """
        Return a single record by partition key
        """
        query = {
            "KeyConditionExpression": "pk = :pk",
            "ExpressionAttributeValues": {":pk": partition_key},
        }

        logger.info("Querying DynamoDB table", query=query)

        response = self.table.query(
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={":pk": partition_key},
        )

        if response["Count"] == 0:
            return None

        if response["Count"] > 1:
            raise Exception("Multiple items found")

        logger.debug("Received response", response=response)

        item = response["Items"][0]
        return self.ITEM_TYPE.parse_obj({"_from_dynamo": True, **item})

    def count_by_nhs_number(
        self,
        nhs_number: str,
        producer_id: Optional[str] = None,
        pointer_types: Optional[List[str]] = None,
    ) -> int:
        """
        Count all DocumentPointer records by NHS number
        """
        key_conditions = ["pk_1 = :pk_1"]
        filter_expressions = []
        expression_attribute_names = {}
        expression_attribute_values = {":pk_1": f"P#{nhs_number}"}

        if producer_id:
            key_conditions.append("begins_with(sk, :sk)")
            expression_attribute_values[":sk"] = f"D#{producer_id}"

        if pointer_types:
            pointer_type_filters = []
            expression_attribute_names[f"#pointer_type"] = "type"

            for i, pointer_type in enumerate(pointer_types):
                pointer_type_filters.append(f"#pointer_type = :type_{i}")
                expression_attribute_values[f":type_{i}"] = pointer_type

            filter_expressions.append(f"({' OR '.join(pointer_type_filters)})")

        query = {
            "KeyConditionExpression": " AND ".join(key_conditions),
            "FilterExpression": " AND ".join(filter_expressions),
            "ExpressionAttributeNames": expression_attribute_names or None,
            "ExpressionAttributeValues": expression_attribute_values,
            "Select": "COUNT",
        }

        logger.info(
            f"Counting records in DynamoDB table {self.table_name}", query=query
        )

        response = self.table.query(IndexName="idx_gsi_1", **query)

        logger.debug("Received count response", response=response)
        logger.info("Counted records", count=response["Count"])

        return response["Count"]

    def search(
        self,
        nhs_number: str,
        pointer_types: Optional[List[str]] = None,
    ) -> Iterator[DocumentPointer]:
        """"""
        key_conditions = ["pk_1 = :pk_1"]
        filter_expressions = []
        expression_attribute_names = {}
        expression_attribute_values = {":pk_1": f"P#{nhs_number}"}

        if pointer_types:
            pointer_type_filters = []
            expression_attribute_names[f"#pointer_type"] = "type"

            for i, pointer_type in enumerate(pointer_types):
                pointer_type_filters.append(f"#pointer_type = :type_{i}")
                expression_attribute_values[f":type_{i}"] = pointer_type

            filter_expressions.append(f"({' OR '.join(pointer_type_filters)})")

        query = {
            "IndexName": "idx_gsi_1",
            "KeyConditionExpression": " AND ".join(key_conditions),
            "FilterExpression": " AND ".join(filter_expressions),
            "ExpressionAttributeNames": expression_attribute_names,
            "ExpressionAttributeValues": expression_attribute_values,
        }

        yield from self._query(**query)

    def search_by_custodian(
        self,
        custodian: str,
        custodian_suffix: Optional[str] = None,
        pointer_types: Optional[List[str]] = None,
        nhs_number: Optional[str] = None,
    ) -> Iterator[DocumentPointer]:
        """ """
        key_conditions = ["pk_2 = :pk_2"]
        filter_expressions = []
        expression_attribute_names = {}
        expression_attribute_values = {
            ":pk_2": f"O#{custodian}",
        }

        if custodian_suffix:
            expression_attribute_values[":pk_2"] = f"O#{custodian}#{custodian_suffix}"

        if pointer_types:
            pointer_type_filters = []
            expression_attribute_names["#pointer_type"] = "type"

            for i, pointer_type in enumerate(pointer_types):
                pointer_type_filters.append(f"#pointer_type = :type_{i}")
                expression_attribute_values[f":type_{i}"] = pointer_type

            filter_expressions.append(f"({' OR '.join(pointer_type_filters)})")

        if nhs_number:
            filter_expressions.append("nhs_number = :nhs_number")
            expression_attribute_values[":nhs_number"] = nhs_number

        query = {
            "IndexName": "idx_gsi_2",
            "FilterExpression": " AND ".join(filter_expressions),
            "KeyConditionExpression": " AND ".join(key_conditions),
            "ExpressionAttributeNames": expression_attribute_names,
            "ExpressionAttributeValues": expression_attribute_values,
        }

        yield from self._query(**query)

    def find_by_nhs_number(self, nhs_number: str) -> Iterator[DocumentPointer]:
        """
        Find all DocumentPointer records by NHS number
        """
        yield from self._query(
            IndexName="idx_gsi_1",
            KeyConditionExpression="pk_1 = :pk_1",
            ExpressionAttributeValues={":pk_1": f"P#{nhs_number}"},
        )

    def find_by_custodian(self, custodian: str) -> Iterator[DocumentPointer]:
        """
        Find all DocumentPointer records by custodian
        """
        yield from self._query(
            IndexName="idx_gsi_2",
            KeyConditionExpression="pk_2 = :pk_2",
            ExpressionAttributeValues={":pk_2": f"C#{custodian}"},
        )

    def save(self, item: DocumentPointer) -> DocumentPointer:
        """
        Save a DocumentPointer resource
        """
        if not item._from_dynamo:
            return self.create(item)

        self.table.put_item(
            Item=item.dict(exclude_none=True),
            ConditionExpression="attribute_exists(pk) AND attribute_exists(sk)",
        )
        return item

    def supersede(
        self, item: DocumentPointer, ids_to_delete: List[str]
    ) -> DocumentPointer:
        """ """
        for id_ in ids_to_delete:
            self.delete_by_id(id_)

        return self.create(item)

    def delete(self, item: DocumentPointer) -> None:
        """
        Delete a DocumentPointer
        """
        logger.info(
            f"Deleting record from DynamoDB table {self.table_name}",
            partition_key=item.pk,
            sort_key=item.sk,
        )
        self.table.delete_item(
            Key={"pk": item.pk, "sk": item.sk},
            ConditionExpression="attribute_exists(pk) AND attribute_exists(sk)",
        )

    def delete_by_id(self, id_: str):
        """ """
        producer_id, document_id = id_.split("-", 1)
        ods_code_parts = producer_id.split(".")
        partition_key = "D#" + "#".join([*ods_code_parts, document_id])
        self.table.delete_item(Key={"pk": partition_key})

    def _query(self, IndexName: str, **kwargs) -> Iterator[DocumentPointer]:
        """
        Wrapper around DynamoDB query method to handle pagination
        Returns an iterator of DocumentPointer objects
        """
        # Remove empty fields from the search query
        query = {key: value for key, value in kwargs.items() if value}

        logger.info(f"Querying DynamoDB table {self.table_name}", query=query)

        paginator = self.dynamodb.meta.client.get_paginator("query")
        response_iterator = paginator.paginate(
            TableName=self.table_name, IndexName=IndexName, **query
        )

        for page in response_iterator:
            logger.debug(
                f"Received page of results",
                stats={
                    "count": page["Count"],
                    "scanned_count": page["ScannedCount"],
                    "last_evaluated_key": page.get("LastEvaluatedKey"),
                },
            )

            for item in page["Items"]:
                logger.debug(item)
                yield self.ITEM_TYPE.parse_obj({"_from_dynamo": True, **item})

    def update(self, item: DocumentPointer) -> DocumentPointer:
        """
        Update a DocumentPointer resource
        """
        self.table.put_item(
            Item=item.dict(),
            ConditionExpression="attribute_exists(pk) AND attribute_exists(sk)",
        )

        return item
