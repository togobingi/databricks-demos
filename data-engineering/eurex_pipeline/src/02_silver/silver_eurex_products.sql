-- Silver Layer: Deduplicated product dimension
CREATE OR REFRESH MATERIALIZED VIEW <YOUR_NAME>_silver_eurex_products (
  CONSTRAINT valid_product_code EXPECT (product_code IS NOT NULL) ON VIOLATION DROP ROW
)
COMMENT 'Deduplicated product dimension table from Eurex daily statistics.'
AS
SELECT DISTINCT
  product_code,
  product_name,
  product_group,
  sub_category,
  category
FROM <YOUR_NAME>_eurex_daily_stats;

