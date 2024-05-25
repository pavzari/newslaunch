import json
import logging

from botocore.exceptions import ClientError
from config import get_config
from guardian_api import GuardianAPI, GuardianAPIError
from kinesis_client import AWSKinesisStream

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def lambda_handler(event: dict, context) -> dict:

    # If the event comes from the API gateway:
    if "body" in event:
        try:
            body = json.loads(event["body"])
            search_term = body.get("search_term")
            from_date = body.get("from_date")
            stream_name = event.get("stream_name")
        except json.JSONDecodeError:
            log.error("Failed to decode event JSON body.")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid JSON format in request body."}),
            }

    # Direct invocation (via boto3 e.g.)
    else:
        search_term = event.get("search_term")
        from_date = event.get("from_date")
        stream_name = event.get("stream_name")  # not sure about this..

    try:
        guardian_api = GuardianAPI(get_config().GUARDIAN_API_KEY)
        kinesis = AWSKinesisStream(stream_name)

        search_results = guardian_api.get_articles(search_term, from_date)
        if search_results is None:
            return {
                "statusCode": 204,
                "body": json.dumps({"message": "No data to process."}),
            }

        kinesis.send_to_stream(search_results)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Data processed and published to stream."}),
        }
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Invalid input parameter: {e}"}),
        }
    except (GuardianAPIError, ClientError) as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Internal server error: {e}"}),
        }
