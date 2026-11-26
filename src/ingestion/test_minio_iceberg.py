
import os
import warnings
from pathlib import Path

import pyarrow as pa
import pyiceberg.avro.decoder as decoder
import pyiceberg.avro.file as avro_file
from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    NestedField, LongType, StringType
)

# Windows Avro fallback
original = decoder.new_decoder

def safe_decoder(data):
    try:
        return original(data)
    except ImportError as error:
        if "decoder_fast" not in str(error):
            raise
        warnings.warn("Using pure-Python Avro decoder")
        return decoder.StreamingBinaryDecoder(data)

avro_file.new_decoder = safe_decoder

# Credentials
access = "medicare_admin"
secret = os.environ["MINIO_SECRET_KEY"]
endpoint = "http://localhost:9000"

# Persistent SQLite catalog, MinIO warehouse
catalog = load_catalog(
    "minio_test",
    **{
        "type": "sql",
        "uri": "sqlite:///data/iceberg/catalogs/minio_test.db",
        "warehouse": "s3://medicare-lakehouse/warehouse",
        "s3.endpoint": endpoint,
        "s3.access-key-id": access,
        "s3.secret-access-key": secret,
        "s3.region": "us-east-1",
        "s3.path-style-access": "true",
    }
)

namespace = "medicare_test"

try:
    catalog.create_namespace(namespace)
except Exception:
    pass

schema = Schema(
    NestedField(1, "record_id", LongType(), required=True),
    NestedField(2, "drug_name", StringType(), required=True),
)

try:
    catalog.drop_table((namespace, "connection_test"))
except Exception:
    pass

table = catalog.create_table(
    identifier=(namespace, "connection_test"),
    schema=schema,
)

data = pa.Table.from_pylist(
    [
        {"record_id": 1, "drug_name": "Eliquis"},
        {"record_id": 2, "drug_name": "Prednisone"},
    ],
    schema=pa.schema([
        pa.field("record_id", pa.int64(), nullable=False),
        pa.field("drug_name", pa.string(), nullable=False),
    ])
)

table.append(data)

result = table.scan().to_arrow()

assert len(result) == 2

print("PYICEBERG + MINIO SUCCESS")
print("Records:", len(result))
print("Location:", table.location())
