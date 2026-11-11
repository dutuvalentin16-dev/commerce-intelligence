SELECT o.order_id
FROM {{ source('commerce_raw', 'orders') }} o
JOIN {{ source('commerce_raw', 'sessions') }} s USING (session_id)
WHERE o.customer_id <> s.customer_id
