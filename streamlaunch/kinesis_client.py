import json
import logging
import uuid

import boto3
from botocore.exceptions import ClientError
from config import get_config

config = get_config()
log = logging.getLogger(__name__)


class AWSKinesisStream:
    """
    Wrapper class for interacting with an AWS Kinesis stream.

    Attributes:
    stream_name (str): The name of the Kinesis stream.
    """

    def __init__(self, stream_name: str):
        self.stream_name = stream_name

    def _get_client(self):
        """Get AWS Kinesis client."""
        return boto3.client(
            "kinesis",
            region_name=config.KINESIS_REGION_NAME,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        )

    def send_to_stream(self, data: str, partition_key: str | None = None) -> dict:
        """
        Send data to Kinesis stream.

        Parameters:
        data: Data to send to the stream.
        partition_key(str, optional): Partition key to use. Defaults to random UUID.

        Returns:
        dict: The response from the Kinesis `put_record` API call.
        """
        if partition_key is None:
            partition_key = str(uuid.uuid4())

        try:
            client = self._get_client()
            response = client.put_record(
                StreamName=self.stream_name,
                # Data=json.dumps(data),
                Data=data,  # API wrapper returns a serialized JSON string, for now...
                PartitionKey=partition_key,
            )
            log.info("Put data to stream %s.", self.stream_name)
        except ClientError:
            log.exception("Error sending record to stream %s.", self.stream_name)
            raise
        else:
            return response
