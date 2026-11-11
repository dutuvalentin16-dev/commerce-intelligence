-- Orders without lines would silently disappear from int_orders_enriched.
SELECT o.order_id
FROM {{ ref('stg_orders') }} o
LEFT JOIN {{ ref('stg_order_items') }} i USING (order_id)
GROUP BY o.order_id
HAVING COUNT(i.order_item_id) = 0
