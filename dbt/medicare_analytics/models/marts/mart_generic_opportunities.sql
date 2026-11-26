{{ config(materialized='table') }}

WITH classified_drugs AS (

    SELECT
        gnrc_name,
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
        AND brnd_name IS NOT NULL
        AND total_claims > 0
        AND total_drug_cost IS NOT NULL
),

drug_cost_summary AS (

    SELECT
        gnrc_name,

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
    GROUP BY gnrc_name
),

cost_comparison AS (

    SELECT
        gnrc_name AS generic_drug_name,
        brand_claims,
        generic_claims,
        brand_total_cost,
        generic_total_cost,

        brand_total_cost / NULLIF(brand_claims, 0)
            AS brand_cost_per_claim,

        generic_total_cost / NULLIF(generic_claims, 0)
            AS generic_cost_per_claim

    FROM drug_cost_summary

    WHERE
        brand_claims > 0
        AND generic_claims > 0
)

SELECT
    generic_drug_name,
    brand_claims,
    generic_claims,
    brand_total_cost,
    generic_total_cost,
    brand_cost_per_claim,
    generic_cost_per_claim,

    GREATEST(
        brand_cost_per_claim - generic_cost_per_claim,
        0
    ) AS estimated_saving_per_claim,

    GREATEST(
        brand_cost_per_claim - generic_cost_per_claim,
        0
    ) * brand_claims AS estimated_cost_optimization_opportunity

FROM cost_comparison
