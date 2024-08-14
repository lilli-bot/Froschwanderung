
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
        -- indicate when a subsequent row indicates a session or user change
        {{extract_session_from_timestamp(timestamp_column = 'timestamp')}} AS session_change,
        {{extract_user_from_timestamp(timestamp_column = 'timestamp')}} AS user_change,
        CASE WHEN clicked_image = LAG(clicked_image, 1) OVER (ORDER BY timestamp) 
            THEN FALSE
            ELSE TRUE 
        END AS winner_change
    FROM parquet_data
)
SELECT
    event_id,
    clicked_image,
    not_clicked_image,
    timestamp,
    filename,
    -- every time a user or session1 changes, increment the ID counter by ID, starting from 1
    SUM(CASE WHEN user_change = TRUE THEN 1 ELSE 0 END) OVER (ORDER BY timestamp) + 1 AS user_id,
    SUM(CASE WHEN session_change = TRUE THEN 1 ELSE 0 END) OVER (ORDER BY timestamp) + 1 AS session_id,
    SUM(CASE WHEN winner_change = FALSE THEN 1 ELSE 0 END) OVER (PARTITION BY clicked_image ORDER BY timestamp) + 1 AS current_winner_streak,
FROM lagged_timestamps