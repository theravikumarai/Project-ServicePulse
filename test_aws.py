import boto3
import streamlit as st


region = st.secrets["AWS_DEFAULT_REGION"]
secret_arn = st.secrets["REDSHIFT_SECRET_ARN"]

client = boto3.client(
    "secretsmanager",
    region_name=region,
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
)

response = client.get_secret_value(
    SecretId=secret_arn
)

st.success("Secret retrieval successful")

st.write("ARN from secrets.toml:")
st.code(secret_arn)

st.write("ARN returned by Secrets Manager:")
st.code(response["ARN"])

st.write("Secret name:")
st.code(response["Name"])