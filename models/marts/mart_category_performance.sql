SELECT
    p.category,
    SUM(CASE WHEN o.status = 'paid' THEN i.quantity ELSE 0 END)::integer AS paid_units,
    SUM(CASE WHEN o.status = 'paid' THEN i.line_value ELSE 0 END)::numeric(14,2) AS net_revenue,
    SUM(CASE WHEN o.status = 'paid' THEN i.quantity * (i.unit_price - p.unit_cost) ELSE 0 END)::numeric(14,2)
      AS estimated_product_margin
FROM {{ ref('stg_order_items') }} i
JOIN {{ ref('stg_orders') }} o ON i.order_id = o.order_id
JOIN {{ ref('stg_products') }} p ON i.product_id = p.product_id
GROUP BY 1
