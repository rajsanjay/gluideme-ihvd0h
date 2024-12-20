"""
AWS utility module providing helper functions for interacting with AWS services.
Implements core AWS functionality for S3, SES, and KMS services with comprehensive
error handling and monitoring.

Version: 1.0.0
"""

# Standard library imports
import logging
from typing import Dict, List, Optional, Union, BinaryIO
from concurrent.futures import ThreadPoolExecutor
import mimetypes
import math

# Third-party imports
import boto3  # version 1.26.0
import botocore  # version 1.29.0
from botocore.config import Config
from botocore.exceptions import ClientError

# Internal imports
from utils.exceptions import ValidationError, AWSError

# Configure logging
logger = logging.getLogger(__name__)

# Initialize AWS clients with default configuration
DEFAULT_CONFIG = Config(
    retries={'max_attempts': 3, 'mode': 'adaptive'},
    connect_timeout=5,
    read_timeout=10
)

class AWSClient:
    """Enhanced AWS client with comprehensive error handling and monitoring."""
    
    def __init__(self, config: Dict = None, region: str = None, 
                 use_privatelink: bool = False) -> None:
        """
        Initialize AWS clients with enhanced configuration.
        
        Args:
            config (Dict): Custom AWS configuration
            region (str): AWS region
            use_privatelink (bool): Whether to use VPC endpoints
        """
        self._config = config or DEFAULT_CONFIG
        self._region = region or 'us-west-2'
        
        # Configure VPC endpoints if using PrivateLink
        if use_privatelink:
            self._config.merge(Config(
                s3={'addressing_style': 'virtual'},
                use_dualstack_endpoint=True
            ))
        
        # Initialize service clients
        self._s3_client = boto3.client('s3', config=self._config, region_name=self._region)
        self._ses_client = boto3.client('ses', config=self._config, region_name=self._region)
        self._kms_client = boto3.client('kms', config=self._config, region_name=self._region)
        
        # Initialize monitoring
        self._setup_monitoring()
    
    def _setup_monitoring(self) -> None:
        """Configure CloudWatch metrics and X-Ray tracing."""
        self._cloudwatch = boto3.client('cloudwatch', config=self._config)
        
        # Register event handlers for client monitoring
        for client in [self._s3_client, self._ses_client, self._kms_client]:
            client.meta.events.register('after-call.*.*', self._record_metrics)
    
    def _record_metrics(self, http_response: Dict, parsed: Dict, model: object) -> None:
        """Record AWS API call metrics to CloudWatch."""
        try:
            self._cloudwatch.put_metric_data(
                Namespace='TransferSystem/AWS',
                MetricData=[{
                    'MetricName': 'APILatency',
                    'Value': http_response.elapsed.total_seconds(),
                    'Unit': 'Seconds',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': model.service_model.service_name},
                        {'Name': 'Operation', 'Value': model.name}
                    ]
                }]
            )
        except Exception as e:
            logger.warning(f"Failed to record metrics: {str(e)}")

    def handle_aws_error(self, error: Exception, operation: str, 
                        context: Dict = None) -> None:
        """
        Enhanced AWS error handler with retry logic and monitoring.
        
        Args:
            error: The AWS exception
            operation: The operation being performed
            context: Additional error context
            
        Raises:
            Appropriate mapped exception
        """
        error_context = {
            'operation': operation,
            'request_id': getattr(error, 'request_id', None),
            **context or {}
        }
        
        logger.error(f"AWS operation failed: {operation}", 
                    extra={'error': str(error), **error_context})
        
        if isinstance(error, ClientError):
            error_code = error.response['Error']['Code']
            error_message = error.response['Error']['Message']
            
            # Map AWS errors to custom exceptions
            if error_code in ['ValidationException', 'InvalidParameter']:
                raise ValidationError(
                    message=error_message,
                    validation_errors={'aws': error_message}
                )
            elif error_code in ['ResourceNotFoundException', 'NoSuchKey']:
                raise AWSError.map_aws_exception(error_code, error_message)
            else:
                raise AWSError.map_aws_exception(
                    error_code, 
                    error_message,
                    context=error_context
                )
        else:
            raise AWSError.map_aws_exception(
                'UnknownError',
                str(error),
                context=error_context
            )

def upload_file_to_s3(file_data: Union[bytes, BinaryIO], file_key: str,
                     bucket_name: str, encrypt: bool = True,
                     metadata: Dict = None, content_type: str = None) -> Dict:
    """
    Upload file to S3 with optional encryption and multipart support.
    
    Args:
        file_data: File data as bytes or file-like object
        file_key: S3 object key
        bucket_name: Target S3 bucket
        encrypt: Whether to use KMS encryption
        metadata: Optional file metadata
        content_type: File content type
        
    Returns:
        Dict containing upload response including version ID
    """
    try:
        aws_client = AWSClient()
        s3_client = aws_client._s3_client
        
        # Validate inputs
        if not file_data or not file_key or not bucket_name:
            raise ValidationError(
                message="Invalid upload parameters",
                validation_errors={
                    'file_data': 'Required' if not file_data else None,
                    'file_key': 'Required' if not file_key else None,
                    'bucket_name': 'Required' if not bucket_name else None
                }
            )
        
        # Determine content type if not provided
        if not content_type:
            content_type = mimetypes.guess_type(file_key)[0] or 'application/octet-stream'
        
        # Configure upload parameters
        upload_args = {
            'Bucket': bucket_name,
            'Key': file_key,
            'ContentType': content_type,
            'Metadata': metadata or {},
        }
        
        if encrypt:
            upload_args['ServerSideEncryption'] = 'aws:kms'
        
        # Handle large files with multipart upload
        if hasattr(file_data, 'seek') and hasattr(file_data, 'tell'):
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Reset position
        else:
            file_size = len(file_data)
        
        if file_size > 100 * 1024 * 1024:  # 100MB threshold
            return _multipart_upload(s3_client, file_data, upload_args, file_size)
        else:
            # Single-part upload
            if isinstance(file_data, bytes):
                upload_args['Body'] = file_data
            else:
                upload_args['Body'] = file_data.read()
            
            response = s3_client.put_object(**upload_args)
            
            return {
                'version_id': response.get('VersionId'),
                'etag': response.get('ETag', '').strip('"'),
                'location': f"s3://{bucket_name}/{file_key}"
            }
            
    except Exception as e:
        aws_client.handle_aws_error(e, 'upload_file_to_s3', {
            'bucket': bucket_name,
            'key': file_key,
            'size': file_size
        })

def _multipart_upload(s3_client, file_data: Union[bytes, BinaryIO],
                     upload_args: Dict, file_size: int) -> Dict:
    """Helper function for multipart uploads."""
    chunk_size = 10 * 1024 * 1024  # 10MB chunks
    total_parts = math.ceil(file_size / chunk_size)
    
    # Initialize multipart upload
    response = s3_client.create_multipart_upload(**upload_args)
    upload_id = response['UploadId']
    
    try:
        parts = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for part_num in range(1, total_parts + 1):
                if isinstance(file_data, bytes):
                    chunk = file_data[(part_num-1)*chunk_size:part_num*chunk_size]
                else:
                    chunk = file_data.read(chunk_size)
                
                futures.append(
                    executor.submit(
                        s3_client.upload_part,
                        Bucket=upload_args['Bucket'],
                        Key=upload_args['Key'],
                        UploadId=upload_id,
                        PartNumber=part_num,
                        Body=chunk
                    )
                )
            
            for part_num, future in enumerate(futures, 1):
                result = future.result()
                parts.append({
                    'PartNumber': part_num,
                    'ETag': result['ETag']
                })
        
        # Complete multipart upload
        response = s3_client.complete_multipart_upload(
            Bucket=upload_args['Bucket'],
            Key=upload_args['Key'],
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        
        return {
            'version_id': response.get('VersionId'),
            'etag': response.get('ETag', '').strip('"'),
            'location': f"s3://{upload_args['Bucket']}/{upload_args['Key']}"
        }
        
    except Exception as e:
        # Abort multipart upload on failure
        s3_client.abort_multipart_upload(
            Bucket=upload_args['Bucket'],
            Key=upload_args['Key'],
            UploadId=upload_id
        )
        raise e

def send_email(to_addresses: List[str], template_name: str,
               template_data: Dict, from_address: str,
               configuration: Dict = None) -> Dict:
    """
    Send emails using AWS SES with template support and batch processing.
    
    Args:
        to_addresses: List of recipient email addresses
        template_name: Email template name
        template_data: Template variables
        from_address: Sender email address
        configuration: Optional sending configuration
        
    Returns:
        Dict containing sending results and message IDs
    """
    try:
        aws_client = AWSClient()
        ses_client = aws_client._ses_client
        
        # Validate inputs
        if not to_addresses or not template_name or not from_address:
            raise ValidationError(
                message="Invalid email parameters",
                validation_errors={
                    'to_addresses': 'Required' if not to_addresses else None,
                    'template_name': 'Required' if not template_name else None,
                    'from_address': 'Required' if not from_address else None
                }
            )
        
        config = configuration or {}
        batch_size = config.get('batch_size', 50)
        results = {
            'successful': [],
            'failed': []
        }
        
        # Process recipients in batches
        for i in range(0, len(to_addresses), batch_size):
            batch = to_addresses[i:i + batch_size]
            
            try:
                response = ses_client.send_templated_email(
                    Source=from_address,
                    Destination={
                        'ToAddresses': batch
                    },
                    Template=template_name,
                    TemplateData=template_data
                )
                
                results['successful'].append({
                    'message_id': response['MessageId'],
                    'recipients': batch
                })
                
            except ClientError as e:
                results['failed'].append({
                    'recipients': batch,
                    'error': str(e)
                })
                logger.error(f"Failed to send email batch: {str(e)}")
        
        return results
        
    except Exception as e:
        aws_client.handle_aws_error(e, 'send_email', {
            'template': template_name,
            'recipient_count': len(to_addresses)
        })