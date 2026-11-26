from pathlib import Path
import pyarrow as pa
import sqlalchemy

from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, LongType, StringType

print("Starting PyIceberg integration test...")

# Create an isolated test directory
base = Path("data/iceberg/smoke_test")
base.mkdir(parents=True, exist_ok=True)

warehouse = base / "warehouse"
warehouse.mkdir(parents=True, exist_ok=True)

# Configure a persistent local SQLite catalog
catalog = load_catalog(
    "medicare_local",
    type="sql",
    uri="sqlite:///data/iceberg/smoke_test/catalog.db",
    warehouse=f"file://{warehouse.resolve().as_posix()}"
)

print("SQLite catalog connected!")
print("SQLAlchemy version:", sqlalchemy.__version__)

# Create a test namespace
namespace = ("medicare_test",)

if namespace not in catalog.list_namespaces():
    catalog.create_namespace(namespace)

# Remove only our previous test table, if it exists
identifier = ("medicare_test", "connectivity_check")

if identifier in catalog.list_tables(namespace):
    catalog.drop_table(identifier)

# Define the Iceberg schema
schema = Schema(
    NestedField(
        field_id=1,
        name="record_id",
        field_type=LongType(),
        required=True
    ),
    NestedField(
        field_id=2,
        name="drug_name",
        field_type=StringType(),
        required=True
    ),
    NestedField(
        field_id=3,
        name="generic_name",
        field_type=StringType(),
        required=True
    ),
    NestedField(
        field_id=4,
        name="total_claims",
        field_type=LongType(),
        required=True
    )
)

# Create the Iceberg table
table = catalog.create_table(
    identifier=identifier,
    schema=schema
)

print("Iceberg table created!")

# Prepare three sample records using PyArrow
sample_schema = pa.schema([
    pa.field("record_id", pa.int64(), nullable=False),
    pa.field("drug_name", pa.string(), nullable=False),
    pa.field("generic_name", pa.string(), nullable=False),
    pa.field("total_claims", pa.int64(), nullable=False)
])

sample_data = pa.Table.from_arrays(
    [
        pa.array([1, 2, 3], type=pa.int64()),
        pa.array(["Eliquis", "Prednisone", "Baclofen"]),
        pa.array(["Apixaban", "Prednisone", "Baclofen"]),
        pa.array([13, 14, 55], type=pa.int64())
    ],
    schema=sample_schema
)
# Write records
table.append(sample_data)

print("Three records written!")

# Read the records back
# Work around Windows Application Control blocking
# PyIceberg's optional compiled Avro decoder.

import warnings
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
            "Compiled Avro decoder blocked. "
            "Using pure-Python decoder instead."
        )

        return avro_decoder.StreamingBinaryDecoder(data)

# avro.file uses an imported reference to new_decoder,
# so replace that reference for this test.
avro_file.new_decoder = safe_new_decoder

print("Using PyIceberg pure-Python Avro decoder...")

result = table.scan().to_arrow()

actual = sorted(
    result.to_pylist(),
    key=lambda row: row["record_id"]
)

expected = [
    {"record_id": 1, "drug_name": "Eliquis",
     "generic_name": "Apixaban", "total_claims": 13},
    {"record_id": 2, "drug_name": "Prednisone",
     "generic_name": "Prednisone", "total_claims": 14},
    {"record_id": 3, "drug_name": "Baclofen",
     "generic_name": "Baclofen", "total_claims": 55}
]

assert actual == expected, "Data verification failed!"

print("\nREAD-BACK RESULTS:")
for row in actual:
    print(row)

print("\nRecords verified:", len(actual))
print("Catalog location:", base / "catalog.db")
print("Warehouse location:", warehouse)

print("\nSUCCESS: PyIceberg + SQLite + PyArrow working!")

