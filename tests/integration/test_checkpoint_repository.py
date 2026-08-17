from src.repositories.checkpoint_repository import (
    CheckpointRepository,
)


repository = CheckpointRepository()

pipeline_name = "servicenow_incidents"

checkpoint = repository.get_checkpoint(
    pipeline_name
)

print(
    f"Existing checkpoint: {checkpoint}"
)

repository.save_checkpoint(
    pipeline_name=pipeline_name,
    timestamp="2026-08-14 19:59:33",
)

checkpoint = repository.get_checkpoint(
    pipeline_name
)

print(
    f"Updated checkpoint: {checkpoint}"
)