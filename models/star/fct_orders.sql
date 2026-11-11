-- Grain: one order; aggregate items before joining to avoid fanout.
WITH values_by_order AS (
    SELECT order_id, SUM(line_value)::numeric(14,2) AS gross_order_value,
           SUM(recognized_revenue)::numeric(14,2) AS recognized_revenue
    FROM {{ ref('fct_order_items') }} GROUP BY order_id
)
SELECT o.*, v.gross_order_value, v.recognized_revenue
FROM {{ ref('stg_orders') }} o JOIN values_by_order v USING (order_id)
