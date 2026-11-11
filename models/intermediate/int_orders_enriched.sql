WITH order_values AS (
    SELECT order_id, SUM(line_value) AS gross_order_value
    FROM {{ ref('stg_order_items') }}
    GROUP BY 1
)
SELECT
    o.order_id, o.customer_id, o.session_id, o.order_date, o.status,
    v.gross_order_value,
    CASE WHEN o.status = 'paid' THEN v.gross_order_value ELSE 0 END::numeric(14,2) AS recognized_revenue
FROM {{ ref('stg_orders') }} o
JOIN order_values v ON o.order_id = v.order_id
