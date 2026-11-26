import requests

CATALOG_URL = "https://data.cms.gov/data.json"

print("Connecting to CMS catalogue...")

try:
    response = requests.get(
        CATALOG_URL,
        headers={"User-Agent": "MedicareLakehouse/1.0"},
        timeout=90
    )

    print("HTTP Status:", response.status_code)
    response.raise_for_status()

    catalog = response.json()

    print("Catalogue downloaded successfully!")
    print("Top-level keys:", list(catalog.keys()))

    target = "Medicare Part D Prescribers - by Provider and Drug"

    matches = [
        item for item in catalog.get("datasetSeries", [])
        if target.casefold() in item.get("title", "").casefold()
    ]

    print("\nMatching dataset series:", len(matches))

    for item in matches:
        print("\nTitle:", item.get("title"))
        print("Latest release:", item.get("last"))

except requests.exceptions.RequestException as error:
    print("CMS CONNECTION ERROR:", error)

except ValueError as error:
    print("JSON ERROR:", error)
