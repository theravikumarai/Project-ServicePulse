from src.services.ingestion_service import IngestionService


def lambda_handler(event, context):
    service = IngestionService()

    result = service.run()

    return {
        "statusCode": 200,
        "body": result,
    }