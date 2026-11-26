import duckdb
from pathlib import Path

db = Path("medicare_analytics.duckdb")
output = Path("/mnt/d/DataAnalytics/Medicare-Lakehouse/dashboard/data")

con = duckdb.connect(str(db), read_only=True)

tables = [
    "mart_drug_cost_analysis",
    "mart_provider_analysis",
    "mart_generic_opportunities",
]

for table in tables:
    destination = output / f"{table}.csv"
    con.execute(
        f"COPY (SELECT * FROM {table}) TO '{destination}' "
        "(HEADER, DELIMITER ',')"
    )
    count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count:,} rows exported")

con.close()
print(f"\nExports saved to: {output}")
