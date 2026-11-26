import requests
import json
from pathlib import Path

DATASET_VERSION_ID = "d5aa71a8-dcc0-4570-8bcf-bd39deac69fe"

URL = (
    "https://data.cms.gov/data-api/v1/"
    f"dataset/{DATASET_VERSION_ID}/data"
)

params = {
    "size": 100,
    "offset": 0
}

print("Connecting to CMS API...")

response = requests.get(
    URL,
    params=params,
    timeout=60
)

response.raise_for_status()

payload = response.json()

if isinstance(payload, list):
    rows = payload
elif isinstance(payload, dict):
    rows = (
        payload.get("data")
        or payload.get("results")
        or payload.get("rows")
    )
else:
    raise ValueError("Unexpected CMS API response format")

if not isinstance(rows, list):
    raise ValueError(
        f"Could not identify records. Response keys: "
        f"{list(payload.keys()) if isinstance(payload, dict) else 'N/A'}"
    )

output = Path("data/raw/cms_api_sample_100.json")
output.parent.mkdir(parents=True, exist_ok=True)

with output.open("w", encoding="utf-8") as file:
    json.dump(rows, file, indent=2)

print("\nCMS API CONNECTION SUCCESSFUL")
print("HTTP status:", response.status_code)
print("Records retrieved:", len(rows))
print("Columns:", len(rows[0]) if rows else 0)
print("Sample columns:", list(rows[0].keys()) if rows else [])
print("Saved to:", output)
