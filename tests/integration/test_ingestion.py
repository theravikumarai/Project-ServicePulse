from src.ingestion.servicenow_client import ServiceNowClient
from src.repositories.s3_repository import S3Repository


def main():

    servicenow_client = ServiceNowClient()
    s3_repository = S3Repository()

    # Temporary checkpoint for testing
    last_updated_on = "2026-04-29 19:56:12"

    incidents = servicenow_client.get_incremental_incidents(
        last_updated_on=last_updated_on,
        overlap_minutes=5,
        page_size=10,
    )

    print(
        f"Records fetched from ServiceNow: "
        f"{len(incidents)}"
    )

    if not incidents:
        print("No new incidents found.")
        return

    key = s3_repository.upload_json(
        records=incidents,
        source="servicenow",
        entity="incidents",
    )

    print(
        "Bronze data written to:"
    )

    print(
        f"s3://{s3_repository.bucket_name}/{key}"
    )


if __name__ == "__main__":
    main()