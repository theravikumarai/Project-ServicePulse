from src.repositories.checkpoint_repository import (
    CheckpointRepository,
)


repository = CheckpointRepository()

repository.save_checkpoint(
    pipeline_name="servicenow_incidents",
    timestamp="2026-04-29 19:54:00",
)

print("Checkpoint reset successfully.")