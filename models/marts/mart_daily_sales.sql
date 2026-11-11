SELECT
    order_date,
    COUNT(*)::integer AS all_orders,
    COUNT(*) FILTER (WHERE status = 'paid')::integer AS paid_orders,
    COUNT(*) FILTER (WHERE status = 'cancelled')::integer AS cancelled_orders,
    COUNT(*) FILTER (WHERE status = 'refunded')::integer AS refunded_orders,
    SUM(recognized_revenue)::numeric(14,2) AS net_revenue,
    (SUM(recognized_revenue) / NULLIF(COUNT(*) FILTER (WHERE status = 'paid'), 0))::numeric(14,2)
        AS average_paid_order_value
FROM {{ ref('int_orders_enriched') }}
GROUP BY order_date
