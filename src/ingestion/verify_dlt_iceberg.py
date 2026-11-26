
import os
import warnings
from pathlib import Path

ROOT = Path.cwd()
WAREHOUSE = ROOT / "data/iceberg/dlt_bronze_test"
CATALOG_DB = ROOT / "data/iceberg/catalogs/medicare_dlt_test.db"

# Same catalog configuration as ingestion
os.environ["ICEBERG_CATALOG__ICEBERG_CATALOG_NAME"] = "medicare_local"
os.environ["ICEBERG_CATALOG__ICEBERG_CATALOG_TYPE"] = "sql"

os.environ["DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__TYPE"] = "sql"
os.environ["DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__URI"] = (
    "sqlite:///" + CATALOG_DB.resolve().as_posix()
)
os.environ["DLT_ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__WAREHOUSE"] = (
    "file://" + WAREHOUSE.resolve().as_posix()
)

# Windows pure-Python Avro fallback
import pyiceberg.avro.decoder as avro_decoder
import pyiceberg.avro.file as avro_file

original_decoder = avro_decoder.new_decoder

def safe_new_decoder(data):
    try:
        return original_decoder(data)
    except ImportError as error:
        if "decoder_fast" not in str(error):
            raise
        warnings.warn("Using pure-Python Avro decoder")
        return avro_decoder.StreamingBinaryDecoder(data)

avro_file.new_decoder = safe_new_decoder

import dlt
from dlt.common.libs.pyiceberg import get_iceberg_tables

destination = dlt.destinations.filesystem(
    bucket_url=str(WAREHOUSE.resolve())
)

pipeline = dlt.pipeline(
    pipeline_name="medicare_iceberg_sample",
    destination=destination,
    dataset_name="medicare_2023_sample"
)

print("Checking Iceberg tables through dlt...")

tables = get_iceberg_tables(pipeline)

print("Tables found:", list(tables.keys()))

for name, table in tables.items():
    print("\nTable:", name)
    result = table.scan().to_arrow()
    print("Records:", len(result))
    print("Columns:", len(result.column_names))
    print("Column names:", result.column_names)
