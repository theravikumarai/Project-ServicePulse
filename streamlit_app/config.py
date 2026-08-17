import os

from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv(
    "AWS_REGION",
    "ap-south-1",
)

REDSHIFT_WORKGROUP = os.getenv(
    "REDSHIFT_WORKGROUP",
    "servicepulse-workgroup",
)

REDSHIFT_DATABASE = os.getenv(
    "REDSHIFT_DATABASE",
    "dev",
)

REDSHIFT_SCHEMA = os.getenv(
    "REDSHIFT_SCHEMA",
    "servicepulse",
)

REDSHIFT_TABLE = os.getenv(
    "REDSHIFT_TABLE",
    "fact_incidents",
)