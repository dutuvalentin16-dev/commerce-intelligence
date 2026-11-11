SELECT order_id, customer_id, session_id, order_ts,
       (order_ts AT TIME ZONE 'UTC')::date AS order_date,
       status
FROM {{ source('commerce_raw', 'orders') }}
