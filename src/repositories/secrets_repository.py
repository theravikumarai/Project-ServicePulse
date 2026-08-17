import json

import boto3


class SecretsRepository:

    def __init__(self, region_name="ap-south-1"):
        self.client = boto3.client(
            "secretsmanager",
            region_name=region_name,
        )

    def get_secret(self, secret_name):
        response = self.client.get_secret_value(
            SecretId=secret_name
        )

        secret_string = response.get("SecretString")

        if not secret_string:
            raise ValueError(
                f"Secret '{secret_name}' does not contain SecretString."
            )

        return json.loads(secret_string)