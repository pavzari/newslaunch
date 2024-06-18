# ruff: noqa: S105
import json
import os

import boto3
import pytest
from moto import mock_aws

from newslaunch.kinesis_writer import KinesisWriter, KinesisWriterError


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
    os.environ["AWS_SECURITY_TOKEN"] = "test"
    os.environ["AWS_SESSION_TOKEN"] = "test"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture(scope="function")
def mock_kinesis_stream(aws_credentials):
    with mock_aws():
        conn = boto3.client("kinesis", region_name="eu-west-2")
        stream_name = "test-stream"
        conn.create_stream(StreamName=stream_name, ShardCount=3)
        yield stream_name


@pytest.fixture
def kinesis_writer(mock_kinesis_stream):
    kinesis_writer = KinesisWriter(stream_name=mock_kinesis_stream)
    yield kinesis_writer


def test_send_single_record_using_put_record(kinesis_writer):
    data = {"key": "value"}
    response = kinesis_writer.send_to_stream(data)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_send_multiple_records_using_put_records(kinesis_writer):
    data = [{"key": "value1"}, {"key": "value2"}]
    response = kinesis_writer.send_to_stream(data, record_per_entry=True)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    assert len(response["Records"]) == 2


def test_send_too_large_record_put_record(kinesis_writer):
    large_data = {"key": "value" * (1024 * 2000)}
    with pytest.raises(KinesisWriterError, match="exceeds the 1MiB limit"):
        kinesis_writer.send_to_stream(large_data)


def test_send_too_large_record_put_records(kinesis_writer):
    large_data = [{"key": "value" * (1024 * 3000)}, {"key2": "value2" * (1024 * 3000)}]
    with pytest.raises(KinesisWriterError, match="exceeds the 5MiB limit"):
        kinesis_writer.send_to_stream(large_data, record_per_entry=True)


def test_send_over_record_count_limit_put_record(kinesis_writer):
    data = [b"x"] * 501
    with pytest.raises(KinesisWriterError, match="exceeds the 500 record limit"):
        kinesis_writer.send_to_stream(data, record_per_entry=True)


def test_send_non_serializable_data(kinesis_writer):
    data = {"non_serializable": lambda x: x}
    with pytest.raises(TypeError, match="is not JSON serializable"):
        kinesis_writer.send_to_stream(data)


def test_send_records_with_partition_key_gets_assigned_to_all_in_batch(kinesis_writer):
    # If sending a batch using put_records with specified partition key, all records get the same
    # partition key and should end up in the same shard.
    data = [{"key": "value1"}, {"key2": "value2"}]
    partition_key = "test_partition_key"
    response = kinesis_writer.send_to_stream(
        data, partition_key=partition_key, record_per_entry=True
    )
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    shard_ids = {record["ShardId"] for record in response["Records"]}
    assert len(shard_ids) == 1


def test_send_and_read_from_the_same_stream(kinesis_writer, mock_kinesis_stream):
    data = [{"test1": "example1"}, {"test2": "example2"}]

    response = kinesis_writer.send_to_stream(data, record_per_entry=True)
    assert len(response["Records"]) == 2

    client = boto3.client("kinesis", region_name="eu-west-2")
    stream = client.describe_stream(StreamName=mock_kinesis_stream)
    shards = stream["StreamDescription"]["Shards"]

    get_stream_data = []
    for shard in shards:
        shard_iterator = client.get_shard_iterator(
            StreamName=mock_kinesis_stream,
            ShardId=shard["ShardId"],
            ShardIteratorType="TRIM_HORIZON",
        )["ShardIterator"]

        records_response = client.get_records(ShardIterator=shard_iterator)
        data = [json.loads(record["Data"]) for record in records_response["Records"]]
        get_stream_data.extend(data)

    # Check without without relying on the order
    for record in data:
        assert record in get_stream_data
