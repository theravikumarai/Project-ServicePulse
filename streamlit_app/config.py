import streamlit as st


AWS_REGION = st.secrets.get(
    "AWS_DEFAULT_REGION",
    "ap-south-1",
)

AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]

AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]

REDSHIFT_SECRET_ARN = st.secrets["REDSHIFT_SECRET_ARN"]


REDSHIFT_WORKGROUP = st.secrets.get(
    "REDSHIFT_WORKGROUP",
    "servicepulse-workgroup",
)

REDSHIFT_DATABASE = st.secrets.get(
    "REDSHIFT_DATABASE",
    "dev",
)

REDSHIFT_SCHEMA = st.secrets.get(
    "REDSHIFT_SCHEMA",
    "servicepulse",
)

REDSHIFT_TABLE = st.secrets.get(
    "REDSHIFT_TABLE",
    "fact_incidents",
)