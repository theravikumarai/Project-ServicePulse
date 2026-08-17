import boto3
import pandas as pd
import streamlit as st

from config import (
    AWS_REGION,
    REDSHIFT_WORKGROUP,
    REDSHIFT_DATABASE,
)


class RedshiftClient:

    def __init__(self):

        self.region = st.secrets.get(
            "AWS_DEFAULT_REGION",
            AWS_REGION,
        )

        self.workgroup = st.secrets.get(
            "REDSHIFT_WORKGROUP",
            REDSHIFT_WORKGROUP,
        )

        self.database = st.secrets.get(
            "REDSHIFT_DATABASE",
            REDSHIFT_DATABASE,
        )

        self.secret_arn = st.secrets[
            "REDSHIFT_SECRET_ARN"
        ]

        self.client = boto3.client(
            "redshift-data",
            region_name=self.region,
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

            if status["Status"] == "FINISHED":
                break

            if status["Status"] in {
                "FAILED",
                "ABORTED",
            }:
                raise RuntimeError(
                    status.get(
                        "Error",
                        "Redshift query failed.",
                    )
                )

        result = self.client.get_statement_result(
            Id=statement_id
        )

        columns = [
            column["name"]
            for column in result["ColumnMetadata"]
        ]

        rows = []

        for record in result["Records"]:

            row = []

            for value in record:

                if "stringValue" in value:
                    row.append(value["stringValue"])

                elif "longValue" in value:
                    row.append(value["longValue"])

                elif "doubleValue" in value:
                    row.append(value["doubleValue"])

                elif "booleanValue" in value:
                    row.append(value["booleanValue"])

                elif value.get("isNull"):
                    row.append(None)

                else:
                    row.append(None)

            rows.append(row)

        return pd.DataFrame(
            rows,
            columns=columns,
        )