{{ config(materialized='table') }}

SELECT
    prscrbr_state_abrvtn AS provider_state,
    prscrbr_type AS provider_specialty,

    COUNT(DISTINCT prscrbr_npi) AS unique_providers,
    COUNT(*) AS provider_drug_records,
    COUNT(DISTINCT gnrc_name) AS unique_generic_drugs,

    SUM(total_claims) AS total_claims,
    SUM(total_drug_cost) AS total_drug_cost,

    SUM(total_drug_cost) / NULLIF(SUM(total_claims), 0)
        AS cost_per_claim,

    SUM(total_30day_fills) AS total_30day_fills

FROM {{ ref('stg_prescriber_drug') }}

WHERE
    prscrbr_state_abrvtn IS NOT NULL
    AND prscrbr_type IS NOT NULL
    AND total_claims > 0
    AND total_drug_cost IS NOT NULL

GROUP BY
    prscrbr_state_abrvtn,
    prscrbr_type
