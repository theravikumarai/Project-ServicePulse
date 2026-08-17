from src.ingestion.servicenow_client import ServiceNowClient


client = ServiceNowClient()

last_updated_on = "2026-04-29 19:56:12"

incidents = client.get_incremental_incidents(
    last_updated_on=last_updated_on,
    overlap_minutes=5,
    page_size=10,
)

print()
print(f"Total records received: {len(incidents)}")
print()

for incident in incidents:
    print(
        incident["number"],
        "-",
        incident["sys_updated_on"]
    )