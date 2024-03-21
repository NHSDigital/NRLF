import json
import sys

import boto3
from botocore.exceptions import ClientError

from nrlf.core.config import Config
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata


def get_pointer_types(
    connection_metadata: ConnectionMetadata, config: Config
) -> list[str]:
    ods_code = ".".join(connection_metadata.ods_code)

    app_id = connection_metadata.client_rp_details.developer_app_id
    ods_code = connection_metadata.ods_code
    ods_code_extension = connection_metadata.ods_code_extension

    if ods_code_extension:
        key = f"{app_id}/{ods_code}.{ods_code_extension}.json"
    else:
        key = f"{app_id}/{ods_code}.json"

    logger.log(LogReference.S3PERMISSIONS001, bucket=config.AUTH_STORE, key=key)
    s3_client = boto3.client("s3")

    try:
        response = s3_client.get_object(Bucket=config.AUTH_STORE, Key=key)
        pointer_types = json.loads(response["Body"].read())
        logger.log(LogReference.S3PERMISSIONS002, pointer_types=pointer_types)
        return pointer_types

    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "NoSuchKey":
            logger.log(LogReference.S3PERMISSIONS003, error=str(exc))
            return []

        logger.log(
            LogReference.S3PERMISSIONS004,
            exc_info=sys.exc_info(),
            stacklevel=5,
            error=str(exc),
        )
        raise exc

    except Exception as exc:
        logger.log(
            LogReference.S3PERMISSIONS004,
            exc_info=sys.exc_info(),
            stacklevel=5,
            error=str(exc),
        )
        raise exc
