import json
import uuid
from typing import Any

import boto3


class AWSKinesisStream:
    """
    Wrapper class for interacting with an AWS Kinesis stream.

    Attributes:
    stream_name (str): The name of the Kinesis stream.
    region_name (str, optional): If not provided, the default region from the boto3 session will be used.

    aws_access_key_id (str, optional): The AWS access key ID for authentication.
    aws_secret_access_key (str, optional): The AWS secret access key for authentication.
    If not provided, the default aws credential resolution chain will be used for both parameters.
    """

    def __init__(
        self,
        stream_name: str,
        region_name: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
    ):
        if not stream_name:
            raise ValueError("Stream_name parameter is required.")

        self.stream_name = stream_name
        self.region_name = region_name or boto3.Session().region_name

        if aws_access_key_id and aws_secret_access_key:
            self.session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
        else:
            self.session = boto3.Session()

        self.client = self.session.client("kinesis", region_name=self.region_name)

    def send_to_stream(self, data: Any, partition_key: str | None = None) -> dict:
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

        response = self.client.put_record(
            StreamName=self.stream_name,
            Data=json.dumps(data),
            PartitionKey=partition_key,
        )
        return response
