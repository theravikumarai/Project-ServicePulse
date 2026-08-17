import os
import time
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

from src.repositories.secrets_repository import SecretsRepository


load_dotenv()


class ServiceNowClient:

    def __init__(self):
        self._load_credentials()

        # Prevent double slash in API URL
        self.endpoint = (
            f"{self.instance_url.rstrip('/')}"
            "/api/now/table/incident"
        )

    def _load_credentials(self):
        """
        Load ServiceNow credentials.

        Local development:
            Credentials are loaded from .env

        AWS Lambda:
            Credentials are loaded from AWS Secrets Manager
        """

        # -----------------------------------------
        # AWS Lambda
        # -----------------------------------------

        if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):

            secret_name = os.getenv(
                "SERVICENOW_SECRET_NAME"
            )

            if not secret_name:
                raise ValueError(
                    "SERVICENOW_SECRET_NAME is not configured."
                )

            secrets_repository = SecretsRepository(
                region_name=os.getenv(
                    "AWS_REGION",
                    "ap-south-1",
                )
            )

            credentials = (
                secrets_repository.get_secret(
                    secret_name
                )
            )

            self.instance_url = credentials.get(
                "instance_url"
            )

            self.username = credentials.get(
                "username"
            )

            self.password = credentials.get(
                "password"
            )

        # -----------------------------------------
        # Local development
        # -----------------------------------------

        else:

            self.instance_url = os.getenv(
                "SERVICENOW_INSTANCE_URL"
            )

            self.username = os.getenv(
                "SERVICENOW_USERNAME"
            )

            self.password = os.getenv(
                "SERVICENOW_PASSWORD"
            )

        # -----------------------------------------
        # Validate credentials
        # -----------------------------------------

        if not all([
            self.instance_url,
            self.username,
            self.password,
        ]):
            raise ValueError(
                "ServiceNow credentials are not configured."
            )

    def get_incident_page(
        self,
        limit=10,
        offset=0,
        query=None,
    ):
        """
        Fetch a single page of incidents from ServiceNow.

        Includes retry handling for transient failures
        and validation of the ServiceNow response.
        """

        params = {
            "sysparm_limit": limit,
            "sysparm_offset": offset,
            "sysparm_fields": (
                "sys_id,"
                "number,"
                "short_description,"
                "state,"
                "priority,"
                "urgency,"
                "impact,"
                "category,"
                "subcategory,"
                "sys_created_on,"
                "sys_updated_on"
            ),
        }

        if query:
            params["sysparm_query"] = query

        max_retries = 3

        for attempt in range(max_retries + 1):

            try:

                response = requests.get(
                    self.endpoint,
                    params=params,
                    auth=(
                        self.username,
                        self.password,
                    ),
                    timeout=30,
                )

                # ---------------------------------
                # SUCCESS
                # ---------------------------------

                if response.status_code == 200:

                    # Protect against empty responses
                    if not response.text.strip():

                        raise RuntimeError(
                            "ServiceNow returned HTTP 200 "
                            "but the response body is empty."
                        )

                    try:

                        data = response.json()

                    except requests.exceptions.JSONDecodeError as exc:

                        content_type = (
                            response.headers.get(
                                "Content-Type",
                                "unknown",
                            )
                        )

                        raise RuntimeError(
                            "ServiceNow returned a non-JSON "
                            "response. "
                            f"Status={response.status_code}, "
                            f"Content-Type={content_type}"
                        ) from exc

                    # ---------------------------------
                    # Validate result
                    # ---------------------------------

                    if "result" not in data:

                        raise RuntimeError(
                            "ServiceNow response does not "
                            "contain 'result'."
                        )

                    return data["result"]

                # ---------------------------------
                # RETRYABLE HTTP ERRORS
                # ---------------------------------

                if response.status_code in {
                    429,
                    500,
                    502,
                    503,
                    504,
                }:

                    if attempt == max_retries:

                        response.raise_for_status()

                    wait_time = 2 ** attempt

                    print(
                        "ServiceNow returned "
                        f"{response.status_code}. "
                        f"Retrying in {wait_time}s..."
                    )

                    time.sleep(wait_time)

                    continue

                # ---------------------------------
                # NON-RETRYABLE HTTP ERRORS
                # ---------------------------------

                response.raise_for_status()

            # -------------------------------------
            # TIMEOUT
            # -------------------------------------

            except requests.exceptions.Timeout:

                if attempt == max_retries:
                    raise

                wait_time = 2 ** attempt

                print(
                    "ServiceNow request timed out. "
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(wait_time)

            # -------------------------------------
            # CONNECTION ERROR
            # -------------------------------------

            except requests.exceptions.ConnectionError:

                if attempt == max_retries:
                    raise

                wait_time = 2 ** attempt

                print(
                    "Connection error. "
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(wait_time)

        raise RuntimeError(
            "ServiceNow request failed after retries."
        )

    def get_all_incidents(
        self,
        page_size=10,
    ):
        """
        Fetch all incidents using pagination.
        """

        return self._fetch_paginated(
            page_size=page_size
        )

    def get_incremental_incidents(
        self,
        last_updated_on,
        overlap_minutes=5,
        page_size=10,
    ):
        """
        Fetch incidents updated since the checkpoint.

        A small overlap window is used to protect
        against timestamp boundary issues.
        """

        checkpoint = datetime.strptime(
            last_updated_on,
            "%Y-%m-%d %H:%M:%S",
        )

        extraction_start = (
            checkpoint
            - timedelta(
                minutes=overlap_minutes
            )
        )

        extraction_start_str = (
            extraction_start.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        query = (
            f"sys_updated_on>={extraction_start_str}"
            "^ORDERBYsys_updated_on"
        )

        print(
            f"Checkpoint: {last_updated_on}"
        )

        print(
            "Extraction start: "
            f"{extraction_start_str}"
        )

        return self._fetch_paginated(
            page_size=page_size,
            query=query,
        )

    def _fetch_paginated(
        self,
        page_size=10,
        query=None,
    ):
        """
        Internal reusable pagination logic.
        """

        all_incidents = []
        offset = 0

        while True:

            records = self.get_incident_page(
                limit=page_size,
                offset=offset,
                query=query,
            )

            all_incidents.extend(records)

            print(
                f"Fetched {len(records)} records "
                f"from offset {offset}"
            )

            # Last page reached
            if len(records) < page_size:
                break

            offset += page_size

        return all_incidents