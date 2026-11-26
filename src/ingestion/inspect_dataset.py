import csv
from pathlib import Path

file_path = Path("data/raw/2023/Medicare_Part_D_2023.csv")

print("Inspecting Medicare Part D dataset...")
print("File size:", round(file_path.stat().st_size / (1024**3), 2), "GB")

with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
    reader = csv.reader(file)

    headers = next(reader)

    print("\nTOTAL COLUMNS:", len(headers))

    print("\nCOLUMN NAMES:")
    for number, column in enumerate(headers, start=1):
        print(f"{number}. {column}")

    print("\nFIRST 5 RECORDS:")

    for row_number, row in enumerate(reader, start=1):
        print(f"\nRECORD {row_number}:")

        for column, value in zip(headers, row):
            print(f"  {column}: {value[:100]}")

        if row_number == 5:
            break

print("\nInspection completed!")
