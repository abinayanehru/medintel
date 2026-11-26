
import os
import csv
import time
import warnings
from pathlib import Path

# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

ROOT = Path.cwd()

SOURCE = ROOT / "data/raw/2023/Medicare_Part_D_2023.csv"
WAREHOUSE = ROOT / "data/iceberg/dlt_bronze_test"
CATALOG_DIR = ROOT / "data/iceberg/catalogs"
CATALOG_DB = CATALOG_DIR / "medicare_dlt_test.db"

DATASET_NAME = "medicare_2023_sample"
TABLE_NAME = "prescriber_drug"

WAREHOUSE.mkdir(parents=True, exist_ok=True)
CATALOG_DIR.mkdir(parents=True, exist_ok=True)




# --------------------------------------------------
# 2. CONFIGURE ICEBERG CATALOG + MINIO
# --------------------------------------------------

MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "medicare_admin"
MINIO_SECRET_KEY = os.environ["MINIO_SECRET_KEY"]
BUCKET = "medicare-lakehouse"

os.environ["ICEBERG_CATALOG__ICEBERG_CATALOG_NAME"] = "medicare_local"
os.environ["ICEBERG_CATALOG__ICEBERG_CATALOG_TYPE"] = "sql"

os.environ["DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__TYPE"] = "sql"
os.environ["DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__URI"] = (
    "sqlite:///" + CATALOG_DB.resolve().as_posix()
)

os.environ["DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__WAREHOUSE"] = (
    f"s3://{BUCKET}/warehouse"
)

os.environ["DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__S3_ENDPOINT"] = MINIO_ENDPOINT
os.environ["DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__S3_ACCESS_KEY_ID"] = MINIO_ACCESS_KEY
os.environ["DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__S3_SECRET_ACCESS_KEY"] = MINIO_SECRET_KEY
os.environ["DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__S3_REGION"] = "us-east-1"
os.environ["DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__S3_FORCE_VIRTUAL_ADDRESSING"] = "false"



# --------------------------------------------------
# 3. PYICEBERG PURE-PYTHON AVRO FALLBACK
# IMPORTANT: APPLY BEFORE DLT INGESTION
# --------------------------------------------------

import pyiceberg.avro.decoder as avro_decoder
import pyiceberg.avro.file as avro_file

original_decoder = avro_decoder.new_decoder

def safe_new_decoder(data):
    try:
        return original_decoder(data)

    except ImportError as error:

        if "decoder_fast" not in str(error):
            raise

        warnings.warn(
            "Compiled Avro decoder blocked by Windows Application Control. "
            "Using pure-Python decoder."
        )

        return avro_decoder.StreamingBinaryDecoder(data)


avro_file.new_decoder = safe_new_decoder

print("PyIceberg pure-Python fallback configured.")


# --------------------------------------------------
# 4. IMPORT DLT AND CATALOG
# --------------------------------------------------

import dlt
from dlt.common.libs.pyiceberg import get_iceberg_tables
from pyiceberg.catalog import load_catalog

if not SOURCE.exists():
    raise FileNotFoundError(f"Source CSV not found: {SOURCE}")


# --------------------------------------------------
# 5. READ SOURCE COLUMN STRUCTURE
# --------------------------------------------------

with open(SOURCE, "r", encoding="utf-8-sig", newline="") as file:

    reader = csv.DictReader(file)
    source_columns = reader.fieldnames

if not source_columns or len(source_columns) != 22:
    raise ValueError("Unexpected source CSV structure")

column_schema = {
    column: {"data_type": "text", "nullable": True}
    for column in source_columns
}


# --------------------------------------------------
# 6. DEFINE DLT RESOURCE
# --------------------------------------------------

@dlt.resource(
    name=TABLE_NAME,
    columns=column_schema,
    write_disposition="replace"
)

def medicare_sample():

    with open(SOURCE, "r", encoding="utf-8-sig", newline="") as file:

        reader = csv.DictReader(file)
        batch = []

        for index, row in enumerate(reader):

            if index >= 1000:
                break

            batch.append({
                column: (
                    row.get(column)
                    if row.get(column) is not None
                    else ""
                )
                for column in source_columns
            })

        print("Source records prepared:", len(batch))

        yield batch


# --------------------------------------------------
# 7. CONFIGURE DLT PIPELINE
# --------------------------------------------------

print("\nStarting dlt Medicare sample ingestion...")

destination = dlt.destinations.filesystem(
    bucket_url=f"s3://{BUCKET}/dlt",
    credentials={
        "aws_access_key_id": MINIO_ACCESS_KEY,
        "aws_secret_access_key": MINIO_SECRET_KEY,
        "endpoint_url": MINIO_ENDPOINT,
        "region_name": "us-east-1",
    },
)
pipeline = dlt.pipeline(
    pipeline_name="medicare_iceberg_sample",
    destination=destination,
    dataset_name=DATASET_NAME
)


# --------------------------------------------------
# 8. RUN INGESTION
# --------------------------------------------------

start_time = time.perf_counter()

load_info = pipeline.run(
    medicare_sample,
    table_format="iceberg"
)

elapsed = time.perf_counter() - start_time

print("\nDLT LOAD RESULT:")
print(load_info)



# --------------------------------------------------
# 9. VERIFY ICEBERG TABLE THROUGH DLT
# --------------------------------------------------

tables = get_iceberg_tables(pipeline)

print("\nICEBERG TABLES FOUND:", list(tables.keys()))

if TABLE_NAME not in tables:
    raise RuntimeError("Expected Iceberg table was not found!")

table = tables[TABLE_NAME]



# --------------------------------------------------
# 10. VERIFY INGESTED DATA
# --------------------------------------------------

result = table.scan().to_arrow()

print("\nVERIFICATION:")
print("Records written:", len(result))
print("Expected records: 1000")
print("Original source columns:", len(source_columns))
print("Total Iceberg columns:", len(result.column_names))
print("Ingestion duration (seconds):", round(elapsed, 2))
print("Warehouse:", WAREHOUSE)

# dlt normalizes CMS column names to lowercase.
expected_columns = {column.lower() for column in source_columns}
actual_columns = set(result.column_names)

missing_columns = expected_columns - actual_columns

if missing_columns:
    raise AssertionError(
        f"Missing source columns after normalization: {missing_columns}"
    )

# Confirm dlt metadata columns are present.
expected_metadata = {"_dlt_load_id", "_dlt_id"}
missing_metadata = expected_metadata - actual_columns

if missing_metadata:
    raise AssertionError(
        f"Missing dlt metadata columns: {missing_metadata}"
    )

assert len(result) == 1000, "Record count mismatch!"
assert len(expected_columns) == 22, "Expected 22 source columns!"
assert len(actual_columns) == 24, "Expected 24 total columns!"

print("\nSUCCESS: 1000 Medicare records ingested and verified in Iceberg!")

