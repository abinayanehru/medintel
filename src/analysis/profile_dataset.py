import csv
import json
from pathlib import Path
from collections import Counter

source = Path("data/raw/2023/Medicare_Part_D_2023.csv")
output = Path("reports/data_quality_profile.json")

numeric_columns = [
    "Tot_Clms",
    "Tot_30day_Fills",
    "Tot_Day_Suply",
    "Tot_Drug_Cst",
    "Tot_Benes",
    "GE65_Tot_Clms",
    "GE65_Tot_30day_Fills",
    "GE65_Tot_Drug_Cst",
    "GE65_Tot_Day_Suply",
    "GE65_Tot_Benes"
]

flag_columns = [
    "GE65_Sprsn_Flag",
    "GE65_Bene_Sprsn_Flag"
]

profile = {
    "file": str(source),
    "file_size_bytes": source.stat().st_size,
    "total_records": 0,
    "missing_values": {},
    "numeric_statistics": {},
    "flag_distributions": {},
    "brand_generic_comparison": {
        "same_name": 0,
        "different_name": 0,
        "missing_name": 0
    },
    "distinct_generic_names": 0
}

missing = Counter()
flags = {col: Counter() for col in flag_columns}
numeric = {
    col: {"valid": 0, "invalid": 0, "min": None, "max": None}
    for col in numeric_columns
}

generic_names = set()
row_count = 0

print("Starting full dataset profiling...")
print("This may take several minutes.")

with open(source, "r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        row_count += 1

        for col, value in row.items():
            if value is None or value.strip() == "":
                missing[col] += 1

        brand = (row.get("Brnd_Name") or "").strip().casefold()
        generic = (row.get("Gnrc_Name") or "").strip().casefold()

        if not brand or not generic:
            profile["brand_generic_comparison"]["missing_name"] += 1
        elif brand == generic:
            profile["brand_generic_comparison"]["same_name"] += 1
        else:
            profile["brand_generic_comparison"]["different_name"] += 1

        if generic:
            generic_names.add(generic)

        for col in numeric_columns:
            value = (row.get(col) or "").strip()

            if not value:
                continue

            try:
                number = float(value)
                stats = numeric[col]
                stats["valid"] += 1

                if stats["min"] is None or number < stats["min"]:
                    stats["min"] = number

                if stats["max"] is None or number > stats["max"]:
                    stats["max"] = number

            except ValueError:
                numeric[col]["invalid"] += 1

        for col in flag_columns:
            value = (row.get(col) or "").strip()
            flags[col][value if value else "<BLANK>"] += 1

        if row_count % 1000000 == 0:
            print(f"Processed {row_count:,} records...")

profile["total_records"] = row_count
profile["missing_values"] = dict(missing)
profile["numeric_statistics"] = numeric
profile["flag_distributions"] = {
    col: dict(counter) for col, counter in flags.items()
}
profile["distinct_generic_names"] = len(generic_names)

output.parent.mkdir(parents=True, exist_ok=True)

with open(output, "w", encoding="utf-8") as file:
    json.dump(profile, file, indent=4)

print("\n========== PROFILING RESULTS ==========")
print("Total records:", f"{row_count:,}")

print("\nMISSING VALUES:")
for col, count in missing.most_common():
    print(f"{col}: {count:,}")

print("\nNUMERIC STATISTICS:")
for col, stats in numeric.items():
    print(col, stats)

print("\nBRAND-GENERIC NAME COMPARISON:")
print(profile["brand_generic_comparison"])

print("\nDISTINCT GENERIC DRUG NAMES:",
      profile["distinct_generic_names"])

print("\nSUPPRESSION FLAGS:")
for col, distribution in profile["flag_distributions"].items():
    print(col, distribution)

print("\nReport saved to:", output)
print("Profiling completed!")
