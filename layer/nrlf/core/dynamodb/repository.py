import sys
from abc import ABC
from typing import Generic, Iterator, List, Optional, Type, TypeVar

from botocore.exceptions import ClientError
from pydantic import ValidationError

from nrlf.core.boto import get_dynamodb_resource, get_dynamodb_table
from nrlf.core.codes import SpineErrorConcept
from nrlf.core.dynamodb.model import DocumentPointer, DynamoDBModel
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import LogReference, logger

RepositoryModel = TypeVar("RepositoryModel", bound=DynamoDBModel)


class Repository(ABC, Generic[RepositoryModel]):
    ITEM_TYPE: Type[RepositoryModel]

    def __init__(self, environment_prefix: str = ""):
        self.dynamodb = get_dynamodb_resource()
        self.table_name = environment_prefix + self.ITEM_TYPE.kebab()
        self.table = get_dynamodb_table(self.table_name)
        logger.log(
            LogReference.REPOSITORY001,
            table_name=self.table_name,
            item_type=self.ITEM_TYPE.__name__,
        )


class DocumentPointerRepository(Repository[DocumentPointer]):
    ITEM_TYPE = DocumentPointer

    def create(self, item: DocumentPointer) -> DocumentPointer:
        """
        Create a DocumentPointer resource
        """
        logger.log(
            LogReference.REPOSITORY002,
            indexes=item.indexes,
            type=item.type,
            source=item.source,
            version=item.version,
        )

        try:
            result = self.table.put_item(
                Item=item.dict(),
                ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
                ReturnConsumedCapacity="INDEXES",
            )
            logger.log(LogReference.REPOSITORY003, result=result)

        except ClientError as exc:
            if (
                exc.response.get("Error", {}).get("Code")
                == "ConditionalCheckFailedException"
            ):
                logger.log(LogReference.REPOSITORY004)
                raise OperationOutcomeError(
                    status_code="409",
                    severity="error",
                    code="conflict",
                    details=SpineErrorConcept.from_code("DUPLICATE_REJECTED"),
                ) from None

            logger.log(
                LogReference.REPOSITORY005,
                exc_info=sys.exc_info(),
                stacklevel=5,
                error=str(exc),
            )
            raise exc

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

        logger.log(LogReference.REPOSITORY006, partition_key=partition_key, query=query)

        try:
            result = self.table.query(
                KeyConditionExpression="pk = :pk",
                ExpressionAttributeValues={":pk": partition_key},
                ReturnConsumedCapacity="INDEXES",
            )
        except ClientError as exc:
            logger.log(
                LogReference.REPOSITORY007,
                exc_info=sys.exc_info(),
                stacklevel=5,
                error=str(exc),
            )
            raise exc

        logger.log(LogReference.REPOSITORY009, result=result)

        if result["Count"] == 0:
            logger.log(LogReference.REPOSITORY012)
            return None

        if result["Count"] > 1:
            logger.log(LogReference.REPOSITORY008)
            raise OperationOutcomeError(
                status_code="500",
                severity="error",
                code="exception",
                details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
            )

        item = result["Items"][0]
        try:
            parsed_item = self.ITEM_TYPE.parse_obj({"_from_dynamo": True, **item})
            logger.log(LogReference.REPOSITORY011)
            logger.log(LogReference.REPOSITORY011a, result=parsed_item.dict())
            return parsed_item

        except ValidationError as exc:
            logger.log(
                LogReference.REPOSITORY010,
                exc_info=sys.exc_info(),
                stacklevel=5,
                error=str(exc),
            )
            raise OperationOutcomeError(
                status_code="500",
                severity="error",
                code="exception",
                details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
            ) from exc

    def count_by_nhs_number(
        self,
        nhs_number: str,
        pointer_types: Optional[List[str]] = None,
    ) -> int:
        """
        Count all DocumentPointer records by NHS number
        """
        logger.log(
            LogReference.REPOSITORY013,
            nhs_number=nhs_number,
            pointer_types=pointer_types,
        )

        key_conditions = ["pk_1 = :pk_1"]
        filter_expressions = []
        expression_attribute_names = {}
        expression_attribute_values = {":pk_1": f"P#{nhs_number}"}

        logger.log(
            LogReference.REPOSITORY014,
            key_conditions=key_conditions,
            filter_expressions=filter_expressions,
            expression_attribute_names=expression_attribute_names,
            expression_attribute_values=expression_attribute_values,
        )

        if pointer_types:
            pointer_type_filters = []
            expression_attribute_names["#pointer_type"] = "type"

            for i, pointer_type in enumerate(pointer_types):
                pointer_type_filters.append(f"#pointer_type = :type_{i}")
                expression_attribute_values[f":type_{i}"] = pointer_type

            expression = f"({' OR '.join(pointer_type_filters)})"
            logger.log(
                LogReference.REPOSITORY016, expression=expression, values=pointer_types
            )
            filter_expressions.append(expression)

        query = {
            "IndexName": "idx_gsi_1",
            "KeyConditionExpression": " AND ".join(key_conditions),
            "FilterExpression": " AND ".join(filter_expressions),
            "ExpressionAttributeNames": expression_attribute_names or None,
            "ExpressionAttributeValues": expression_attribute_values,
            "Select": "COUNT",
            "ReturnConsumedCapacity": "INDEXES",
        }

        logger.log(LogReference.REPOSITORY017, query=query)

        try:
            result = self.table.query(**query)
        except ClientError as exc:
            logger.log(
                LogReference.REPOSITORY019,
                exc_info=sys.exc_info(),
                stacklevel=5,
                error=str(exc),
            )
            raise OperationOutcomeError(
                status_code="500",
                severity="error",
                code="exception",
                details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
            ) from exc

        logger.log(LogReference.REPOSITORY018, count=result["Count"])
        logger.log(LogReference.REPOSITORY018a, result=result)

        return result["Count"]

    def search(
        self,
        nhs_number: str,
        custodian: Optional[str] = None,
        pointer_types: Optional[List[str]] = None,
    ) -> Iterator[DocumentPointer]:
        """"""
        logger.log(
            LogReference.REPOSITORY020,
            nhs_number=nhs_number,
            custodian=custodian,
            pointer_types=pointer_types,
        )

        key_conditions = ["pk_1 = :pk_1"]
        filter_expressions = []
        expression_attribute_names = {}
        expression_attribute_values = {":pk_1": f"P#{nhs_number}"}

        logger.log(
            LogReference.REPOSITORY014,
            key_conditions=key_conditions,
            filter_expressions=filter_expressions,
            expression_attribute_names=expression_attribute_names,
            expression_attribute_values=expression_attribute_values,
        )

        if custodian:
            logger.log(
                LogReference.REPOSITORY016,
                expression="custodian = :custodian",
                values=["custodian"],
            )
            filter_expressions.append("custodian = :custodian")
            expression_attribute_values[":custodian"] = custodian

        if pointer_types:
            pointer_type_filters = []
            expression_attribute_names["#pointer_type"] = "type"

            for i, pointer_type in enumerate(pointer_types):
                pointer_type_filters.append(f"#pointer_type = :type_{i}")
                expression_attribute_values[f":type_{i}"] = pointer_type

            expression = f"({' OR '.join(pointer_type_filters)})"
            logger.log(
                LogReference.REPOSITORY016, expression=expression, values=pointer_types
            )
            filter_expressions.append(expression)

        query = {
            "IndexName": "idx_gsi_1",
            "KeyConditionExpression": " AND ".join(key_conditions),
            "FilterExpression": " AND ".join(filter_expressions),
            "ExpressionAttributeNames": expression_attribute_names,
            "ExpressionAttributeValues": expression_attribute_values,
            "ReturnConsumedCapacity": "INDEXES",
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

        logger.log(
            LogReference.REPOSITORY014,
            key_conditions=key_conditions,
            filter_expressions=filter_expressions,
            expression_attribute_names=expression_attribute_names,
            expression_attribute_values=expression_attribute_values,
        )

        if pointer_types is not None:
            pointer_type_filters = []
            expression_attribute_names["#pointer_type"] = "type"

            for i, pointer_type in enumerate(pointer_types):
                pointer_type_filters.append(f"#pointer_type = :type_{i}")
                expression_attribute_values[f":type_{i}"] = pointer_type

            expression = f"({' OR '.join(pointer_type_filters)})"
            logger.log(
                LogReference.REPOSITORY016, expression=expression, values=pointer_types
            )
            filter_expressions.append(expression)

        if nhs_number:
            logger.log(
                LogReference.REPOSITORY016,
                expression="nhs_number = :nhs_number",
                values=[nhs_number],
            )
            filter_expressions.append("nhs_number = :nhs_number")
            expression_attribute_values[":nhs_number"] = nhs_number

        query = {
            "IndexName": "idx_gsi_2",
            "FilterExpression": " AND ".join(filter_expressions),
            "KeyConditionExpression": " AND ".join(key_conditions),
            "ExpressionAttributeNames": expression_attribute_names,
            "ExpressionAttributeValues": expression_attribute_values,
            "ReturnConsumedCapacity": "INDEXES",
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
            ReturnConsumedCapacity="INDEXES",
        )

    def find_by_custodian(self, custodian: str) -> Iterator[DocumentPointer]:
        """
        Find all DocumentPointer records by custodian
        """
        yield from self._query(
            IndexName="idx_gsi_2",
            KeyConditionExpression="pk_2 = :pk_2",
            ExpressionAttributeValues={":pk_2": f"C#{custodian}"},
            ReturnConsumedCapacity="INDEXES",
        )

    def save(self, item: DocumentPointer) -> DocumentPointer:
        """
        Save a DocumentPointer resource
        """
        if not item._from_dynamo:
            logger.log(LogReference.REPOSITORY023)
            return self.create(item)

        logger.log(LogReference.REPOSITORY024)
        return self.update(item)

    def supersede(
        self,
        item: DocumentPointer,
        ids_to_delete: List[str],
        can_ignore_delete_fail: bool = False,
    ) -> DocumentPointer:
        """ """
        saved_item = self.create(item)

        for id_ in ids_to_delete:
            self.delete_by_id(id_, can_ignore_delete_fail)

        return saved_item

    def delete(self, item: DocumentPointer) -> None:
        """
        Delete a DocumentPointer
        """
        logger.log(LogReference.REPOSITORY025, partition_key=item.pk, sort_key=item.sk)

        try:
            result = self.table.delete_item(
                Key={"pk": item.pk, "sk": item.sk},
                ConditionExpression="attribute_exists(pk) AND attribute_exists(sk)",
                ReturnConsumedCapacity="INDEXES",
            )
            logger.log(LogReference.REPOSITORY027, result=result)

        except ClientError as exc:
            logger.log(
                LogReference.REPOSITORY026,
                exc_info=sys.exc_info(),
                stacklevel=5,
                error=str(exc),
            )
            raise OperationOutcomeError(
                status_code="500",
                severity="error",
                code="exception",
                details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
            ) from exc

    def delete_by_id(self, id_: str, can_ignore_delete_fail: bool = False):
        """ """
        producer_id, document_id = id_.split("-", 1)
        ods_code_parts = producer_id.split(".")
        partition_key = "D#" + "#".join([*ods_code_parts, document_id])
        try:
            self.table.delete_item(Key={"pk": partition_key, "sk": partition_key})
        except ClientError as exc:
            if can_ignore_delete_fail:
                logger.log(
                    LogReference.REPOSITORY026a,
                    exc_info=sys.exc_info(),
                    stacklevel=5,
                    error=str(exc),
                )

    def _query(self, **kwargs) -> Iterator[DocumentPointer]:
        """
        Wrapper around DynamoDB query method to handle pagination
        Returns an iterator of DocumentPointer objects
        """
        # Remove empty fields from the search query
        query = {key: value for key, value in kwargs.items() if value}

        logger.log(LogReference.REPOSITORY021, query=query, table=self.table_name)

        try:
            paginator = self.dynamodb.meta.client.get_paginator("query")
            response_iterator = paginator.paginate(TableName=self.table_name, **query)

            for page in response_iterator:
                logger.log(
                    LogReference.REPOSITORY028,
                    stats={
                        "count": page["Count"],
                        "scanned_count": page["ScannedCount"],
                        "last_evaluated_key": page.get("LastEvaluatedKey"),
                    },
                )
                logger.log(LogReference.REPOSITORY028a, result=page)

                for item in page["Items"]:
                    try:
                        yield self.ITEM_TYPE.parse_obj({"_from_dynamo": True, **item})

                    except ValidationError as exc:
                        logger.log(
                            LogReference.REPOSITORY010,
                            exc_info=sys.exc_info(),
                            stacklevel=5,
                            error=str(exc),
                        )
                        raise OperationOutcomeError(
                            status_code="500",
                            severity="error",
                            code="exception",
                            details=SpineErrorConcept.from_code(
                                "INTERNAL_SERVER_ERROR"
                            ),
                        ) from exc

        except ClientError as exc:
            logger.log(
                LogReference.REPOSITORY022,
                exc_info=sys.exc_info(),
                stacklevel=5,
                error=str(exc),
            )
            raise exc

    def update(self, item: DocumentPointer) -> DocumentPointer:
        """
        Update a DocumentPointer resource
        """
        try:
            result = self.table.put_item(
                Item=item.dict(),
                ConditionExpression="attribute_exists(pk) AND attribute_exists(sk)",
                ReturnConsumedCapacity="INDEXES",
            )
            logger.log(LogReference.REPOSITORY029a, result=result)
        except ClientError as exc:
            logger.log(
                LogReference.REPOSITORY023,
                exc_info=sys.exc_info(),
                stacklevel=5,
                error=str(exc),
            )
            raise OperationOutcomeError(
                status_code="500",
                severity="error",
                code="exception",
                details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
            ) from exc

        return item
