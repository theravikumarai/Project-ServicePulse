import json
import os
from datetime import datetime, timezone
from pathlib import Path

import boto3
from dotenv import load_dotenv


# Project root:
# servicepulse/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")


class S3Repository:

    def __init__(self, bucket_name=None):
        self.bucket_name = (
            bucket_name
            or os.getenv("S3_BUCKET_NAME")
        )

        if not self.bucket_name:
            raise ValueError(
                "S3_BUCKET_NAME is not configured."
            )

        self.s3_client = boto3.client("s3")

    def upload_json(
        self,
        records,
        source="servicenow",
        entity="incidents",
        batch_id=None,
    ):
        """Upload records to the Bronze layer."""

        if not records:
            raise ValueError(
                "Cannot upload an empty record set."
            )

        ingestion_time = datetime.now(timezone.utc)

        year = ingestion_time.strftime("%Y")
        month = ingestion_time.strftime("%m")
        day = ingestion_time.strftime("%d")

        if batch_id is None:
            batch_id = ingestion_time.strftime(
                "%Y%m%dT%H%M%S"
            )

        key = (
            f"bronze/{source}/{entity}/"
            f"year={year}/"
            f"month={month}/"
            f"day={day}/"
            f"batch_{batch_id}.json"
        )

        payload = {
            "_metadata": {
                "source": source,
                "entity": entity,
                "ingestion_timestamp": (
                    ingestion_time.isoformat()
                ),
                "batch_id": batch_id,
                "record_count": len(records),
            },
            "records": records,
        }

        body = json.dumps(
            payload,
            ensure_ascii=False,
        )

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json",
        )

        return key