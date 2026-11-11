WITH paid_orders AS (
    SELECT customer_id, COUNT(*) AS paid_order_count, SUM(recognized_revenue) AS revenue
    FROM {{ ref('int_orders_enriched') }}
    WHERE status = 'paid'
    GROUP BY 1
)
SELECT
    COUNT(*)::integer AS paying_customers,
    COUNT(*) FILTER (WHERE paid_order_count >= 2)::integer AS repeat_customers,
    (COUNT(*) FILTER (WHERE paid_order_count >= 2)::numeric / NULLIF(COUNT(*), 0))::numeric(6,4)
      AS repeat_customer_rate,
    SUM(revenue)::numeric(14,2) AS total_customer_revenue
FROM paid_orders
