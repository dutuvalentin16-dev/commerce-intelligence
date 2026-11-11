SELECT product_id, category, unit_cost
FROM {{ source('commerce_raw', 'products') }}
