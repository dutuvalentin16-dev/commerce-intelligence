-- Compare actual timestamps, not strings; signup_date has day-level precision.
SELECT s.session_id, o.order_id
FROM {{ ref('stg_sessions') }} s
JOIN {{ ref('stg_customers') }} c USING (customer_id)
LEFT JOIN {{ ref('stg_orders') }} o USING (session_id)
WHERE s.session_date < c.signup_date
   OR o.order_ts < s.session_ts
