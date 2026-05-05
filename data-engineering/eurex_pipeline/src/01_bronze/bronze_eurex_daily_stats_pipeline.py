import os
import glob
import pandas as pd
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, DateType
)
from pyspark import pipelines as dp


# TODO
# Update these values with your volume and schema names and table names
VOLUME_PATH = "/Volumes/<CATALOG>/<SCHEMA>/<VOLUME-NAME>"
TABLE_NAME = "<APPEND-YOUR-NAME>_bronze_eurex_daily_stats"



def _extract_daily_stats(file_path: str) -> pd.DataFrame:
    """Extract and clean data from a single Eurex daily statistics XLS file."""
    filename = os.path.basename(file_path)
    date_str = filename.replace("dailystat_", "").replace(".xls", "")
    report_date = pd.to_datetime(date_str, format="%Y%m%d").date()

    df = pd.read_excel(
        file_path,
        sheet_name="Eurex Daily Statistics",
        header=None,
        skiprows=9,
    )

    columns = [
        "category", "sub_category", "product_group", "product_name", "product_code",
        "traded_contracts", "traded_contracts_flexible",
        "traded_contracts_month", "traded_contracts_flexible_month",
        "traded_contracts_year", "traded_contracts_flexible_year",
        "traded_contracts_avg_month", "traded_contracts_avg_year",
        "pc_ratio", "open_interest_prev_day",
        "volume_eur", "volume_eur_month", "volume_eur_year",
        "open_interest_eur_prev_day",
    ]
    df.columns = columns

    # Skip the header text row
    df = df.iloc[1:]

    # Forward-fill hierarchical columns
    df["category"] = df["category"].ffill()
    df["sub_category"] = df["sub_category"].ffill()
    df["product_group"] = df["product_group"].ffill()

    # Keep only rows with a product_code (actual data rows)
    df = df[df["product_code"].notna()].copy()

    # Cast numeric columns
    numeric_cols = [
        "traded_contracts", "traded_contracts_flexible",
        "traded_contracts_month", "traded_contracts_flexible_month",
        "traded_contracts_year", "traded_contracts_flexible_year",
        "traded_contracts_avg_month", "traded_contracts_avg_year",
        "pc_ratio", "open_interest_prev_day",
        "volume_eur", "volume_eur_month", "volume_eur_year",
        "open_interest_eur_prev_day",
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["report_date"] = report_date

    return df.reset_index(drop=True)


@dp.materialized_view(
    name=f"{TABLE_NAME}",
    comment="Eurex daily trading statistics extracted from XLS files in the volume.",
)
def eurex_daily_stats_pipeline():
    xls_files = sorted(glob.glob(os.path.join(VOLUME_PATH, "dailystat_*.xls")))

    all_dfs = []
    for file_path in xls_files:
        try:
            df = _extract_daily_stats(file_path)
            all_dfs.append(df)
        except Exception:
            pass  # Skip files that fail to parse

    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
    else:
        # Return empty DataFrame with correct schema
        combined_df = pd.DataFrame(columns=[
            "category", "sub_category", "product_group", "product_name", "product_code",
            "traded_contracts", "traded_contracts_flexible",
            "traded_contracts_month", "traded_contracts_flexible_month",
            "traded_contracts_year", "traded_contracts_flexible_year",
            "traded_contracts_avg_month", "traded_contracts_avg_year",
            "pc_ratio", "open_interest_prev_day",
            "volume_eur", "volume_eur_month", "volume_eur_year",
            "open_interest_eur_prev_day", "report_date",
        ])

    return spark.createDataFrame(combined_df)
