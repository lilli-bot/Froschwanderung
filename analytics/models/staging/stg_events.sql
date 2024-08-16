{# We need to materialise this into a table because later when this query will be read
    from a DuckDB inside a container, the path of the Parquets will not be correct.
    In other words: The parquets will not even be IN the container.
    To change this, you either need to run Metabase on your local machine directly OR provide
    the Parquet files in the Container volume. #}
{{
  config(
    materialized = 'table',
    )
}}

WITH parquet_data AS (
    SELECT *
    FROM read_parquet('./results/*.parquet', filename=true)
    ORDER BY timestamp
),
lagged_timestamps AS (
    SELECT 
        event_id,
        clicked_image,
        not_clicked_image,
        timestamp AT TIME ZONE 'Europe/Berlin' AS timestamp,
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
    -- every time a user or session changes, increment the ID counter by ID, starting from 1
    SUM(CASE WHEN user_change = TRUE THEN 1 ELSE 0 END) OVER (ORDER BY timestamp) + 1 AS user_id,
    SUM(CASE WHEN session_change = TRUE THEN 1 ELSE 0 END) OVER (ORDER BY timestamp) + 1 AS session_id,
    -- ever time the winner stays the same, the current streak of the winner increments
    SUM(CASE WHEN winner_change = FALSE THEN 1 ELSE 0 END) 
        OVER (PARTITION BY clicked_image ORDER BY timestamp) + 1 AS current_winner_streak,
FROM lagged_timestamps
-- TODO Impute missing timestamps
WHERE timestamp IS NOT NULL
ORDER BY timestamp