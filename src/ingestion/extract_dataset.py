import zipfile
import shutil
from pathlib import Path

zip_path = Path("data/raw/Medicare_Part_D_2023.zip")

member = (
    "Medicare Part D Prescribers - by Provider and Drug/"
    "2023/MUP_DPR_RY25_P04_V10_DY23_NPIBN.csv"
)

output_dir = Path("data/raw/2023")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "Medicare_Part_D_2023.csv"

print("Starting extraction...")

with zipfile.ZipFile(zip_path, "r") as archive:
    with archive.open(member) as source:
        with open(output_file, "wb") as destination:
            shutil.copyfileobj(source, destination, length=8 * 1024 * 1024)

print("Extraction completed!")
print("Extracted file:", output_file)
print("Size (MB):", round(output_file.stat().st_size / (1024 * 1024), 2))
