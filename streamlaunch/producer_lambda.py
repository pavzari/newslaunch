import json
import logging

from botocore.exceptions import ClientError
from config import get_config
from guardian_api import GuardianAPI, GuardianAPIError
from kinesis_client import AWSKinesisStream

logging.basicConfig(level=get_config().LOG_LEVEL)
log = logging.getLogger(__name__)


def lambda_handler(event: dict, context) -> dict:

    # If the event comes from the API gateway:
    if "body" in event:
        try:
            body = json.loads(event["body"])
            search_term = body.get("search_term")
            from_date = body.get("from_date")
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
        stream_name = event.get("guardian_content")  # not sure about this..

    try:
        guardian_api = GuardianAPI(get_config().GUARDIAN_API_KEY)
        kinesis = AWSKinesisStream(stream_name)

        search_results = guardian_api.get_articles(search_term, from_date)
        response = kinesis.send_to_stream(search_results)

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
