import base64
import json
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def process_article(record: bytes) -> dict:
    article_data = base64.b64decode(record).decode("utf-8")
    return json.loads(article_data)


def lambda_handler(event: dict, context) -> None:
    log.info("Processing new batch of articles.")

    for record in event["Records"]:
        try:
            article = process_article(record["kinesis"]["data"])
            log.info(f"Article processed: {article}")
        except Exception as e:
            log.error(f"Error processing article: {record}. Exception: {e}")
            # raise to retry?
    log.info("Processing complete.")
