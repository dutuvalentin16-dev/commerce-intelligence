-- Compatibility view for existing marts and consumers.
SELECT * FROM {{ ref('fct_orders') }}
