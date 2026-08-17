import os

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

        # ---------------------------------------------------------
        # AWS Configuration
        # ---------------------------------------------------------

        # Streamlit Cloud Secrets take priority.
        # Local development falls back to your existing config.py
        # and default AWS credential chain.
        region = st.secrets.get(
            "AWS_DEFAULT_REGION",
            os.getenv("AWS_DEFAULT_REGION", AWS_REGION),
        )

        self.workgroup = st.secrets.get(
            "REDSHIFT_WORKGROUP",
            REDSHIFT_WORKGROUP,
        )

        self.database = st.secrets.get(
            "REDSHIFT_DATABASE",
            REDSHIFT_DATABASE,
        )

        self.db_user = st.secrets.get(
            "REDSHIFT_DB_USER",
            "streamlit_reader",
        )

        # ---------------------------------------------------------
        # Create Redshift Data API client
        # ---------------------------------------------------------

        access_key = st.secrets.get(
            "AWS_ACCESS_KEY_ID",
            os.getenv("AWS_ACCESS_KEY_ID"),
        )

        secret_key = st.secrets.get(
            "AWS_SECRET_ACCESS_KEY",
            os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

        # Cloud: use credentials from Streamlit Secrets
        # Local: use normal boto3 credential chain
        if access_key and secret_key:

            self.client = boto3.client(
                "redshift-data",
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )

        else:

            self.client = boto3.client(
                "redshift-data",
                region_name=region,
            )

    # -------------------------------------------------------------
    # Execute SQL Query
    # -------------------------------------------------------------

    def execute_query(self, sql: str) -> pd.DataFrame:

        response = self.client.execute_statement(
            WorkgroupName=self.workgroup,
            Database=self.database,
            DbUser=self.db_user,
            Sql=sql,
        )

        statement_id = response["Id"]

        # ---------------------------------------------------------
        # Wait for query completion
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Get query result
        # ---------------------------------------------------------

        result = self.client.get_statement_result(
            Id=statement_id
        )

        # ---------------------------------------------------------
        # Extract columns
        # ---------------------------------------------------------

        columns = [
            column["name"]
            for column in result["ColumnMetadata"]
        ]

        # ---------------------------------------------------------
        # Extract rows
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Return DataFrame
        # ---------------------------------------------------------

        return pd.DataFrame(
            rows,
            columns=columns,
        )