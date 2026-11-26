
# MedIntel — dbt Analytics

This dbt project transforms the 2023 CMS Medicare Part D Prescribers by Provider and Drug Iceberg dataset into analytical models for healthcare prescription cost analysis.

## Project Structure

```text
medicare_analytics/
├── models/
│   ├── staging/
│   │   ├── stg_prescriber_drug.sql
│   │   └── schema.yml
│   └── marts/
│       ├── mart_drug_cost_analysis.sql
│       ├── mart_provider_analysis.sql
│       ├── mart_generic_opportunities.sql
│       └── schema.yml
├── export_marts.py
├── dbt_project.yml
└── README.md
```

## Data Models

| Model | Materialization | Purpose |
|---|---|---|
| stg_prescriber_drug | View | Standardizes source fields and safely casts numeric values |
| mart_drug_cost_analysis | Table | Compares reported costs and utilization |
| mart_provider_analysis | Table | Aggregates costs by provider state and specialty |
| mart_generic_opportunities | Table | Builds threshold-filtered cost comparison scenarios |

## Data Source

The staging model reads the Iceberg table through DuckDB's `iceberg_scan()` function.

Set the environment variable:

`MEDICARE_ICEBERG_METADATA_PATH`

It must point to the Iceberg table's metadata JSON file in the local MinIO-backed storage environment.

## Configuration

The project uses the `medicare_analytics` dbt profile.

The profile must configure:

- DuckDB as the adapter.
- The local DuckDB database.
- S3-compatible MinIO access.
- Iceberg metadata access.

Keep credentials and machine-specific configuration outside the public repository.

## Running the Models

Activate the analytics Python environment and navigate to this directory.

```bash
dbt debug
dbt run
dbt test
```

Run only the generic opportunity model after changing its SQL:

```bash
dbt run --select mart_generic_opportunities
dbt test --select mart_generic_opportunities
```

## Exporting Analytical Marts

After successful model execution:

```bash
python export_marts.py
```

The script exports all three analytical marts to:

`dashboard/data/`

The exported CSV files are used by the Tableau Public dashboard.

## Analytical Methodology

The generic opportunity model:

1. Classifies source records using case-insensitive brand-name and generic-name equality.
2. Aggregates claims and reported drug costs by generic drug name.
3. Requires at least 1,000 claims in both classifications.
4. Calculates reported cost per claim for each classification.
5. Calculates a scenario estimate using the positive difference between the two costs multiplied by brand claims.

The threshold is an analyst-defined screening rule. It does not establish statistical significance, clinical interchangeability, or actual savings.

The source does not provide sufficient strength, dosage-form, and route information to establish clinical equivalence.

## Important Interpretation

The model produces exploratory cost-comparison scenarios, not medical recommendations or verified financial savings.

The source dataset is aggregated at provider-drug level and does not represent individual patient transactions.
