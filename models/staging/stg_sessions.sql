SELECT session_id, customer_id, session_ts,
       (session_ts AT TIME ZONE 'UTC')::date AS session_date,
       channel, landing_page
FROM {{ source('commerce_raw', 'sessions') }}
