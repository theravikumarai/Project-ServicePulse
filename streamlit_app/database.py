import time

import boto3
import pandas as pd
import streamlit as st

from config import (
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    REDSHIFT_SECRET_ARN,
    REDSHIFT_WORKGROUP,
    REDSHIFT_DATABASE,
)


class RedshiftClient:

    def __init__(self):

        self.region = AWS_REGION

        self.workgroup = REDSHIFT_WORKGROUP

        self.database = REDSHIFT_DATABASE

        self.secret_arn = REDSHIFT_SECRET_ARN

        self.client = boto3.client(
            "redshift-data",
            region_name=self.region,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

    def execute_query(self, sql: str) -> pd.DataFrame:

        response = self.client.execute_statement(
            WorkgroupName=self.workgroup,
            Database=self.database,
            SecretArn=self.secret_arn,
            Sql=sql,
        )

        statement_id = response["Id"]

        while True:

            status = self.client.describe_statement(
                Id=statement_id
            )

            current_status = status["Status"]

            if current_status == "FINISHED":
                break

            if current_status in {
                "FAILED",
                "ABORTED",
            }:
                raise RuntimeError(
                    status.get(
                        "Error",
                        "Redshift query failed.",
                    )
                )

            time.sleep(0.5)

        return self._get_results(statement_id)

    def _get_results(self, statement_id: str) -> pd.DataFrame:

        response = self.client.get_statement_result(
            Id=statement_id
        )

        columns = [
            column["name"]
            for column in response["ColumnMetadata"]
        ]

        rows = []

        for record in response["Records"]:

            row = []

            for value in record:

                if value.get("isNull"):
                    row.append(None)

                elif "stringValue" in value:
                    row.append(value["stringValue"])

                elif "longValue" in value:
                    row.append(value["longValue"])

                elif "doubleValue" in value:
                    row.append(value["doubleValue"])

                elif "booleanValue" in value:
                    row.append(value["booleanValue"])

                else:
                    row.append(None)

            rows.append(row)

        return pd.DataFrame(
            rows,
            columns=columns,
        )