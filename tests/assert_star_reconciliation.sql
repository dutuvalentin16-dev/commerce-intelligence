-- Check coverage and values at both fact grains, independently of marts.
WITH expected AS (
 SELECT o.order_id, SUM(i.quantity * i.unit_price)::numeric(14,2) AS gross,
        SUM(CASE WHEN o.status = 'paid' THEN i.quantity * i.unit_price ELSE 0 END)::numeric(14,2) AS revenue
 FROM {{ source('commerce_raw', 'orders') }} o
 JOIN {{ source('commerce_raw', 'order_items') }} i USING (order_id)
 GROUP BY o.order_id
)
SELECT COALESCE(e.order_id, f.order_id) AS invalid_id
FROM expected e FULL JOIN {{ ref('fct_orders') }} f USING (order_id)
WHERE e.order_id IS NULL OR f.order_id IS NULL
   OR e.gross IS DISTINCT FROM f.gross_order_value
   OR e.revenue IS DISTINCT FROM f.recognized_revenue
UNION ALL
SELECT COALESCE(r.order_item_id, f.order_item_id)
FROM {{ source('commerce_raw', 'order_items') }} r
FULL JOIN {{ ref('fct_order_items') }} f USING (order_item_id)
WHERE r.order_item_id IS NULL OR f.order_item_id IS NULL
   OR (r.quantity * r.unit_price) IS DISTINCT FROM f.line_value
