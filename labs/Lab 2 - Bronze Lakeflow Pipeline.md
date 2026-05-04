# 🔁 Lab 2 – The Lakeflow Pipeline (Bronze)

## 🎯 Learning Objectives
By the end of this lab, you will:
- Upload a real Eurex Daily Statistics report to a Unity Catalog Volume
- Understand how a Lakeflow Spark Declarative Pipelines declares tables across the Medallion layers
- Add **data quality expectations** to the Silver layer to catch bad rows
- Filter out aggregation/summary rows that pollute the dataset
- Build a **Gold table** that surfaces the top-performing Eurex products by trading volume

## Introduction

**What is Lakeflow Spark Declarative Pipelines (SDP)?**

SDP is Databricks' declarative pipeline framework. Instead of writing imperative jobs that call each other, you define each table and Databricks handles orchestration, dependencies, incremental updates, and lineage automatically.

**Why Medallion Architecture?**

| Layer | Rule | What we do |
|-------|------|------------|
| **Bronze** | Keep everything, change nothing | Parse raw XLS sheets, preserve all strings |
| **Silver** | Clean, type, validate | Cast numerics, enforce DQ expectations, drop bad rows |
| **Gold** | Aggregate for the business | Top products, volume by segment, market sentiment |

The Eurex XLS report covers **11 sheets** of derivatives trading data — equity options, index futures, ETF derivatives, and fixed-income products traded on Frankfurt's derivatives exchange.

---

## Instructions

### Step 1: Upload the Eurex XLS File to Your Personal Volume

Each participant uploads the report to their own volume to avoid conflicts.


1. In the Catalog Explorer, navigate to your Unity Catalog volume and click **Upload to this volume**
2. Upload `dailystat_20260428.xls` (found [here](https://www.eurex.com/ex-en/data/statistics/trading-statistics) or download it from this repo: `labs/artifacts/data/dailystat_20260428.xls`)


> 💡 The XLS file contains Eurex's official daily report for 28 April 2026 — traded contract counts, EUR volumes, put/call ratios, and open interest across all market segments.


--- 

### Step 2: Create a Lakeflow pipeline
To create a new ETL pipeline using the Lakeflow Pipelines Editor, follow these steps:

1. At the top of the left sidebar, click `+` icon and then select `ETL Pipeline`.

2. At the top, you can give your pipeline a unique name such as "Eurex ETL pipeline". To the right of the pipeline name, you will see the default `catalog` and `schema` that have been automatically selected for your pipeline. You can change these if required to the catalog and schema you will use.

![pipeline-UI](/labs/artifacts/screenshots/sdp-ui.png)

3. Click on the pipeline **Settings** and add `xlrd>=2.0.1` under the **Pipeline environment -> Dependencies -> edit Environment** section. Click save We need this to be able to process `xls` files.
---

### Step 3: Explore the Bronze Layer

1. Let's rename the root folder of the pipeline directory from `New Pipeline 2026-05-05...` to `Eurex Pipeline` for instance. Click on the 3 dots next to the root directory name and click on **Rename root folder**.
2. Delete the default `transformations` folder that was automatically created for this pipeline. 
3. Now click on the `+` icon next to the root folder to create a `New pipeline source code folder` for each stage in the medallion architecture:
    - 01_bronze
    - 02_silver
    - 03_gold

Now your project structure should look like this:
![sdp-folder-struc](/labs/artifacts/screenshots/sdp-folder-structure.png)

4. Now click on the `+` icon next to the `01_bronze` folder and create a new file called `bronze_eurex_daily_stats_pipeline.py`. 
   - From this repo copy the code from this path `eurex_pipeline/src/01_bronze/bronze_eurex_daily_stats_pipeline.py` and paste it in the new file you just created in the UI.

5. Review line 12 and 13 in the file and update the `VOLUME_PATH` & `TABLE_NAME` to match yours:
   - ```python
       VOLUME_PATH = "/Volumes/<CATALOG>/<SCHEMA>/<VOLUME-NAME>"
       TABLE_NAME = "<APPEND-YOUR-NAME>_bronze_eurex_daily_stats"
      ```
6. Here is a summary of what this file does:
   - We are parsing through the file from the Volume and cleaning out some rows which don't include any data
   - On line 70, we are creating a Materiazed view, which is one of the core dataset types in SDP.
   - As we might be sharing the same schema in the workshop, you are expected to append the view's/table name with your name so you can find it easily in Unity Catalog.
  
7. To run the pipeline, click on the `Run pipeline` button on the top right 
   ![bronze-run](/labs/artifacts/screenshots/bronze-run.png)

8. (**Optional**) Open the the SQL Editor in the left side bar, run the following query to view the rows in the file you created:

   ```sql
   SELECT * FROM SCHEMA.CATALOG.<APPEND_YOUR_NAME>_bronze_eurex_daily_stats
   ```


5. Scroll through the raw rows. Notice rows where `product_code` is blank `--` — these are **category headers** (e.g. "Equity Derivatives:") and summary rows (e.g. a row labelled "Sum"). The Bronze parser already strips empty rows, but summary rows can slip through. We will clean them up in Silver, although you could also do that in this step if you want.


## What Happens Next?

You now have the bronze layer completed. Head on over to **Lab 3** to build our multiple silver tables.