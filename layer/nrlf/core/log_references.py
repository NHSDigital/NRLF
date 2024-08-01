from dataclasses import dataclass
from enum import Enum


@dataclass
class _Reference:
    level: str
    message: str


class LogReference(Enum):
    # Request Handler Logs
    HANDLER000 = _Reference("INFO", "Starting execution of request handler")
    HANDLER001 = _Reference("DEBUG", "Loaded config from environment variables")
    HANDLER002 = _Reference("DEBUG", "Attempting to parse request headers")
    HANDLER003 = _Reference("INFO", "Parsed metadata from request headers")
    HANDLER004 = _Reference("INFO", "Authorisation lookup enabled")
    HANDLER004a = _Reference("INFO", "Authorisation lookup skipped for sync request")
    HANDLER004b = _Reference("INFO", "Parsing embedded permissions file from S3")
    HANDLER005 = _Reference("WARN", "Rejecting request due to missing pointer types")
    HANDLER006 = _Reference("DEBUG", "Attempting to parse request parameters")
    HANDLER007 = _Reference("INFO", "Parsed request parameters")
    HANDLER008 = _Reference("DEBUG", "Attempting to parse request body")
    HANDLER009 = _Reference("INFO", "Parsed request body")
    HANDLER010 = _Reference("DEBUG", "Attempting to parse request path parameters")
    HANDLER011 = _Reference("INFO", "Parsed request path parameters")
    HANDLER012 = _Reference("DEBUG", "Filtered request handler function arguments")
    HANDLER013 = _Reference("INFO", "Calling lambda-specific request handler")
    HANDLER014 = _Reference(
        "WARN", "Rejecting request due to missing X-Request-Id header"
    )
    HANDLER015 = _Reference(
        "WARN", "Rejecting request due to missing NHSD-Correlation-Id header"
    )
    HANDLER999 = _Reference("INFO", "Request handler returned successfully")

    # Error Logs
    ERROR000 = _Reference(
        "ERROR", "An unhandled exception occurred whilst processing the request"
    )
    ERROR001 = _Reference(
        "WARN", "An OperationOutcomeError occurred whilst processing the request"
    )
    ERROR002 = _Reference(
        "WARN", "An ParseError occurred whilst processing the request"
    )

    # S3 Permissions Lookup Logs
    S3PERMISSIONS001 = _Reference("INFO", "Retrieving pointer types from S3 bucket")
    S3PERMISSIONS002 = _Reference("INFO", "Retrieved list of pointer types from S3")
    S3PERMISSIONS003 = _Reference("WARN", "No permissions file found in S3")
    S3PERMISSIONS004 = _Reference(
        "EXCEPTION", "An error occurred whilst retrieving pointer types from S3"
    )
    S3PERMISSIONS005 = _Reference(
        "EXCEPTION",
        "An error occurred whilst pasrsing embedded permissions files from S3",
    )

    # Parse Logs
    PARSE000 = _Reference("DEBUG", "Attempting to parse data against model")
    PARSE001 = _Reference("INFO", "Parsed data against model")
    PARSE001a = _Reference("DEBUG", "Parsed data against model with result")
    PARSE002 = _Reference("WARN", "Failed to parse data against model")

    # Validator Logs
    VALIDATOR000 = _Reference("INFO", "Attempting to validate resource")
    VALIDATOR001 = _Reference("DEBUG", "Starting validation step")
    VALIDATOR001a = _Reference("INFO", "Skipping validation step")
    VALIDATOR002 = _Reference(
        "WARN", "An error was encountered whilst validating the resource"
    )
    VALIDATOR003 = _Reference("INFO", "Validation was stopped early due to errors")
    VALIDATOR999 = _Reference("INFO", "Validation completed on resource")

    # Repository logs
    REPOSITORY001 = _Reference("INFO", "Initialised DynamoDB repository")
    REPOSITORY002 = _Reference("INFO", "Creating item in DynamoDB")
    REPOSITORY003 = _Reference("INFO", "Successfully created item in DynamoDB")
    REPOSITORY004 = _Reference(
        "WARN", "Failed to create item in DynamoDB due to existing item"
    )
    REPOSITORY005 = _Reference("EXCEPTION", "Failed to create item in DynamoDB")
    REPOSITORY006 = _Reference("INFO", "Retrieving item from DynamoDB")
    REPOSITORY007 = _Reference("EXCEPTION", "Failed to retrieve item from DynamoDB")
    REPOSITORY008 = _Reference("ERROR", "Multiple items returned for partition key")
    REPOSITORY009 = _Reference("DEBUG", "Received query response from DynamoDB")
    REPOSITORY010 = _Reference(
        "EXCEPTION", "Existing item in datastore failed validation"
    )
    REPOSITORY011 = _Reference("INFO", "Successfully retrieved item from DynamoDB")
    REPOSITORY011a = _Reference(
        "DEBUG", "Successfully retrieved item from DynamoDB with result"
    )
    REPOSITORY012 = _Reference("INFO", "No item found in DynamoDB")
    REPOSITORY013 = _Reference("INFO", "Counting items in DynamoDB with criteria")
    REPOSITORY014 = _Reference("DEBUG", "Constructed base query")
    REPOSITORY015 = _Reference("DEBUG", "Adding key condition to query")
    REPOSITORY016 = _Reference("DEBUG", "Adding filter expression to query")
    REPOSITORY017 = _Reference("INFO", "Performing DynamoDB count query")
    REPOSITORY018 = _Reference("INFO", "Count query returned successfully")
    REPOSITORY018a = _Reference(
        "DEBUG", "Count query returned successfully with result"
    )
    REPOSITORY019 = _Reference(
        "EXCEPTION", "An error occurred whilst performing count query"
    )
    REPOSITORY020 = _Reference("INFO", "Searching items in DynamoDB with criteria")
    REPOSITORY021 = _Reference("INFO", "Performing DynamoDB query")
    REPOSITORY022 = _Reference("EXCEPTION", "An error occurred whilst performing query")
    REPOSITORY023 = _Reference("DEBUG", "Saving new resource to DynamoDB")
    REPOSITORY024 = _Reference("DEBUG", "Saving updated resource in DynamoDB")

    REPOSITORY025 = _Reference("DEBUG", "Deleting resource from DynamoDB")
    REPOSITORY026 = _Reference("EXCEPTION", "Failed to delete resource from DynamoDB")
    REPOSITORY026a = _Reference(
        "EXCEPTION", "Ignoring failure to delete resource from DynamoDB"
    )
    REPOSITORY027 = _Reference("INFO", "Successfully deleted item from DynamoDB")
    REPOSITORY028 = _Reference("INFO", "Received page of search results")
    REPOSITORY028a = _Reference("DEBUG", "Received page of search results with result")
    REPOSITORY029a = _Reference("DEBUG", "Updated item with result")

    # Model logs
    DOCPOINTER001 = _Reference("DEBUG", "Extracting custodian suffix from custodian")
    DOCPOINTER002 = _Reference("DEBUG", "Extracted custodian ID and custodian suffix")
    DOCPOINTER003 = _Reference("DEBUG", "Extracting producer ID from the document ID")
    DOCPOINTER004 = _Reference("DEBUG", "Extracted producer ID and document ID")
    DOCPOINTER005 = _Reference(
        "INFO", "Constructed DocumentPointer from DocumentReference resource"
    )
    DOCPOINTER006 = _Reference(
        "EXCEPTION", "Unsupported system defined for document reference"
    )

    # Consumer - CountDocumentReference
    CONCOUNT000 = _Reference(
        "INFO", "Starting to process consumer countDocumentReference"
    )
    CONCOUNT001 = _Reference(
        "INFO", "Invalid NHS number provided in the query parameters"
    )
    CONCOUNT999 = _Reference(
        "INFO", "Successfully completed consumer countDocumentReference"
    )

    # Consumer - ReadDocumentReference
    CONREAD000 = _Reference(
        "INFO", "Starting to process consumer readDocumentReference"
    )
    CONREAD001 = _Reference("INFO", "Returning 404 DocumentReference not found")
    CONREAD002 = _Reference(
        "WARN", "Organisation does not have permissions to access resource"
    )
    CONREAD003 = _Reference(
        "EXCEPTION", "The stored DocumentReference could not be parsed"
    )
    CONREAD999 = _Reference(
        "INFO", "Successfully completed consumer readDocumentReference"
    )

    # Consumer - SearchDocumentReference
    CONSEARCH000 = _Reference(
        "INFO", "Starting to process consumer searchDocumentReference"
    )
    CONSEARCH001 = _Reference(
        "INFO", "Invalid NHS number provided in the query parameters"
    )
    CONSEARCH002 = _Reference(
        "INFO", "Invalid document type provided in the query parameters"
    )
    CONSEARCH003 = _Reference("DEBUG", "Performing search by NHS number")
    CONSEARCH004 = _Reference(
        "DEBUG", "Parsed DocumentReference and added to search results"
    )
    CONSEARCH005 = _Reference(
        "EXCEPTION", "The DocumentReference resource could not be parsed"
    )
    CONSEARCH999 = _Reference(
        "INFO", "Successfully completed consumer searchDocumentReference"
    )

    # Consumer - SearchPostDocumentReference
    CONPOSTSEARCH000 = _Reference(
        "INFO", "Starting to process consumer searchPostDocumentReference"
    )
    CONPOSTSEARCH001 = _Reference(
        "INFO", "Invalid NHS number provided in the request body"
    )
    CONPOSTSEARCH002 = _Reference(
        "INFO", "Invalid document type provided in the request body"
    )
    CONPOSTSEARCH003 = _Reference("DEBUG", "Performing search by NHS number")
    CONPOSTSEARCH004 = _Reference(
        "DEBUG", "Parsed DocumentReference and added to search results"
    )
    CONPOSTSEARCH005 = _Reference(
        "EXCEPTION", "The DocumentReference resource could not be parsed"
    )
    CONPOSTSEARCH999 = _Reference(
        "INFO", "Successfully completed consumer searchDocumentReference"
    )

    # Producer - CreateDocumentReference
    PROCREATE000 = _Reference(
        "INFO", "Starting to process producer createDocumentReference"
    )
    PROCREATE001 = _Reference("DEBUG", "Validating DocumentReference resource")
    PROCREATE002 = _Reference("WARN", "DocumentReference resource failed validation")
    PROCREATE003 = _Reference(
        "WARN", "ODS code in headers does not match ODS code in resource ID"
    )
    PROCREATE004 = _Reference(
        "WARN", "ODS code in headers does not match ODS code in resource custodian"
    )
    PROCREATE005 = _Reference(
        "WARN", "Organisation is not allowed to create pointer type"
    )  #
    PROCREATE005a = _Reference(
        "WARN",
        "Organisation is not allowed to create pointer type with incorrect category",
    )  #
    PROCREATE006 = _Reference("DEBUG", "Performing relatesTo validation on resource")
    PROCREATE007a = _Reference(
        "WARN", "RelatesTo validation failed - no target identifier value"
    )
    PROCREATE007b = _Reference(
        "WARN", "RelatesTo validation failed - invalid producer for target identifier"
    )
    PROCREATE007c = _Reference(
        "WARN", "RelatesTo validation failed - no pointer exists with target identifier"
    )
    PROCREATE007d = _Reference(
        "WARN", "RelatesTo validation failed - relating pointer NHS number mismatch"
    )
    PROCREATE007e = _Reference(
        "WARN", "RelatesTo validation failed - relating pointer document type mismatch"
    )
    PROCREATE008 = _Reference("INFO", "Selecting document as target to be superseded")
    PROCREATE009 = _Reference("INFO", "Creating new document reference")
    PROCREATE010 = _Reference("INFO", "Superseding document reference")
    PROCREATE011 = _Reference(
        "INFO", "Preserved .date field when creating new document reference"
    )
    PROCREATE999 = _Reference(
        "INFO", "Successfully completed producer createDocumentReference"
    )

    # Producer - UpsertDocumentReference
    PROUPSERT000 = _Reference(
        "INFO", "Starting to process producer upsertDocumentReference"
    )
    PROUPSERT001 = _Reference(
        "DEBUG", "Validating DocumentReference resource for upsert"
    )
    PROUPSERT002 = _Reference(
        "WARN", "DocumentReference resource failed validation for upsert"
    )
    PROUPSERT003 = _Reference(
        "WARN", "ODS code in headers does not match ODS code in resource ID for upsert"
    )
    PROUPSERT004 = _Reference(
        "WARN",
        "ODS code in headers does not match ODWS code in resource custodian for upsert",
    )
    PROUPSERT005 = _Reference(
        "WARN", "Organisation is not allowed to upsert pointer type for upsert"
    )  #
    PROUPSERT005a = _Reference(
        "WARN",
        "Organisation is not allowed to upsert pointer type with incorrect category code",
    )  #
    PROUPSERT006 = _Reference(
        "DEBUG", "Performing relatesTo validation on resource for upsert"
    )
    PROUPSERT006a = _Reference(
        "DEBUG", "Skipping relatesTo validation on resource for sync upsert request"
    )
    PROUPSERT007a = _Reference(
        "WARN", "RelatesTo validation failed - no target identifier value for upsert"
    )
    PROUPSERT007b = _Reference(
        "WARN",
        "RelatesTo validation failed - invalid producer for target identifier for upsert",
    )
    PROUPSERT007c = _Reference(
        "WARN",
        "RelatesTo validation failed - no pointer exists with target identifier for upsert",
    )
    PROUPSERT007d = _Reference(
        "WARN",
        "RelatesTo validation failed - relating pointer NHS number mismatch for upsert",
    )
    PROUPSERT007e = _Reference(
        "WARN",
        "RelatesTo validation failed - relating pointer document type mismatch for upsert",
    )
    PROUPSERT008 = _Reference("INFO", "Selecting document as target to be superseded")
    PROUPSERT009 = _Reference("INFO", "Upserting new document reference")
    PROUPSERT010 = _Reference("INFO", "Superseding document reference for upsert")
    PROUPSERT011 = _Reference(
        "INFO", "Preserved .date field when creating new document reference for upsert"
    )
    PROUPSERT999 = _Reference(
        "INFO", "Successfully completed producer upsertDocumentReference"
    )

    # Producer - DeleteDocumentReference
    PRODELETE000 = _Reference(
        "INFO", "Starting to process producer deleteDocumentReference"
    )
    PRODELETE001 = _Reference(
        "WARN",
        "Organisation is not allowed to delete pointer as it is not the producer",
    )
    PRODELETE002 = _Reference("WARN", "Cannot delete pointer as it does not exist")
    PRODELETE999 = _Reference(
        "INFO", "Successfully completed producer deleteDocumentReference"
    )

    # Producer - ReadDocumentReference
    PROREAD000 = _Reference(
        "INFO", "Starting to process producer readDocumentReference"
    )
    PROREAD001 = _Reference(
        "WARN",
        "Unable to return DocumentReference as it belongs to another organisation",
    )
    PROREAD002 = _Reference("INFO", "Returning 404 DocumentReference not found")
    PROREAD003 = _Reference(
        "EXCEPTION", "The stored DocumentReference could not be parsed"
    )
    PROREAD999 = _Reference(
        "INFO", "Successfully completed producer readDocumentReference"
    )

    # Producer - SearchDocumentReference
    PROSEARCH000 = _Reference(
        "INFO", "Starting to process producer searchDocumentReference"
    )
    PROSEARCH001 = _Reference(
        "INFO", "Invalid NHS number provided in the query parameters"
    )
    PROSEARCH002 = _Reference(
        "INFO", "Invalid document type provided in the query parameters"
    )
    PROSEARCH003 = _Reference("DEBUG", "Performing search by custodian")
    PROSEARCH004 = _Reference(
        "DEBUG", "Parsed DocumentReference and added to search results"
    )
    PROSEARCH005 = _Reference(
        "EXCEPTION", "The DocumentReference esource could not be parsed"
    )
    PROSEARCH999 = _Reference(
        "INFO", "Successfully completed producer searchDocumentReference"
    )

    # Producer - SearchPostDocumentReference
    PROPOSTSEARCH000 = _Reference(
        "INFO", "Starting to process producer searchPostDocumentReference"
    )
    PROPOSTSEARCH001 = _Reference(
        "INFO", "Invalid NHS number provided in the request body"
    )
    PROPOSTSEARCH002 = _Reference(
        "INFO", "Invalid document type provided in the request body"
    )
    PROPOSTSEARCH003 = _Reference("DEBUG", "Performing search by custodian")
    PROPOSTSEARCH004 = _Reference(
        "DEBUG", "Parsed DocumentReference and added to search results"
    )
    PROPOSTSEARCH005 = _Reference(
        "EXCEPTION", "The DocumentReference resource could not be parsed"
    )
    PROPOSTSEARCH999 = _Reference(
        "INFO", "Successfully completed producer searchDocumentReference"
    )

    # Producer - UpdateDocumentReference
    PROUPDATE000 = _Reference(
        "INFO", "Starting to process producer updateDocumentReference"
    )
    PROUPDATE001 = _Reference(
        "WARN", "The ID in the path does not match the ID in the document body"
    )
    PROUPDATE002 = _Reference("DEBUG", "Validating DocumentReference resource")
    PROUPDATE003 = _Reference("WARN", "DocumentReference resource failed validation")
    PROUPDATE004 = _Reference(
        "WARN", "ODS code in headers does not match ODS code in resource ID"
    )
    PROUPDATE005 = _Reference("WARN", "No existing DocumentReference to update")
    PROUPDATE006 = _Reference(
        "WARN", "Cannot update DocumentReference as immutable fields have changed"
    )
    PROUPDATE007 = _Reference(
        "WARN",
        "Update provided for DocumentReference with invalid preserved field, ignoring",
    )
    PROUPDATE999 = _Reference(
        "INFO", "Successfully completed producer updateDocumentReference"
    )

    # Firehose Logs
    FIREHOSE000 = _Reference("INFO", "Starting to process CloudWatch log records")
    FIREHOSE001 = _Reference("INFO", "Parsed config from event")

    # Status Logs
    STATUS000 = _Reference("INFO", "Starting to process consumer status")
    STATUS001 = _Reference("DEBUG", "Checking environment variables")
    STATUS002 = _Reference("DEBUG", "Checking database connection")
    STATUS003 = _Reference("EXCEPTION", "An error occurred during the status check")
    STATUS999 = _Reference("INFO", "Successfully completed consumer status")
