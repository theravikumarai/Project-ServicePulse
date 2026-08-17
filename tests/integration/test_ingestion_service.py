from src.services.ingestion_service import IngestionService


service = IngestionService()

result = service.run()

print("\nPipeline result:")
print(result)