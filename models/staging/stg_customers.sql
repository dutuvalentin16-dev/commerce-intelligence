SELECT customer_id, signup_date, region
FROM {{ source('commerce_raw', 'customers') }}
