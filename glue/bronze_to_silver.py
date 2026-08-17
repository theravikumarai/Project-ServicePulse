import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions

from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, ArrayType
from pyspark.sql.window import Window


# ============================================================
# Job arguments
# ============================================================

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "SOURCE_PATH",
        "TARGET_PATH",
    ],
)


# ============================================================
# Spark / Glue initialization
# ============================================================

sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

job = Job(glue_context)

job.init(
    args["JOB_NAME"],
    args,
)


source_path = args["SOURCE_PATH"]
target_path = args["TARGET_PATH"]

print(f"Source path: {source_path}")
print(f"Target path: {target_path}")


# ============================================================
# Read Bronze JSON
# ============================================================

df = (
    spark.read
    .option("multiLine", "true")
    .json(source_path)
)

print("Original Bronze schema:")
df.printSchema()


# ============================================================
# Flatten ServiceNow records
# ============================================================

metadata_column = None


# ------------------------------------------------------------
# Case 1: ServiceNow-style "result" array
# ------------------------------------------------------------

if "result" in df.columns:

    result_type = df.schema["result"].dataType

    if isinstance(result_type, ArrayType):

        if "_metadata" in df.columns:

            df = (
                df
                .select(
                    F.explode("result").alias("record"),
                    "_metadata",
                )
                .select(
                    "record.*",
                    "_metadata",
                )
            )

        else:

            df = (
                df
                .select(
                    F.explode("result").alias("record")
                )
                .select("record.*")
            )


# ------------------------------------------------------------
# Case 2: Our Bronze format uses "records"
# ------------------------------------------------------------

elif "records" in df.columns:

    records_type = df.schema["records"].dataType

    if isinstance(records_type, ArrayType):

        if "_metadata" in df.columns:

            df = (
                df
                .select(
                    F.explode("records").alias("record"),
                    "_metadata",
                )
                .select(
                    "record.*",
                    "_metadata",
                )
            )

        else:

            df = (
                df
                .select(
                    F.explode("records").alias("record")
                )
                .select("record.*")
            )

    else:

        raise ValueError(
            "'records' exists but is not an array."
        )


else:

    raise ValueError(
        "Bronze JSON does not contain "
        "'result' or 'records'."
    )


print("Flattened schema:")
df.printSchema()


# ============================================================
# Convert empty strings to NULL
# Only STRING columns
# ============================================================

string_columns = [
    field.name
    for field in df.schema.fields
    if isinstance(field.dataType, StringType)
]


for column in string_columns:

    df = df.withColumn(
        column,
        F.when(
            F.trim(F.col(column)) == "",
            None,
        ).otherwise(F.col(column))
    )


# ============================================================
# Convert numeric fields
# ============================================================

integer_columns = [
    "state",
    "priority",
    "urgency",
    "impact",
]


for column in integer_columns:

    if column in df.columns:

        df = df.withColumn(
            column,
            F.col(column).cast("integer")
        )


# ============================================================
# Convert timestamps
# ============================================================

timestamp_columns = [
    "sys_created_on",
    "sys_updated_on",
]


for column in timestamp_columns:

    if column in df.columns:

        df = df.withColumn(
            column,
            F.to_timestamp(
                F.col(column),
                "yyyy-MM-dd HH:mm:ss"
            )
        )


# ============================================================
# Validate required column
# ============================================================

if "sys_id" not in df.columns:

    raise ValueError(
        "sys_id is missing after flattening Bronze records."
    )


# ============================================================
# Remove invalid records
# ============================================================

df = df.filter(
    F.col("sys_id").isNotNull()
)


# ============================================================
# Deduplicate incidents
#
# Keep latest version of each incident.
# ============================================================

window_spec = (
    Window
    .partitionBy("sys_id")
    .orderBy(
        F.col("sys_updated_on")
        .desc_nulls_last()
    )
)


df = (
    df
    .withColumn(
        "_row_number",
        F.row_number().over(window_spec)
    )
    .filter(
        F.col("_row_number") == 1
    )
    .drop("_row_number")
)


# ============================================================
# Create Silver partitions
# ============================================================

df = (
    df
    .withColumn(
        "year",
        F.year("sys_updated_on")
    )
    .withColumn(
        "month",
        F.month("sys_updated_on")
    )
    .withColumn(
        "day",
        F.dayofmonth("sys_updated_on")
    )
)


# ============================================================
# Validate final schema
# ============================================================

print("Final Silver schema:")
df.printSchema()


record_count = df.count()

print(
    f"Records to write: {record_count}"
)


# ============================================================
# Write Silver Parquet
# ============================================================

(
    df
    .write
    .mode("append")
    .partitionBy(
        "year",
        "month",
        "day"
    )
    .parquet(target_path)
)


print(
    "Silver transformation completed successfully."
)

print(
    f"Records written: {record_count}"
)


# ============================================================
# Complete Glue job
# ============================================================

job.commit()