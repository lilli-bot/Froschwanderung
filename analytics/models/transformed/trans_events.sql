
SELECT 
    e.*,
    s.session_title
FROM {{ ref('stg_events') }} e
CROSS JOIN {{ ref('sessions') }} s
    WHERE e.timestamp BETWEEN s.session_start AND s.session_end