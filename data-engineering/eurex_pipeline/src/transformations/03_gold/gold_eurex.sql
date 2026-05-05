-- Gold Layer: Daily aggregates by category and sub-category
CREATE OR REFRESH MATERIALIZED VIEW gold_eurex_category_summary
COMMENT 'Daily aggregates by category and sub-category.'
AS
SELECT
  report_date,
  category,
  sub_category,
  SUM(traded_contracts) AS total_contracts,
  SUM(traded_contracts_flexible) AS total_contracts_flexible,
  SUM(volume_eur) AS total_volume_eur,
  SUM(open_interest_prev_day) AS total_open_interest,
  SUM(open_interest_eur_prev_day) AS total_open_interest_eur,
  COUNT(DISTINCT product_code) AS product_count,
  AVG(pc_ratio) AS avg_pc_ratio
FROM silver_eurex_daily_trading
GROUP BY report_date, category, sub_category;




