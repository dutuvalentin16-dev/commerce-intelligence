-- Type 1 dimension: one current row per source business key.
SELECT * FROM {{ ref('stg_products') }}
