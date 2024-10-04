SELECT
    e.*,
    --s.exhibition_title,
    EXP(-0.3 * (e.current_winner_streak - 1)) AS penalty_factor
FROM {{ ref('stg_events') }} AS e
--CROSS JOIN {{ ref('exhibitions') }} AS s
--OPTIONAL: Only include those events for which we have a exhibition for in the metadata (seed data)
--WHERE e.timestamp BETWEEN s.exhibition_start AND s.exhibition_end
