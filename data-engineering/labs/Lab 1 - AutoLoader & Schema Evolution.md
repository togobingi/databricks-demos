# Lab 1 – AutoLoader & Schema Evolution

##  Learning Objectives
By the end of this lab, you will:
- Create a Unity Catalog Volume to store raw files
- Use **AutoLoader** to incrementally ingest CSV files into a Delta table
- Understand what happens when a new column appears in an incoming file
- Change the **schema evolution mode** to handle schema drift gracefully

## Introduction

**What is AutoLoader?**

AutoLoader (`cloudFiles` format) is Databricks' built-in incremental file ingestion engine. It monitors a cloud storage path and processes only new files as they arrive — without scanning what was already processed.

Key advantages over a regular `spark.read`:
- **Incremental**: only processes new files, not the whole directory
- **Scalable**: handles millions of files efficiently using file notifications
- **Schema inference**: automatically detects and evolves the schema of incoming files

**Why does schema evolution matter?**

In financial data pipelines, upstream systems frequently add new fields to reports. Without handling schema drift, your pipeline will break. AutoLoader gives you control over what happens:

| Mode | Behaviour |
|------|-----------|
| `addNewColumns` *(default)* | Stream fails. New columns are added to the schema. Existing columns do not evolve data types. |
| `none` | Does not evolve the schema, new columns are ignored, and data is not rescued unless the rescuedDataColumn option is set. Stream does not fail due to schema changes. |
| `rescue` | Keeps processing; puts unexpected columns in a `_rescued_data` column |

See more options [here](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/schema#how-does-auto-loader-schema-evolution-work).

---

## Instructions

### Step 1: Navigate to your Personal Volume

Each attendee gets their own volume to avoid file conflicts.


1. Navigate to **Catalog -> Schema** 
2. You should see a volume within your schema

![uc-UI](/data-engineering/labs/artifacts/screenshots/uc-catalog.png)
  


---

### Step 2: Upload the First CSV File

1. Download `trades_day1.csv` from the `labs/artifacts/data/` folder in this repository
2. In Catalog Explorer, navigate to your volume and click **Upload to this volume**
3. Upload **ONLY** the `trades_day1.csv` file in this step

4. Confirm the file is visible in the UI. You can also confirm this programmatically. Click on the **'+ New -> Notebook'** button in the left sidebar, and paste this in the notebook:
   ```python
   display(dbutils.fs.ls("/Volumes/<catalog_name>/<schema_name>/<volume_name>"))
   ```

   You should see details about the file you just uploaded.

---

### Step 3: Read with AutoLoader

> 💡 You initiate Auto Loader when you include this line in your code: `.format("cloudFiles")`

1. In a new cell in your notebook, run the following to read the CSV file with AutoLoader:


```python
    CHECKPOINT_SCHEMA_PATH = "/tmp/autoloader_checkpoint"
 VOLUME_PATH = "/Volumes/<CATALOG>/<SCHEMA>/<VOLUME-NAME>"

df= (
       spark.readStream
           .format("cloudFiles")
           .option("cloudFiles.format", "csv")
           .option("header", "true")
           .option("cloudFiles.schemaLocation", CHECKPOINT_SCHEMA_PATH)
           .load(VOLUME_PATH)
   )

```

2. Once complete, query the dataframe:
   ```python
   display(df)
   ```

3. Note the columns: `product_id`, `product_name`, `traded_contracts`, `volume_eur`

---

### Step 4: Upload a Second CSV with a New Column

The next day's file has an extra column: `asset_class`.

1. Upload `trades_day2.csv` to your volume (same steps as Step 2)

2. Re-run the AutoLoader cell from Step 3

3. **What happens?** The stream stops with a schema mismatch error — the new `asset_class` column isn't in the inferred schema.

> 💡 This is intentional. AutoLoader's default behaviour protects you from accidentally corrupting your Delta table with unexpected columns. In production you'd receive an alert and investigate before proceeding.

---

### Step 5: Handle the Schema Change

Now fix it by enabling schema evolution. Choose the mode that fits your scenario:

**Option A — Add the new column automatically:**

```python
df = (
    spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("cloudFiles.schemaLocation", CHECKPOINT_PATH)
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")   # ← add this
        .load(VOLUME_PATH)
)

```

**Option B — Rescue unexpected columns instead:**

```python
.option("cloudFiles.schemaEvolutionMode", "rescue")
```

With `rescue`, the `asset_class` value will appear inside the `_rescued_data` JSON column rather than as a proper column. Useful when you want to capture schema changes without modifying your table structure immediately.

2. Re-run with **Option A** and then query the table again:

   ```python
   dsiplay(df)
   ```

3. Confirm:
   - Rows from `trades_day1.csv` have `asset_class = null`
   - Rows from `trades_day2.csv` have `asset_class` populated

---

## What Happens Next?

You have seen how AutoLoader handles incremental ingestion and schema evolution. These same principles power the **Bronze layer** in Lab 2 — except instead of CSV files, you'll be parsing multi-sheet XLS reports from Deutsche Börse and running the entire pipeline through Lakeflow Spark Declarative Pipeline (SDP).

Proceed to **Lab 2 — The Eurex Lakeflow Pipeline**.
