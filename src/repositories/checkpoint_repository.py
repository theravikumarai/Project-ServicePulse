import os
from datetime import datetime, timezone

import boto3
from dotenv import load_dotenv


load_dotenv()


class CheckpointRepository:

    def __init__(self, table_name=None):
        self.table_name = (
            table_name
            or os.getenv("CHECKPOINT_TABLE_NAME")
        )

        if not self.table_name:
            raise ValueError(
                "CHECKPOINT_TABLE_NAME is not configured."
            )

        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(
            self.table_name
        )

    def get_checkpoint(self, pipeline_name):
        response = self.table.get_item(
            Key={
                "pipeline_name": pipeline_name
            }
        )

        item = response.get("Item")

        if not item:
            return None

        return item.get(
            "last_successful_timestamp"
        )

    def save_checkpoint(
        self,
        pipeline_name,
        timestamp,
    ):
        updated_at = datetime.now(
            timezone.utc
        ).isoformat()

        self.table.put_item(
            Item={
                "pipeline_name": pipeline_name,
                "last_successful_timestamp": timestamp,
                "updated_at": updated_at,
            }
        )