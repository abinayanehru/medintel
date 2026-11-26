
from pathlib import Path

import duckdb


PROJECT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PROJECT_DIR.parents[1]
DATABASE_PATH = PROJECT_DIR / "medicare_analytics.duckdb"
OUTPUT_DIR = REPOSITORY_ROOT / "dashboard" / "data"

TABLES = (
    "mart_drug_cost_analysis",
    "mart_provider_analysis",
    "mart_generic_opportunities",
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(DATABASE_PATH), read_only=True) as connection:
        for table in TABLES:
            destination = (OUTPUT_DIR / f"{table}.csv").as_posix()
            safe_destination = destination.replace("'", "''")

            connection.execute(
                f"COPY (SELECT * FROM {table}) "
                f"TO '{safe_destination}' (HEADER, DELIMITER ',')"
            )

            row_count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"{table}: {row_count:,} rows exported")

    print(f"\nExports saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
