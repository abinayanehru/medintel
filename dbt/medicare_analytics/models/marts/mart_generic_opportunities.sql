
{{ config(materialized='table') }}

WITH classified_drugs AS (

    SELECT
        TRIM(gnrc_name) AS generic_drug_name,
        total_claims,
        total_drug_cost,

        CASE
            WHEN LOWER(TRIM(brnd_name)) = LOWER(TRIM(gnrc_name))
                THEN 'Generic'
            ELSE 'Brand'
        END AS drug_type

    FROM {{ ref('stg_prescriber_drug') }}

    WHERE
        gnrc_name IS NOT NULL
        AND TRIM(gnrc_name) <> ''
        AND brnd_name IS NOT NULL
        AND TRIM(brnd_name) <> ''
        AND total_claims > 0
        AND total_drug_cost IS NOT NULL
        AND total_drug_cost >= 0
),

drug_cost_summary AS (

    SELECT
        generic_drug_name,

        SUM(total_claims) FILTER (
            WHERE drug_type = 'Brand'
        ) AS brand_claims,

        SUM(total_claims) FILTER (
            WHERE drug_type = 'Generic'
        ) AS generic_claims,

        SUM(total_drug_cost) FILTER (
            WHERE drug_type = 'Brand'
        ) AS brand_total_cost,

        SUM(total_drug_cost) FILTER (
            WHERE drug_type = 'Generic'
        ) AS generic_total_cost

    FROM classified_drugs

    GROUP BY generic_drug_name
),

eligible_drugs AS (

    SELECT
        *,
        1000 AS minimum_claims_per_category

    FROM drug_cost_summary

    WHERE
        brand_claims >= 1000
        AND generic_claims >= 1000
),

cost_comparison AS (

    SELECT
        generic_drug_name,
        brand_claims,
        generic_claims,
        brand_total_cost,
        generic_total_cost,
        minimum_claims_per_category,

        brand_total_cost / NULLIF(brand_claims, 0)
            AS brand_cost_per_claim,

        generic_total_cost / NULLIF(generic_claims, 0)
            AS generic_cost_per_claim

    FROM eligible_drugs
)

SELECT
    generic_drug_name,
    brand_claims,
    generic_claims,
    brand_total_cost,
    generic_total_cost,
    minimum_claims_per_category,

    brand_cost_per_claim,
    generic_cost_per_claim,

    GREATEST(
        brand_cost_per_claim - generic_cost_per_claim,
        0
    ) AS estimated_saving_per_claim,

    GREATEST(
        brand_cost_per_claim - generic_cost_per_claim,
        0
    ) * brand_claims
        AS estimated_cost_optimization_opportunity

FROM cost_comparison
