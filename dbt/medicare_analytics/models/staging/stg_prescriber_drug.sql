
{{ config(materialized='view') }}

SELECT
    prscrbr_npi,
    prscrbr_last_org_name,
    prscrbr_first_name,
    prscrbr_city,
    prscrbr_state_abrvtn,
    prscrbr_state_fips,
    prscrbr_type,
    prscrbr_type_src,

    brnd_name,
    gnrc_name,

    TRY_CAST(NULLIF(TRIM(tot_clms), '') AS BIGINT)
        AS total_claims,

    TRY_CAST(NULLIF(TRIM(tot_30day_fills), '') AS DOUBLE)
        AS total_30day_fills,

    TRY_CAST(NULLIF(TRIM(tot_day_suply), '') AS BIGINT)
        AS total_day_supply,

    TRY_CAST(NULLIF(TRIM(tot_drug_cst), '') AS DOUBLE)
        AS total_drug_cost,

    TRY_CAST(NULLIF(TRIM(tot_benes), '') AS BIGINT)
        AS total_beneficiaries,

    NULLIF(TRIM(ge65_sprsn_flag), '') AS ge65_suppression_flag,

    TRY_CAST(NULLIF(TRIM(ge65_tot_clms), '') AS BIGINT)
        AS ge65_total_claims,

    TRY_CAST(NULLIF(TRIM(ge65_tot_30day_fills), '') AS DOUBLE)
        AS ge65_total_30day_fills,

    TRY_CAST(NULLIF(TRIM(ge65_tot_drug_cst), '') AS DOUBLE)
        AS ge65_total_drug_cost,

    TRY_CAST(NULLIF(TRIM(ge65_tot_day_suply), '') AS BIGINT)
        AS ge65_total_day_supply,

    NULLIF(TRIM(ge65_bene_sprsn_flag), '')
        AS ge65_beneficiary_suppression_flag,

    TRY_CAST(NULLIF(TRIM(ge65_tot_benes), '') AS BIGINT)
        AS ge65_total_beneficiaries

FROM iceberg_scan(
    '{{ env_var("MEDICARE_ICEBERG_METADATA_PATH") }}'
)
