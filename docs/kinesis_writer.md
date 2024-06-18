## Overview

The `KinesisWriter` class is a helper utility for writing data to an AWS Kinesis stream. This class intends to simplify the interaction with the AWS Kinesis API by handling data serialization, formatting, and partition key generation.

## Usage

### Initialization

To create an instance of `KinesisWriter`, you need to provide the stream name. Optionally, you can also specify the AWS region and AWS credentials.

If AWS credentials are not provided, the KinesisWriter class will use the default boto3 AWS credential resolution chain, which works locally as well as on AWS Lambda.

```python
from newslaunch.kinesis_writer import KinesisWriter

kinesis_writer = KinesisWriter(
    stream_name="your_kinesis_stream_name",
    region_name="your_aws_region",  # Optional
    aws_access_key_id="your_aws_access_key_id",  # Optional
    aws_secret_access_key="your_aws_secret_access_key"  # Optional
)
```

## Methods

### `send_to_stream`

The `send_to_stream` method allows you to send data to the Kinesis stream. You can send either a single record or multiple records.

#### Parameters

- `data`: The data to send to the stream. Can be a single item or a list of items. Each item can be a JSON-serializable object, string, or bytes.
- `partition_key` (str, optional): The partition key to use. If not provided, a random UUID will be generated for the single record or for each individual record if the `record_per_entry` flag is `True`. This is to distribute the records across different shards for within the Kinesis stream.
- `record_per_entry` (bool, optional): This parameter determines whether to send multiple records in a single request or to send each record individually.
  - If `True`, the method uses Kinesis API `put_records` method and expects `data` to be a list of items. Each item should be JSON-serializable. This approach is efficient for sending multiple records in a single HTTP API call but has limitations on the number of records (up to 500) and the total payload size (up to 5 MiB).
  - If `False`, the method uses `put_record` to send a single record per API call. This is suitable for sending individual records without batching. Anything passed to the method via `data` parameter, will be sent as a content of a single record.

When using either `put_record` or `put_records`, it is important that the items are JSON-serializable before sending them to the stream. Non-serializable items should be converted to a serializable format, such as a string or a dictionary, before attempting to send them.

#### Returns

- `dict`: The response from the Kinesis API call.

#### Raises

- `KinesisWriterError`: If there is an error with the provided data.

### Example

```python
data = {"webUrl": "https://example.co.uk"}
response = kinesis_writer.send_to_stream(data)
print(response)
```

## Exception Handling

The `KinesisWriter` class uses a custom exception `KinesisWriterError` for some errors. These exceptions can occur when:

- Stream name is missing during initialization.
- Data being sent exceeds Kinesis limits.

The KinesisWriter class does not internally handle boto3 exceptions such as ClientError or other potential errors that may arise during the API calls. Users are encouraged to implement their own error handling and retry logic based on the errors received from the response object. See example below.

## Examples

```python
from streamlaunch.kinesis_writer import KinesisWriter

kinesis_writer = KinesisWriter(stream_name="my_stream")

data ={"webUrl": "https://example.co.uk", "content": "Example content..."}
response = kinesis_writer.send_to_stream(data)
print(response)
```

```python
from streamlaunch.kinesis_writer import KinesisWriter

kinesis_writer = KinesisWriter(stream_name="my_stream")

data = [
    {"webUrl": "https://example.co.uk", "content": "Example content..."},
    {"webUrl": "https://example.co.uk", "content": "More example content..."}
]

# Each item in the list will appear as a single record in the stream.
# Each record will be assigned the same partition key.
response = kinesis_writer.send_to_stream(data, record_per_entry=True, partition_key="example.co.uk")
```

### Error Handling Examples

```python
from streamlaunch.kinesis_writer import KinesisWriter
from botocore.exceptions import ClientError
import time

kinesis_writer = KinesisWriter(stream_name="my_stream")

def send_with_retries(kinesis_writer, data, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            response = kinesis_writer.send_to_stream(data)
            print("Data sent:", response)
            return response
        except ClientError as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                print("Throughput limit exceeded, retrying...")
                time.sleep(delay)
            else:
                print("Error, could not send records:", e.response)
                break
    print("Failed to send data after multiple attempts")


data = {"data": "example"}
kinesis_writer = KinesisWriter(stream_name="my_stream")
send_with_retries(kinesis_writer, data)
```

```python
def send_with_failed_record_handling(kinesis_writer, data):
    response = kinesis_writer.send_to_stream(data, record_per_entry=True)
    if response['FailedRecordCount'] > 0:
       ...

data = [{"data": "example"}, {"data2": "example2"}]
kinesis_writer = KinesisWriter(stream_name="my_stream")
send_with_failed_record_handling(kinesis_writer, data)
```
