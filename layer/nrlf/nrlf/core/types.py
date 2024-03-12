from typing import Union

from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_s3 import S3Client

from nrlf.consumer.fhir.r4 import model as consumer_model
from nrlf.producer.fhir.r4 import model as producer_model

__all__ = ["DynamoDBServiceResource", "S3Client", "LambdaClient", "DynamoDBClient"]


# Generic Model Types
OperationOutcomeIssue = Union[
    producer_model.OperationOutcomeIssue, consumer_model.OperationOutcomeIssue
]
CodeableConcept = Union[producer_model.CodeableConcept, consumer_model.CodeableConcept]
Bundle = Union[producer_model.Bundle, consumer_model.Bundle]
DocumentReference = Union[
    producer_model.DocumentReference, consumer_model.DocumentReference
]
RequestQueryType = Union[
    producer_model.RequestQueryType, consumer_model.RequestQueryType
]
