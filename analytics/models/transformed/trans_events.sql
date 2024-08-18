SELECT
    e.*,
    s.session_title,
    EXP(-0.3 * (e.current_winner_streak - 1)) AS penalty_factor
FROM {{ ref('stg_events') }} AS e
CROSS JOIN {{ ref('sessions') }} AS s
WHERE e.timestamp BETWEEN s.session_start AND s.session_end
