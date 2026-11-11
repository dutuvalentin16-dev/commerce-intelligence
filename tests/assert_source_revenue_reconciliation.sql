-- An independent source calculation prevents two equally wrong marts from passing.
WITH source_total AS (
    SELECT COALESCE(SUM(i.quantity * i.unit_price), 0) AS revenue
    FROM {{ source('commerce_raw', 'order_items') }} i
    JOIN {{ source('commerce_raw', 'orders') }} o USING (order_id)
    WHERE o.status = 'paid'
), mart_totals AS (
    SELECT 'daily' AS mart, COALESCE(SUM(net_revenue), 0) AS revenue
    FROM {{ ref('mart_daily_sales') }}
    UNION ALL
    SELECT 'channel', COALESCE(SUM(net_revenue), 0)
    FROM {{ ref('mart_channel_performance') }}
    UNION ALL
    SELECT 'category', COALESCE(SUM(net_revenue), 0)
    FROM {{ ref('mart_category_performance') }}
    UNION ALL
    SELECT 'customer', COALESCE(SUM(total_customer_revenue), 0)
    FROM {{ ref('mart_customer_repeat') }}
)
SELECT m.mart, m.revenue, s.revenue AS source_revenue
FROM mart_totals m CROSS JOIN source_total s
WHERE m.revenue <> s.revenue
