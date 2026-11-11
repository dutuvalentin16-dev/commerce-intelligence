-- dbt singular data test: returns rows on failure.
SELECT * FROM {{ ref('mart_channel_performance') }}
WHERE conversion_rate < 0 OR conversion_rate > 1
