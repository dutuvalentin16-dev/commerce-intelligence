-- Revenue in channel and daily marts must agree: both measure paid-order revenue.
SELECT 1 AS mismatch
WHERE ABS(
    (SELECT COALESCE(SUM(net_revenue), 0) FROM {{ ref('mart_channel_performance') }})
    -
    (SELECT COALESCE(SUM(net_revenue), 0) FROM {{ ref('mart_daily_sales') }})
) > 0.01
