import zipfile

path = "data/raw/Medicare_Part_D_2023.zip"

with zipfile.ZipFile(path, "r") as archive:
    files = archive.infolist()

    print("Number of files:", len(files))
    print("\nFiles inside ZIP:")

    for file in files:
        print(file.filename, "|",
              round(file.file_size / (1024 * 1024), 2), "MB")

    total_size = sum(f.file_size for f in files)

    print("\nTotal extracted size:",
          round(total_size / (1024 * 1024), 2), "MB")

    print("\nChecking archive integrity...")
    print("Integrity result:", archive.testzip())
