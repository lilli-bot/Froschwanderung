
{{
  config(
    materialized = 'table',
    )
}}

WITH parquet_data AS (
    SELECT *
    FROM read_parquet('./results/*.parquet', filename=true)
),
lagged_timestamps AS (
    SELECT 
        event_id,
        clicked_image,
        not_clicked_image,
        timestamp,
        filename,
        {{extract_session_from_timestamp(timestamp_column = 'timestamp')}} AS session_change,
        {{extract_user_from_timestamp(timestamp_column = 'timestamp')}} AS user_change
    FROM parquet_data
)
SELECT
    event_id,
    clicked_image,
    not_clicked_image,
    timestamp,
    filename,
    SUM(CASE WHEN user_change = TRUE THEN 1 ELSE 0 END) OVER (ORDER BY timestamp) + 1 AS user_id,
    SUM(CASE WHEN session_change = TRUE THEN 1 ELSE 0 END) OVER (ORDER BY timestamp) + 1 AS session_id
FROM lagged_timestamps