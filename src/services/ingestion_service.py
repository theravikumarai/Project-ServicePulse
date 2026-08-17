from datetime import datetime, timedelta, timezone

from src.ingestion.servicenow_client import ServiceNowClient
from src.repositories.checkpoint_repository import CheckpointRepository
from src.repositories.s3_repository import S3Repository


class IngestionService:

    PIPELINE_NAME = "servicenow_incidents"

    def __init__(
        self,
        servicenow_client=None,
        checkpoint_repository=None,
        s3_repository=None,
    ):
        self.servicenow_client = (
            servicenow_client
            or ServiceNowClient()
        )

        self.checkpoint_repository = (
            checkpoint_repository
            or CheckpointRepository()
        )

        self.s3_repository = (
            s3_repository
            or S3Repository()
        )

    def run(self):

        # 1. Get last successful checkpoint
        checkpoint = (
            self.checkpoint_repository.get_checkpoint(
                self.PIPELINE_NAME
            )
        )

        # 2. Determine extraction start
        if checkpoint:
            checkpoint_dt = datetime.strptime(
                checkpoint,
                "%Y-%m-%d %H:%M:%S",
            )

            extraction_start = (
                checkpoint_dt - timedelta(minutes=5)
            )

        else:
            # Initial load fallback
            extraction_start = (
                datetime.now(timezone.utc)
                - timedelta(days=1)
            )

        extraction_start_str = (
            extraction_start.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        print(
            f"Checkpoint: {checkpoint}"
        )

        print(
            f"Extraction start: "
            f"{extraction_start_str}"
        )

        # 3. Extract incremental incidents
        incidents = (
            self.servicenow_client
            .get_incremental_incidents(
                last_updated_on=extraction_start_str,
                overlap_minutes=0,
                page_size=10,
            )
        )

        print(
            f"Records received: "
            f"{len(incidents)}"
        )

        # 4. Nothing to process
        if not incidents:
            print("No new incidents found.")

            return {
                "status": "success",
                "records_processed": 0,
                "checkpoint": checkpoint,
            }

        # 5. Write to Bronze
        key = self.s3_repository.upload_json(
            records=incidents,
            source="servicenow",
            entity="incidents",
        )

        print(
            f"Bronze file written: {key}"
        )

        # 6. Determine new checkpoint
        max_updated_on = max(
            record["sys_updated_on"]
            for record in incidents
            if record.get("sys_updated_on")
        )

        # 7. Update checkpoint ONLY after S3 success
        self.checkpoint_repository.save_checkpoint(
            pipeline_name=self.PIPELINE_NAME,
            timestamp=max_updated_on,
        )

        print(
            f"Checkpoint updated: "
            f"{max_updated_on}"
        )

        return {
            "status": "success",
            "records_processed": len(incidents),
            "s3_key": key,
            "checkpoint": max_updated_on,
        }