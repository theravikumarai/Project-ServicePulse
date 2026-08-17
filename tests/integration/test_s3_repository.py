from src.repositories.s3_repository import S3Repository


repository = S3Repository()

records = [
    {
        "sys_id": "test-001",
        "number": "INC-TEST-001",
        "short_description": "ServicePulse S3 test",
    }
]

key = repository.upload_json(
    records=records,
    source="servicenow",
    entity="incidents",
    batch_id="test-001",
)

print(
    f"s3://{repository.bucket_name}/{key}"
)