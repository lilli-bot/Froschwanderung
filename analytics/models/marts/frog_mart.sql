WITH wins AS (
	SELECT clicked_image::VARCHAR AS image_id , COUNT(*) AS wins 
	FROM {{ref('trans_events')}} te
	GROUP BY clicked_image
),
losses AS (
	SELECT not_clicked_image::VARCHAR AS image_id, COUNT(*) AS losses
	FROM  {{ref('trans_events')}} te
	GROUP BY not_clicked_image
),
wins_losses AS(
	SELECT wins.image_id, wins.wins, losses.losses
	FROM wins 
	JOIN losses USING (image_id)
),
frog_score AS(
	SELECT te.clicked_image as image_id, SUM(penalty_factor) AS image_score
	FROM {{ref('trans_events')}} te
	GROUP BY 1
)
SELECT
  f.*, wl.wins, wl.losses, sc.image_score
FROM
  {{ref('frogs')}} f
LEFT JOIN wins_losses wl ON f.image_id::VARCHAR = wl.image_id::VARCHAR
LEFT JOIN frog_score sc ON f.image_id ::VARCHAR = sc.image_id::VARCHAR

