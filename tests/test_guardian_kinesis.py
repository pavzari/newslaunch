# ruff: noqa: S105
import json
import os
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

from newslaunch.guardian_api import GuardianAPI
from newslaunch.kinesis_writer import KinesisWriter


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


@pytest.fixture
def guardian_api(monkeypatch):
    monkeypatch.setenv("GUARDIAN_API_KEY", "test-api-key")
    return GuardianAPI(os.getenv("GUARDIAN_API_KEY"))


@pytest.fixture
def sample_response():
    with open(
        os.path.join(os.path.dirname(__file__), "test_data/full_guardian_response.json")
    ) as f:
        return json.load(f)


@pytest.fixture
def filtered_sample_response():
    with open(
        os.path.join(
            os.path.dirname(__file__), "test_data/filtered_guardian_response.json"
        )
    ) as f:
        return json.load(f)


def test_search_articles_and_send_to_kinesis(
    guardian_api, kinesis_writer, sample_response, filtered_sample_response
):
    with patch("requests.get") as mocked_get:
        # mock get request to return a JSON sample of full API response:
        mock_response = MagicMock()
        mock_response.json.return_value = sample_response
        mock_response.status_code = 200
        mocked_get.return_value = mock_response

        articles = guardian_api.search_articles("test-query")

        # send the search result to a kinesis stream:
        response = kinesis_writer.send_to_stream(articles, record_per_entry=True)
        assert len(response["Records"]) == len(articles)

        client = boto3.client("kinesis", region_name="eu-west-2")
        stream = client.describe_stream(StreamName=kinesis_writer.stream_name)
        shards = stream["StreamDescription"]["Shards"]

        # iterrate through available shards in the stream and gather all the articles:
        stream_data = []
        for shard in shards:
            shard_iterator = client.get_shard_iterator(
                StreamName=kinesis_writer.stream_name,
                ShardId=shard["ShardId"],
                ShardIteratorType="TRIM_HORIZON",
            )["ShardIterator"]

            shard_data = client.get_records(ShardIterator=shard_iterator)
            data = [json.loads(record["Data"]) for record in shard_data["Records"]]
            stream_data.extend(data)

        # we expect the records in the stream to match the "filtered_sample_response"
        # which is what the guardian wrapper returns after parsing the full API
        # response with default settings.
        assert len(filtered_sample_response) == len(stream_data)

        for article in filtered_sample_response:
            assert article in stream_data
