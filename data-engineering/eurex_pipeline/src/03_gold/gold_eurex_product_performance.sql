-- Gold Layer: Per-product daily performance with MTD/YTD metrics
CREATE OR REFRESH MATERIALIZED VIEW <YOUR-NAME>_gold_eurex_product_performance
COMMENT 'Per-product daily performance with MTD/YTD metrics.'
AS
SELECT
  report_date,
  product_code,
  product_name,
  category,
  sub_category,
  product_group,
  SUM(traded_contracts) AS daily_contracts,
  SUM(volume_eur) AS daily_volume_eur,
  MAX(traded_contracts_month) AS mtd_contracts,
  MAX(traded_contracts_year) AS ytd_contracts,
  MAX(volume_eur_month) AS mtd_volume_eur,
  MAX(volume_eur_year) AS ytd_volume_eur,
  MAX(open_interest_prev_day) AS open_interest,
  MAX(open_interest_eur_prev_day) AS open_interest_eur,
  MAX(pc_ratio) AS pc_ratio
FROM <YOUR-NAME>_silver_eurex_daily_trading
GROUP BY report_date, product_code, product_name, category, sub_category, product_group;
