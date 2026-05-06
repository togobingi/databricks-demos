-- Silver Layer: Deduplicated product dimension
CREATE OR REFRESH MATERIALIZED VIEW  ${user_name}_silver_eurex_products (
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
FROM  ${user_name}_eurex_daily_stats
  WHERE product_code NOT IN ${bad_rows}
  AND sub_category NOT IN ('Sum');

