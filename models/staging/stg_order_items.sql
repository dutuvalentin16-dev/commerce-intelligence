SELECT order_item_id, order_id, product_id, quantity, unit_price,
       (quantity * unit_price)::numeric(14,2) AS line_value
FROM {{ source('commerce_raw', 'order_items') }}
