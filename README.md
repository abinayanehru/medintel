\# Medicare Part D Analytics | Prescription Cost \& Generic Optimization (2023)



An end-to-end healthcare analytics lakehouse built using Python, dlt, MinIO, Apache Iceberg, DuckDB, dbt Core, and Tableau Public.



\## Project Overview



This project analyzes the 2023 CMS Medicare Part D Prescribers by Provider and Drug dataset to understand prescription drug costs, brand-versus-generic patterns, and potential cost-optimization opportunities.



The solution implements a data lakehouse architecture that ingests a large healthcare dataset, stores it in Apache Iceberg format, transforms it using dbt, and presents analytical insights through an interactive Tableau dashboard.



\## Business Objectives



\- Compare reported prescription costs between brand and generic drug records.

\- Identify drugs with high reported prescription costs.

\- Analyze prescription costs across provider states and specialties.

\- Estimate potential cost-optimization opportunities using aggregate brand and generic cost comparisons.

\- Build a reproducible, end-to-end analytical pipeline.



\## Technology Stack



| Layer | Technology |

|---|---|

| Programming | Python |

| Data ingestion | dlt |

| Object storage | MinIO |

| Table format | Apache Iceberg |

| Table operations | PyIceberg |

| Query engine | DuckDB |

| Transformation | dbt Core |

| Visualization | Tableau Public |

| Containerization | Docker Engine, Docker Compose |

| Catalog | SQLite |

| Environment | Ubuntu on WSL2 |



\## Architecture



```mermaid

flowchart TD

&#x20;   A\["CMS Medicare Part D CSV"] --> B\["Python + dlt"]

&#x20;   B --> C\["MinIO Object Storage"]

&#x20;   C --> D\["Apache Iceberg Tables"]

&#x20;   D --> E\["DuckDB Query Engine"]

&#x20;   E --> F\["dbt Core Transformations"]

&#x20;   F --> G\["Analytical Mart Tables"]

&#x20;   G --> H\["CSV Exports"]

&#x20;   H --> I\["Tableau Public Dashboard"]

```



\## Dataset



\*\*Source:\*\* CMS Medicare Part D Prescribers by Provider and Drug, 2023.



| Attribute | Value |

|---|---:|

| Source records | 26,794,878 |

| Source columns | 22 |

| Extracted CSV size | Approximately 3.61 GB |

| ZIP archive size | Approximately 657.84 MB |

| Distinct generic drug names | 1,779 |



The dataset contains provider identifiers, provider specialties, states, drug brand names, generic names, claims, fills, days supplied, reported drug costs, and beneficiary-related fields.



\## Data Engineering Pipeline



\### 1. Ingestion



\- Used Python and dlt to process the CMS CSV.

\- Read the source in batches of 25,000 records.

\- Loaded the data into MinIO using an S3-compatible interface.

\- Stored the dataset in Apache Iceberg format.



\### 2. Storage



\- MinIO provides object storage.

\- Apache Iceberg manages the analytical table and snapshots.

\- SQLite is used for catalog metadata.



\### 3. Querying and Transformation



\- DuckDB reads the Iceberg table directly from MinIO.

\- dbt Core creates a staging view and analytical models.

\- SQL transformations standardize numeric fields, aggregate costs, and calculate analytical metrics.



\### 4. Analytical Models



| Model | Purpose |

|---|---|

| `stg\_prescriber\_drug` | Cleaned staging view |

| `mart\_drug\_cost\_analysis` | Brand/generic cost comparison |

| `mart\_provider\_analysis` | State and specialty analysis |

| `mart\_generic\_opportunities` | Estimated cost-optimization opportunities |



\## Dashboard



The Tableau Public dashboard contains four analytical views:



1\. \*\*Brand vs Generic Cost:\*\* Compares aggregate reported drug costs across the two classifications.

2\. \*\*Top 10 Drug Costs:\*\* Identifies drug names with the highest reported prescription costs.

3\. \*\*Provider Analysis:\*\* Compares reported costs across provider states and specialties.

4\. \*\*Generic Cost Optimization Opportunities:\*\* Ranks scenario-based cost-optimization estimates.



\## Implementation Metrics



| Metric | Measured result |

|---|---:|

| Records ingested | 26,794,878 |

| Ingestion batches | 1,072 |

| Ingestion duration | 129.37 minutes |

| Ingestion throughput | Approximately 3,452 records/sec |

| Iceberg data files | 1,072 Parquet files |

| MinIO objects | 5,366 |

| Total MinIO object size | Approximately 1.374 GB |

| Invalid numeric values found during profiling | 0 |

| dbt staging data tests passed | 4 |

| Analytical models created | 3 |



\## Data Quality and Analytical Considerations



\- Suppressed beneficiary values are preserved as NULL rather than treated as zero.

\- Numeric fields are converted using safe casting.

\- The staging model is validated using not-null tests for provider NPI, brand name, generic name, and total claims.

\- Brand/generic classification is based on normalized brand-name and generic-name equality.

\- Generic-name matching does not establish clinical interchangeability.

\- The source data is aggregated at provider-drug level, not individual patient transaction level.

\- Reported drug costs should not be interpreted as guaranteed Medicare savings or amounts paid exclusively by Medicare.

\- Generic cost-optimization figures are scenario-based estimates, not actual realized savings or clinical substitution recommendations.



\## Repository Structure



```text

Medicare-Lakehouse/

├── data/

│   ├── raw/

│   └── processed/

├── src/

│   ├── ingestion/

│   └── analysis/

├── dbt/

│   └── medicare\_analytics/

│       ├── models/

│       │   ├── staging/

│       │   └── marts/

│       └── dbt\_project.yml

├── dashboard/

│   └── data/

├── docs/

├── metrics/

├── logs/

└── README.md

```



\## Future Improvements



\- Add automated data-quality checks for analytical mart tables.

\- Improve brand/generic classification using more detailed drug attributes.

\- Add provider-level benchmarking with minimum sample-size thresholds.

\- Introduce incremental ingestion and automated pipeline scheduling.

\- Expand dashboard interactivity and drill-down analysis.



\## Disclaimer



This project is for educational and analytical purposes. The findings are descriptive and do not constitute medical advice, clinical substitution guidance, or verified financial savings.



\## Author



\*\*Abinaya N.\*\*



Healthcare Data Analytics | Data Engineering | SQL | Python | Tableau

