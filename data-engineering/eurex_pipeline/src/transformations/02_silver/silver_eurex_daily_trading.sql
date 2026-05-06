-- Silver Layer: Cleaned daily trading fact table
CREATE OR REFRESH MATERIALIZED VIEW ${user_name}_silver_eurex_daily_trading (
  CONSTRAINT valid_traded_contracts EXPECT (traded_contracts >= 0),
  CONSTRAINT valid_volume_eur EXPECT (volume_eur >= 0),
  CONSTRAINT valid_report_date EXPECT (report_date IS NOT NULL) ON VIOLATION FAIL UPDATE
  )
COMMENT 'Cleaned daily trading fact table with only rows containing trading activity.'
AS
SELECT
  report_date,
  product_code,
  product_name,
  category,
  sub_category,
  product_group,
  nanvl(traded_contracts, null) AS traded_contracts,
  nanvl(traded_contracts_flexible, null) AS traded_contracts_flexible,
  nanvl(traded_contracts_month, null) AS traded_contracts_month,
  nanvl(traded_contracts_flexible_month, null) AS traded_contracts_flexible_month,
  nanvl(traded_contracts_year, null) AS traded_contracts_year,
  nanvl(traded_contracts_flexible_year, null) AS traded_contracts_flexible_year,
  nanvl(traded_contracts_avg_month, null) AS traded_contracts_avg_month,
  nanvl(traded_contracts_avg_year, null) AS traded_contracts_avg_year,
  nanvl(pc_ratio, null) AS pc_ratio,
  nanvl(open_interest_prev_day, null) AS open_interest_prev_day,
  nanvl(volume_eur, null) AS volume_eur,
  nanvl(volume_eur_month, null) AS volume_eur_month,
  nanvl(volume_eur_year, null) AS volume_eur_year,
  nanvl(open_interest_eur_prev_day, null) AS open_interest_eur_prev_day
FROM  ${user_name}_eurex_daily_stats
WHERE (NOT isnan(traded_contracts) OR NOT isnan(traded_contracts_month)
       OR NOT isnan(traded_contracts_year) OR NOT isnan(volume_eur)
       OR NOT isnan(volume_eur_month) OR NOT isnan(volume_eur_year)
       OR NOT isnan(open_interest_prev_day) OR NOT isnan(open_interest_eur_prev_day))
  AND product_code NOT IN ${bad_rows}
  AND sub_category NOT IN ('Sum')
