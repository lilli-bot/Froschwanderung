{{
  config(
    materialized = 'table',
    )
}}

WITH parquet_data AS (
    SELECT *
    FROM read_parquet('./results/*.parquet', filename=true)
)

SELECT *
FROM parquet_data