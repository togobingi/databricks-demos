
-- Gold Layer: Top 20 products per day by daily volume EUR

SELECT
  report_date,
  volume_rank,
  product_code,
  product_name,
  category,
  daily_contracts,
  daily_volume_eur,
  open_interest_eur
FROM (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY report_date ORDER BY daily_volume_eur DESC) AS volume_rank
  FROM {{ source('sdp_pipeline','YOUR_USERNAME_gold_eurex_product_performance') }}
)
WHERE volume_rank <= 20;