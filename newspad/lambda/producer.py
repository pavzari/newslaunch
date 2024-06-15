import json
import logging

from botocore.exceptions import ClientError

from newslaunch import GuardianAPI, GuardianAPIError, KinesisWriter

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def lambda_handler(event: dict, context) -> dict:
    try:
        # If the event comes via the API gateway vs boto3:
        body = json.loads(event["body"]) if "body" in event else event

        search_term = body.get("search_term")
        stream_name = body.get("stream_name")

        optional_params = {
            "page_size": body.get("page_size"),
            "from_date": body.get("from_date"),
            "filter_response": body.get("filter_response"),
            "order_by": body.get("order_by"),
        }

        optional_params["filter_response"] = (
            optional_params["filter_response"].lower() == "true"
            if optional_params["filter_response"] is not None
            else None
        )

        optional_params = {k: v for k, v in optional_params.items() if v is not None}

        guardian_api = GuardianAPI()
        kinesis = KinesisWriter(stream_name)
        search_results = guardian_api.search_articles(search_term, **optional_params)

        if search_results:
            batch = True if len(search_results) > 1 else False
            kinesis.send_to_stream(search_results, record_per_entry=batch)
            log.info(f"Data published to {stream_name}")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": f"Data published to {stream_name}."}),
            }
        else:
            log.info(f"No results for '{search_term}' with provided parameters")
            return {
                "statusCode": 204,
                "body": json.dumps({"message": f"No results for '{search_term}'"}),
            }

    except json.JSONDecodeError:
        log.error("Failed to decode event JSON body.")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON in request body."}),
        }
    except ValueError as e:
        log.error(f"Invalid input: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Invalid input: {e}"}),
        }
    except (GuardianAPIError, ClientError) as e:
        log.error(f"Error processing request: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Internal server error: {e}"}),
        }
