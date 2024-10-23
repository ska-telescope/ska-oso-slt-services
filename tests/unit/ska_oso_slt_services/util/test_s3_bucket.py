import base64
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from fastapi import UploadFile

from ska_oso_slt_services.common.error_handling import FileExists

# Assuming the function is in a module named 's3_utils'
from ska_oso_slt_services.utils.s3_bucket import (
    AWS_SLT_BUCKET_NAME,
    get_file_object_from_s3,
    upload_file_object_to_s3,
)


@pytest.fixture
def mock_file():
    file = Mock(spec=UploadFile)
    file.filename = "test_file.txt"
    file.content_type = "text/plain"
    file.file = Mock()
    return file


@pytest.fixture
def mock_aws_client():
    with patch("ska_oso_slt_services.utils.s3_bucket.get_aws_client") as mock_client:
        yield mock_client.return_value


@patch("ska_oso_slt_services.utils.s3_bucket.get_aws_client")
@patch("ska_oso_slt_services.utils.s3_bucket.calculate_file_hash")
def test_upload_file_object_to_s3_client_error(
    mock_calculate_file_hash, mock_get_aws_client, mock_file
):
    # Arrange
    mock_s3_client = Mock()
    mock_get_aws_client.return_value = mock_s3_client
    mock_calculate_file_hash.return_value = "fake_hash"
    mock_file.filename = "test.jpg"

    # Simulate file not found in S3, then upload error
    mock_s3_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "head_object"
    )
    mock_s3_client.upload_fileobj.side_effect = ClientError(
        {"Error": {"Code": "TestException", "Message": "Test error message"}},
        "upload_fileobj",
    )

    # Act & Assert
    with pytest.raises(ClientError):
        upload_file_object_to_s3(mock_file)

    # Verify function calls
    mock_calculate_file_hash.assert_called_once_with(mock_file)
    mock_s3_client.head_object.assert_called_once_with(
        Bucket=AWS_SLT_BUCKET_NAME, Key="fake_hash.jpg"
    )
    mock_s3_client.upload_fileobj.assert_called_once()


@patch("ska_oso_slt_services.utils.s3_bucket.get_aws_client")
@patch("ska_oso_slt_services.utils.s3_bucket.calculate_file_hash")
def test_upload_file_object_to_s3_file_exists(
    mock_calculate_file_hash, mock_get_aws_client, mock_file
):
    # Arrange
    mock_s3_client = Mock()
    mock_get_aws_client.return_value = mock_s3_client
    mock_calculate_file_hash.return_value = "existing_hash"
    mock_file.filename = "test.jpg"

    # Simulate file found in S3
    mock_s3_client.head_object.return_value = {}  # Simulating that the file exists

    # Act & Assert
    with pytest.raises(FileExists) as exc_info:
        upload_file_object_to_s3(mock_file)

    # Assert
    assert (
        str(exc_info.value)
        == "302: File existing_hash.jpg already exists in S3. Skipping upload."
    )
    mock_calculate_file_hash.assert_called_once_with(mock_file)
    mock_s3_client.head_object.assert_called_once_with(
        Bucket=AWS_SLT_BUCKET_NAME, Key="existing_hash.jpg"
    )
    mock_s3_client.upload_fileobj.assert_not_called()


@patch("ska_oso_slt_services.utils.s3_bucket.get_aws_client")
@patch("ska_oso_slt_services.utils.s3_bucket.calculate_file_hash")
def test_upload_file_object_to_s3_key_error(
    mock_calculate_file_hash, mock_get_aws_client, mock_file
):
    # Arrange
    mock_calculate_file_hash.return_value = "fake_hash"
    mock_s3_client = Mock()
    mock_get_aws_client.return_value = mock_s3_client
    mock_s3_client.upload_fileobj.side_effect = KeyError("Test key error")

    # Ensure mock_file has necessary attributes
    mock_file.file.seek = Mock()
    mock_file.file.read = Mock(return_value=b"Test content")

    # Act & Assert
    with pytest.raises(FileExists):
        upload_file_object_to_s3(mock_file)


@patch("ska_oso_slt_services.utils.s3_bucket.get_aws_client")
@patch("ska_oso_slt_services.utils.s3_bucket.calculate_file_hash")
@patch("ska_oso_slt_services.utils.s3_bucket.AWS_SLT_BUCKET_NAME", "test-bucket")
@patch("ska_oso_slt_services.utils.s3_bucket.AWS_BUCKET_URL", "test-url")
def test_upload_file_object_to_s3_success(
    mock_calculate_file_hash, mock_get_aws_client, mock_file
):
    # Arrange

    mock_calculate_file_hash.return_value = "fake_hash"
    mock_s3_client = Mock()
    mock_get_aws_client.return_value = mock_s3_client

    # Mock the head_object method to raise a ClientError with a 404 status
    mock_s3_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
    )

    # Act
    file_url, filename, file_extension = upload_file_object_to_s3(mock_file)
    # Assert
    assert file_url == "https://test-bucket.test-url/fake_hash.txt"
    assert filename == "fake_hash.txt"
    assert file_extension == ".txt"

    # Verify that the necessary methods were called
    mock_calculate_file_hash.assert_called_once_with(mock_file)
    mock_s3_client.head_object.assert_called_once_with(
        Bucket="test-bucket", Key="fake_hash.txt"
    )
    mock_s3_client.upload_fileobj.assert_called_once_with(
        mock_file.file,
        "test-bucket",
        "fake_hash.txt",
        ExtraArgs={"ContentType": "text/plain"},
    )


def test_get_file_object_from_s3_success(mock_aws_client):
    # Arrange
    file_key = "test/file.txt"
    mock_content = b"This is test content"
    mock_content_type = "text/plain"

    mock_body = Mock()
    mock_body.read.return_value = mock_content

    mock_aws_client.get_object.return_value = {
        "Body": mock_body,
        "ContentType": mock_content_type,
    }

    # Act
    result = get_file_object_from_s3(file_key)

    # Assert
    assert isinstance(result, tuple)
    assert len(result) == 3
    returned_file_key, base64_content, returned_content_type = result

    assert returned_file_key == file_key
    assert base64_content == base64.b64encode(mock_content).decode("utf-8")
    assert returned_content_type == mock_content_type

    mock_aws_client.get_object.assert_called_once_with(
        Bucket=AWS_SLT_BUCKET_NAME, Key=file_key
    )


def test_get_file_object_from_s3_client_error(mock_aws_client):
    # Arrange
    file_key = "non-existent/file.txt"
    mock_aws_client.get_object.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist.",
            }
        },
        operation_name="GetObject",
    )

    # Act & Assert
    with pytest.raises(ClientError):
        get_file_object_from_s3(file_key)


def test_get_file_object_from_s3_key_error(mock_aws_client):
    # Arrange
    file_key = "test/file.txt"
    mock_aws_client.get_object.return_value = {}  # Missing expected keys

    # Act & Assert
    with pytest.raises(KeyError):
        get_file_object_from_s3(file_key)


@patch("ska_oso_slt_services.utils.s3_bucket.LOGGER")
def test_get_file_object_from_s3_client_error_logging(mock_logger, mock_aws_client):
    # Arrange
    file_key = "error/file.txt"
    error_message = "Access Denied"
    mock_aws_client.get_object.side_effect = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": error_message}},
        operation_name="GetObject",
    )

    # Act & Assert
    with pytest.raises(ClientError):
        get_file_object_from_s3(file_key)

    mock_logger.error.assert_called_once_with(
        "Error retrieving object from S3 bucket:%s",
        {
            "An error occurred (AccessDenied) when calling the "
            f"GetObject operation: {error_message}"
        },
    )


@patch("ska_oso_slt_services.utils.s3_bucket.LOGGER")
def test_get_file_object_from_s3_key_error_logging(mock_logger, mock_aws_client):
    # Arrange
    file_key = "test/file.txt"
    mock_aws_client.get_object.return_value = {}  # Missing expected keys

    # Act & Assert
    with pytest.raises(KeyError):
        get_file_object_from_s3(file_key)

    mock_logger.error.assert_called_once()  # Check if error was logged


def test_get_file_object_from_s3_large_file(mock_aws_client):
    # Arrange
    file_key = "large/file.bin"
    mock_content = b"0" * 1024 * 1024  # 1 MB of data
    mock_content_type = "application/octet-stream"

    mock_body = Mock()
    mock_body.read.return_value = mock_content

    mock_aws_client.get_object.return_value = {
        "Body": mock_body,
        "ContentType": mock_content_type,
    }

    # Act
    result = get_file_object_from_s3(file_key)

    # Assert
    assert isinstance(result, tuple)
    assert len(result) == 3
    returned_file_key, base64_content, returned_content_type = result

    assert returned_file_key == file_key
    assert base64_content == base64.b64encode(mock_content).decode("utf-8")
    assert returned_content_type == mock_content_type

    # Check if the content was read only once (efficient for large files)
    mock_body.read.assert_called_once()
