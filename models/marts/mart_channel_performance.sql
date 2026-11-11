-- Pre-aggregate orders at session grain to avoid duplicating sessions or revenue.
WITH per_session_orders AS (
    SELECT
        session_id,
        MAX(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) AS has_paid_order,
        SUM(recognized_revenue) AS recognized_revenue
    FROM {{ ref('int_orders_enriched') }}
    GROUP BY session_id
)
SELECT
    s.channel,
    COUNT(*)::integer AS sessions,
    SUM(COALESCE(o.has_paid_order, 0))::integer AS converted_sessions,
    SUM(COALESCE(o.recognized_revenue, 0))::numeric(14,2) AS net_revenue,
    (SUM(COALESCE(o.has_paid_order, 0))::numeric / NULLIF(COUNT(*), 0))::numeric(6,4)
      AS conversion_rate
FROM {{ ref('stg_sessions') }} s
LEFT JOIN per_session_orders o USING (session_id)
GROUP BY 1
