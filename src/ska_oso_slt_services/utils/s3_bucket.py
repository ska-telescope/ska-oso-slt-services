import base64
import hashlib
import logging
import os
from typing import Tuple

import boto3
from botocore.exceptions import ClientError

from ska_oso_slt_services.common.constant import (
    AWS_BUCKET_URL,
    AWS_REGION_NAME,
    AWS_SERVER_PUBLIC_KEY,
    AWS_SERVER_SECRET_KEY,
    AWS_SERVICE_NAME,
    AWS_SLT_BUCKET_NAME,
)
from ska_oso_slt_services.domain.shift_models import Media

LOGGER = logging.getLogger(__name__)


def get_aws_client():
    """
    Creates and returns an AWS client for a specific service
    using predefined credentials.

    This function initializes a boto3 client for an AWS
    service using the credentials
    and region specified in the global constants. It's designed to provide a
    centralized way of creating AWS clients with consistent
    configuration across the application.

    Returns:
        boto3.client: A boto3 client object for the specified AWS service.

    Global Constants Used:
        AWS_SERVER_PUBLIC_KEY (str): The AWS access key ID.
        AWS_SERVER_SECRET_KEY (str): The AWS secret access key.
        AWS_REGION_NAME (str): The AWS region to connect to.
        AWS_SERVICE_NAME (str): The name of the AWS service
        for which to create a client.

    Note:
        - This function assumes that the necessary AWS credential constants
          (AWS_SERVER_PUBLIC_KEY, AWS_SERVER_SECRET_KEY) are properly set and secured.
        - The AWS region (AWS_REGION_NAME) and service name (AWS_SERVICE_NAME) should be
          configured appropriately for the intended use.
        - For security best practices, consider using AWS IAM
          roles or environment variables
          for credential management instead of hardcoded constants,
          especially in production environments.

    Example:
        s3_client = get_aws_client()
        # Now s3_client can be used to interact with AWS S3 service
    """

    return boto3.client(
        AWS_SERVICE_NAME,
        aws_access_key_id=AWS_SERVER_PUBLIC_KEY,
        aws_secret_access_key=AWS_SERVER_SECRET_KEY,
        region_name=AWS_REGION_NAME,
    )


def calculate_file_hash(file: Media) -> str:
    """Calculate SHA-256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    file.file.seek(0)
    for chunk in iter(lambda: file.file.read(4096), b""):
        hash_sha256.update(chunk)
    file.file.seek(0)
    return hash_sha256.hexdigest()


def upload_file_object_to_s3(file: Media) -> Tuple[str, str, str]:
    """
    Upload a file object to an S3 bucket if it doesn't already exist.

    This function calculates a hash of the file, checks
    if a file with the same hash
    already exists in the S3 bucket,
    and uploads the file if it doesn't exist.

    Args:
        file (Media): A Media object containing the file to be uploaded.
            The Media object should have the following attributes:
            - filename: The name of the file
            - file: A file-like object containing the file data
            - content_type: The MIME type of the file

    Returns:
        Tuple[str, str, str]: A tuple containing:
            - file_url (str): The URL of the file in the S3 bucket
            - filename (str): The name of the file in the
              S3 bucket (hash + extension)
            - file_extension (str): The extension of the uploaded file

    Raises:
        FileExists: If a file with the same hash
        already exists in the S3 bucket
        ClientError: If there's an error
        interacting with the S3 bucket
        KeyError: If there's an unexpected
        response format from the S3 bucket

    Note:
        This function uses the AWS_SLT_BUCKET_NAME and AWS_BUCKET_URL environment
        variables for the S3 bucket name and URL, respectively.
    """
    try:
        file_extension = os.path.splitext(file.filename)[1]
        file_hash = calculate_file_hash(file)
        filename = f"{file_hash}{file_extension}"
        s3_client = get_aws_client()

        # Check if the file already exists in S3
        s3_client.upload_fileobj(
            file.file,
            AWS_SLT_BUCKET_NAME,
            filename,
            ExtraArgs={"ContentType": file.content_type},
        )
        LOGGER.info("File uploaded to S3: %s", filename)

        # Construct the URL of the file
        file_url = f"https://{AWS_SLT_BUCKET_NAME}.{AWS_BUCKET_URL}/{filename}"
        return file_url, filename, file_extension
    except ClientError as e:
        LOGGER.error("Error interacting with S3 bucket: %s", str(e))
        raise
    except KeyError as e:
        LOGGER.error("Unexpected response format from S3 bucket: %s", str(e))
        raise


def get_file_object_from_s3(file_key) -> Tuple[str, str, str]:
    """
    Retrieves an object from an S3 bucket and returns its content as an iterator.

    This function fetches a file from the specified S3 bucket using
    the provided file key.It returns an iterator for the file's content,
    allowing for efficient streaming of
    large files without loading the entire file into memory at once.

    Args:
        file_key (str): The key (path) of the file in the S3 bucket.

    Returns:
        tuple: A tuple containing three elements:
            - file_key (str): The original file key passed to the function.
            - content_iterator (iterator): An iterator
                that yields chunks of the file's content.
            - content_type (str): The content type of the file as returned from S3.

    Raises:
        ClientError: If there's an error retrieving
                     the object from S3, such as the file
                     not existing or insufficient permissions.
        KeyError: If the response from S3 doesn't
                contain the expected keys, indicating
                an unexpected response format.

    Note:
        - This function assumes that the AWS credentials
          and bucket name (AWS_SLT_BUCKET_NAME)
          are properly configured either through environment
          variables or AWS configuration files.
        - The content_iterator allows for memory-efficient
          processing of large files.
    """
    try:

        s3_client = get_aws_client()
        response = s3_client.get_object(Bucket=AWS_SLT_BUCKET_NAME, Key=file_key)
        content_type = response["ContentType"]

        content = response["Body"].read()

        # Convert to base64
        base64_content = base64.b64encode(content).decode("utf-8")

        return file_key, base64_content, content_type

    except ClientError as e:
        LOGGER.error("Error retrieving object from S3 bucket:%s", {str(e)})
        raise
    except KeyError as e:
        LOGGER.error("Unexpected response format from S3 bucket: %s", {str(e)})
        raise
