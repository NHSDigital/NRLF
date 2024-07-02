import sys
import tomllib
from os import path

from botocore.exceptions import ClientError

from nrlf.core.boto import get_s3_client
from nrlf.core.config import Config
from nrlf.core.constants import CUSTODIAN_SEPARATOR, PERMISSIONS_FILENAME
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata


def get_pointer_types(
    connection_metadata: ConnectionMetadata, config: Config
) -> list[str]:
    if connection_metadata.test_pointer_types:
        return connection_metadata.test_pointer_types

    pointer_types = parse_permissions_file(connection_metadata)

    if not pointer_types and not connection_metadata.load_test_permissions:
        logger.log(LogReference.HANDLER004)
        pointer_types = get_pointer_types_from_s3(connection_metadata, config)

    return pointer_types


def get_pointer_types_from_s3(
    connection_metadata: ConnectionMetadata, config: Config
) -> list[str]:
    key = PERMISSIONS_FILENAME
    logger.log(LogReference.S3PERMISSIONS001, bucket=config.AUTH_STORE, key=key)
    s3_client = get_s3_client()

    try:
        response = s3_client.get_object(Bucket=config.AUTH_STORE, Key=key)
        pointer_types = parse_permissions_file(connection_metadata)
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


def parse_permissions_file(connection_metadata: ConnectionMetadata) -> list[str]:
    app_id = connection_metadata.nrl_app_id
    ods_code = connection_metadata.ods_code
    ods_code_extension = connection_metadata.ods_code_extension

    key = ods_code
    if ods_code_extension:
        key += CUSTODIAN_SEPARATOR + ods_code_extension

    file_path = f"/opt/python/nrlf_permissions/{PERMISSIONS_FILENAME}"

    if connection_metadata.load_test_permissions:
        file_path = path.abspath(f"layer/test_permissions/{PERMISSIONS_FILENAME}")

    pointer_types = []
    try:
        with open(file_path, "rb") as file:
            data = tomllib.load(file)
            pointer_types = data[app_id][ods_code]
    except Exception as exc:
        logger.log(
            LogReference.S3PERMISSIONS005,
            exc_info=sys.exc_info(),
            stacklevel=5,
            error=str(exc),
        )
    return pointer_types
