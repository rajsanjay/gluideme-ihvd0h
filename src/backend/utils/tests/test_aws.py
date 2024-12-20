"""
Test suite for AWS utility functions covering S3, SES, and KMS operations.
Tests error handling, retries, and successful scenarios.

Version: 1.0.0
"""

# Standard library imports
import pytest
from unittest import mock
import io
import json
from typing import Dict, Any

# Third-party imports
import boto3  # version 1.26.0
from botocore.exceptions import ClientError  # version 1.29.0

# Internal imports
from utils.aws import (
    upload_file_to_s3,
    download_file_from_s3,
    send_email,
    encrypt_data,
    decrypt_data,
    AWSClient
)
from utils.exceptions import ValidationError, ServerError

class TestAWSClient:
    """Test AWS client functionality and error handling."""

    @pytest.fixture
    def aws_client(self):
        """Fixture for AWS client with mocked services."""
        with mock.patch('boto3.client') as mock_boto:
            # Configure mock responses
            mock_s3 = mock.MagicMock()
            mock_ses = mock.MagicMock()
            mock_kms = mock.MagicMock()
            mock_cloudwatch = mock.MagicMock()
            
            mock_boto.side_effect = lambda service, **kwargs: {
                's3': mock_s3,
                'ses': mock_ses,
                'kms': mock_kms,
                'cloudwatch': mock_cloudwatch
            }[service]
            
            client = AWSClient()
            client._s3_client = mock_s3
            client._ses_client = mock_ses
            client._kms_client = mock_kms
            client._cloudwatch = mock_cloudwatch
            
            yield client

    def test_handle_aws_error_validation(self, aws_client):
        """Test handling of AWS validation errors."""
        error_response = {
            'Error': {
                'Code': 'ValidationException',
                'Message': 'Invalid parameter value'
            }
        }
        error = ClientError(error_response, 'operation')

        with pytest.raises(ValidationError) as exc_info:
            aws_client.handle_aws_error(error, 'test_operation')
        
        assert 'Invalid parameter value' in str(exc_info.value)
        assert exc_info.value.error_code.startswith('VAL_')

    def test_handle_aws_error_not_found(self, aws_client):
        """Test handling of AWS resource not found errors."""
        error_response = {
            'Error': {
                'Code': 'ResourceNotFoundException',
                'Message': 'Resource not found'
            }
        }
        error = ClientError(error_response, 'operation')

        with pytest.raises(ServerError) as exc_info:
            aws_client.handle_aws_error(error, 'test_operation')
        
        assert 'Resource not found' in str(exc_info.value)
        assert exc_info.value.error_code.startswith('SRV_')

class TestS3Operations:
    """Test S3 upload and download operations."""

    @pytest.fixture
    def mock_s3_client(self):
        """Fixture for mocked S3 client."""
        with mock.patch('boto3.client') as mock_boto:
            mock_s3 = mock.MagicMock()
            mock_boto.return_value = mock_s3
            yield mock_s3

    @pytest.mark.asyncio
    async def test_upload_file_to_s3_success(self, mock_s3_client):
        """Test successful file upload to S3."""
        # Test data
        file_data = b"test content"
        file_key = "test/file.txt"
        bucket_name = "test-bucket"
        
        # Configure mock response
        mock_s3_client.put_object.return_value = {
            'VersionId': 'test-version',
            'ETag': '"test-etag"'
        }

        # Perform upload
        result = upload_file_to_s3(
            file_data=file_data,
            file_key=file_key,
            bucket_name=bucket_name,
            encrypt=True
        )

        # Verify upload
        mock_s3_client.put_object.assert_called_once_with(
            Bucket=bucket_name,
            Key=file_key,
            Body=file_data,
            ContentType='text/plain',
            ServerSideEncryption='aws:kms',
            Metadata={}
        )

        assert result['version_id'] == 'test-version'
        assert result['etag'] == 'test-etag'
        assert result['location'] == f"s3://{bucket_name}/{file_key}"

    @pytest.mark.asyncio
    async def test_upload_file_to_s3_multipart(self, mock_s3_client):
        """Test multipart upload for large files."""
        # Create large test file
        file_size = 150 * 1024 * 1024  # 150MB
        file_data = io.BytesIO(b"x" * file_size)
        file_key = "test/large_file.dat"
        bucket_name = "test-bucket"

        # Configure mock responses
        mock_s3_client.create_multipart_upload.return_value = {
            'UploadId': 'test-upload-id'
        }
        mock_s3_client.upload_part.return_value = {
            'ETag': '"test-etag"'
        }
        mock_s3_client.complete_multipart_upload.return_value = {
            'VersionId': 'test-version',
            'ETag': '"test-multipart-etag"'
        }

        # Perform upload
        result = upload_file_to_s3(
            file_data=file_data,
            file_key=file_key,
            bucket_name=bucket_name
        )

        # Verify multipart upload
        assert mock_s3_client.create_multipart_upload.called
        assert mock_s3_client.upload_part.called
        assert mock_s3_client.complete_multipart_upload.called
        assert result['version_id'] == 'test-version'

    @pytest.mark.asyncio
    async def test_upload_file_to_s3_error(self, mock_s3_client):
        """Test error handling during S3 upload."""
        error_response = {
            'Error': {
                'Code': 'NoSuchBucket',
                'Message': 'The specified bucket does not exist'
            }
        }
        mock_s3_client.put_object.side_effect = ClientError(
            error_response, 'PutObject'
        )

        with pytest.raises(ServerError) as exc_info:
            upload_file_to_s3(
                file_data=b"test",
                file_key="test.txt",
                bucket_name="nonexistent-bucket"
            )

        assert 'bucket does not exist' in str(exc_info.value)

class TestEmailOperations:
    """Test SES email operations."""

    @pytest.fixture
    def mock_ses_client(self):
        """Fixture for mocked SES client."""
        with mock.patch('boto3.client') as mock_boto:
            mock_ses = mock.MagicMock()
            mock_boto.return_value = mock_ses
            yield mock_ses

    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_ses_client):
        """Test successful email sending."""
        # Test data
        to_addresses = ['test@example.com']
        template_name = 'test-template'
        template_data = {'name': 'Test User'}
        from_address = 'sender@example.com'

        # Configure mock response
        mock_ses_client.send_templated_email.return_value = {
            'MessageId': 'test-message-id'
        }

        # Send email
        result = send_email(
            to_addresses=to_addresses,
            template_name=template_name,
            template_data=template_data,
            from_address=from_address
        )

        # Verify email sending
        assert len(result['successful']) == 1
        assert result['successful'][0]['message_id'] == 'test-message-id'
        assert len(result['failed']) == 0

    @pytest.mark.asyncio
    async def test_send_email_batch(self, mock_ses_client):
        """Test batch email sending."""
        # Test data
        to_addresses = [f'test{i}@example.com' for i in range(75)]
        template_name = 'test-template'
        template_data = {'name': 'Test User'}
        from_address = 'sender@example.com'

        # Configure mock response
        mock_ses_client.send_templated_email.return_value = {
            'MessageId': 'test-message-id'
        }

        # Send emails
        result = send_email(
            to_addresses=to_addresses,
            template_name=template_name,
            template_data=template_data,
            from_address=from_address,
            configuration={'batch_size': 50}
        )

        # Verify batch processing
        assert len(result['successful']) == 2  # Two batches
        assert mock_ses_client.send_templated_email.call_count == 2

    @pytest.mark.asyncio
    async def test_send_email_validation(self, mock_ses_client):
        """Test email parameter validation."""
        with pytest.raises(ValidationError) as exc_info:
            send_email(
                to_addresses=[],
                template_name='test-template',
                template_data={},
                from_address=''
            )

        assert 'Invalid email parameters' in str(exc_info.value)
        assert 'to_addresses' in exc_info.value.validation_errors
        assert 'from_address' in exc_info.value.validation_errors

def test_aws_client_initialization():
    """Test AWS client initialization with custom configuration."""
    with mock.patch('boto3.client') as mock_boto:
        client = AWSClient(
            config={'retries': {'max_attempts': 5}},
            region='us-east-1',
            use_privatelink=True
        )
        
        # Verify client initialization
        assert mock_boto.call_count == 4  # s3, ses, kms, cloudwatch
        assert client._region == 'us-east-1'
        
        # Verify PrivateLink configuration
        config_calls = [call[1].get('config') for call in mock_boto.call_args_list]
        assert any('use_dualstack_endpoint' in str(config) for config in config_calls)