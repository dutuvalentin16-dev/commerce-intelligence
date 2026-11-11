-- Grain: one order item; source order_item_id is the durable primary key.
SELECT i.*, o.customer_id, o.session_id, o.order_date, o.status,
       CASE WHEN o.status = 'paid' THEN i.line_value ELSE 0 END::numeric(14,2) AS recognized_revenue
FROM {{ ref('stg_order_items') }} i
JOIN {{ ref('stg_orders') }} o USING (order_id)
