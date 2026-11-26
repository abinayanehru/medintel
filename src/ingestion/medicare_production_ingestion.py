
import os
import csv
import time
import warnings
from pathlib import Path

# --------------------------------------------------
# 1. PATHS AND SETTINGS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

SOURCE = ROOT / "data/raw/2023/Medicare_Part_D_2023.csv"
BATCH_SIZE = 25_000

BUCKET = "medicare-lakehouse"
ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "medicare_admin"
SECRET_KEY = os.environ["MINIO_SECRET_KEY"]

CATALOG_DIR = ROOT / "data/iceberg/catalogs"
CATALOG_DIR.mkdir(parents=True, exist_ok=True)

CATALOG_DB = CATALOG_DIR / "medicare_production_v2.db"

PIPELINE_NAME = "medicare_2023_production_v2"
DATASET_NAME = "medicare_2023"
TABLE_NAME = "prescriber_drug"

# Keep all dlt working files on D:
PIPELINES_DIR = ROOT / "dlt_state"
PIPELINES_DIR.mkdir(parents=True, exist_ok=True)

if not SOURCE.exists():
    raise FileNotFoundError(f"Source CSV not found: {SOURCE}")

# --------------------------------------------------
# 2. ICEBERG CATALOG CONFIGURATION
# --------------------------------------------------

os.environ["ICEBERG_CATALOG__ICEBERG_CATALOG_NAME"] = "medicare_production"
os.environ["ICEBERG_CATALOG__ICEBERG_CATALOG_TYPE"] = "sql"

prefix = "DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__"

os.environ[prefix + "TYPE"] = "sql"
os.environ[prefix + "URI"] = (
    "sqlite:///" + CATALOG_DB.resolve().as_posix()
)
os.environ[prefix + "WAREHOUSE"] = f"s3://{BUCKET}/warehouse"
os.environ[prefix + "S3_ENDPOINT"] = ENDPOINT
os.environ[prefix + "S3_ACCESS_KEY_ID"] = ACCESS_KEY
os.environ[prefix + "S3_SECRET_ACCESS_KEY"] = SECRET_KEY
os.environ[prefix + "S3_REGION"] = "us-east-1"
os.environ[prefix + "S3_PATH_STYLE_ACCESS"] = "true"

# --------------------------------------------------
# 3. PYICEBERG AVRO FALLBACK
# --------------------------------------------------

import pyiceberg.avro.decoder as avro_decoder
import pyiceberg.avro.file as avro_file

original_decoder = avro_decoder.new_decoder

def safe_decoder(data):
    try:
        return original_decoder(data)
    except ImportError as error:
        if "decoder_fast" not in str(error):
            raise
        warnings.warn("Using pure-Python Avro decoder")
        return avro_decoder.StreamingBinaryDecoder(data)

avro_file.new_decoder = safe_decoder

# --------------------------------------------------
# 4. IMPORT DLT
# --------------------------------------------------

import dlt

# --------------------------------------------------
# 5. READ AND VALIDATE CSV SCHEMA
# --------------------------------------------------

with open(SOURCE, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    source_columns = reader.fieldnames

if not source_columns or len(source_columns) != 22:
    raise ValueError(
        f"Unexpected CMS schema. Expected 22 columns, "
        f"found {len(source_columns) if source_columns else 0}"
    )

column_schema = {
    col: {"data_type": "text", "nullable": True}
    for col in source_columns
}

# --------------------------------------------------
# 6. MINIO DESTINATION
# --------------------------------------------------

destination = dlt.destinations.filesystem(
    bucket_url=f"s3://{BUCKET}/dlt",
    credentials={
        "aws_access_key_id": ACCESS_KEY,
        "aws_secret_access_key": SECRET_KEY,
        "endpoint_url": ENDPOINT,
        "region_name": "us-east-1",
    },
)

# --------------------------------------------------
# 7. CREATE PIPELINE ON D:
# --------------------------------------------------

pipeline = dlt.pipeline(
    pipeline_name=PIPELINE_NAME,
    pipelines_dir=str(PIPELINES_DIR),
    destination=destination,
    dataset_name=DATASET_NAME,
)

# --------------------------------------------------
# 8. BATCH-BY-BATCH PRODUCTION INGESTION
# --------------------------------------------------

print("=" * 55)
print("MEDICARE PART D - PRODUCTION INGESTION")
print("=" * 55)
print("Source:", SOURCE)
print("Batch size:", f"{BATCH_SIZE:,}")
print("Destination: MinIO + Apache Iceberg")
print("Pipeline:", PIPELINE_NAME)
print("Pipeline state:", PIPELINES_DIR)
print("=" * 55)

start = time.perf_counter()

total_rows = 0
batch_number = 0

with open(SOURCE, "r", encoding="utf-8-sig", newline="") as f:

    reader = csv.DictReader(f)
    batch = []

    for row in reader:

        record = {
            col: (row.get(col) if row.get(col) != "" else None)
            for col in source_columns
        }

        batch.append(record)

        if len(batch) >= BATCH_SIZE:

            batch_number += 1

            # First batch creates/replaces the table.
            # Every following batch appends to it.
            disposition = "replace" if batch_number == 1 else "append"

            load_info = pipeline.run(
                batch,
                table_name=TABLE_NAME,
                write_disposition=disposition,
                columns=column_schema,
                table_format="iceberg",
            )

            total_rows += len(batch)

            elapsed = time.perf_counter() - start

            print(
                f"Batch {batch_number:,} | "
                f"Rows loaded: {total_rows:,} | "
                f"Batch rows: {len(batch):,} | "
                f"Elapsed: {elapsed / 60:.2f} minutes"
            )

            batch = []

    # Load the final incomplete batch.
    if batch:

        batch_number += 1

        disposition = "replace" if batch_number == 1 else "append"

        load_info = pipeline.run(
            batch,
            table_name=TABLE_NAME,
            write_disposition=disposition,
            columns=column_schema,
            table_format="iceberg",
        )

        total_rows += len(batch)

        elapsed = time.perf_counter() - start

        print(
            f"Batch {batch_number:,} | "
            f"Rows loaded: {total_rows:,} | "
            f"Final batch: {len(batch):,}"
        )

# --------------------------------------------------
# 9. FINAL RESULTS
# --------------------------------------------------

elapsed = time.perf_counter() - start

print("\n" + "=" * 55)
print("INGESTION RESULTS")
print("=" * 55)

print("Total rows loaded:", f"{total_rows:,}")
print("Source columns:", len(source_columns))
print("Expected columns including dlt metadata:", len(source_columns) + 2)
print("Total batches:", f"{batch_number:,}")
print("Duration:", round(elapsed / 60, 2), "minutes")
print(
    "Average throughput:",
    f"{total_rows / elapsed:,.2f} rows/second"
)
print("Pipeline:", PIPELINE_NAME)
print("Dataset:", DATASET_NAME)
print("Table:", TABLE_NAME)
print("Storage: MinIO + Apache Iceberg")

print("\nPRODUCTION INGESTION FINISHED")
print("Verify the Iceberg table before marking the load successful.")
