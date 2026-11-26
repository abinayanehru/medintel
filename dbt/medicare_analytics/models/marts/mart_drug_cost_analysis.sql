{{ config(materialized='table') }}

SELECT
    gnrc_name AS generic_drug_name,

    CASE
        WHEN LOWER(TRIM(brnd_name)) = LOWER(TRIM(gnrc_name))
            THEN 'Generic'
        ELSE 'Brand'
    END AS drug_type,

    COUNT(*) AS provider_drug_records,
    COUNT(DISTINCT prscrbr_npi) AS unique_providers,

    SUM(total_claims) AS total_claims,
    SUM(total_30day_fills) AS total_30day_fills,
    SUM(total_day_supply) AS total_day_supply,
    SUM(total_drug_cost) AS total_drug_cost,

    SUM(total_drug_cost) / NULLIF(SUM(total_claims), 0)
        AS cost_per_claim,

    SUM(total_drug_cost) / NULLIF(SUM(total_30day_fills), 0)
        AS cost_per_30day_fill

FROM {{ ref('stg_prescriber_drug') }}

WHERE
    gnrc_name IS NOT NULL
    AND brnd_name IS NOT NULL
    AND total_claims > 0
    AND total_drug_cost IS NOT NULL

GROUP BY
    gnrc_name,
    CASE
        WHEN LOWER(TRIM(brnd_name)) = LOWER(TRIM(gnrc_name))
            THEN 'Generic'
        ELSE 'Brand'
    END
