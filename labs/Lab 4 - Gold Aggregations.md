
### Step 1: Create the Gold performance tables

Now create two new files `gold_eurex_product_performance.sql` and `gold_eurex.sql` under the `03_gold` folder. 

You can find the source code for these files in `eurex_pipeline/src/03_gold/`. Copy and paste the content into the respective files you just created.

These are simple aggregate datasets which:
- Show Per-product daily performance with MTD/YTD metrics
- Daily aggregates by category and sub-category


We are going to add one more Gold table that ranks products by EUR trading volume, and we will do this with dbt! 

But first, let us run the full end-to-end Lakeflow Spark Declarative Pipeline and explore the full lineage graph. 

---

### Step 2: Run the full pipeline 

1. In the pipeline UI, click on **Run pipeline** 
2. Watch the pipeline DAG update in real time — Bronze turns green first, then Silver, then Gold
![sdp-dag](/labs/artifacts/screenshots/sdp-dag.png)


3. Once complete, query your new Gold table:

   ```sql
   SELECT
       *
   FROM CATALOG.SCHEMA.gold_eurex
   ORDER BY volume_rank
   ```


 > **Discussion:** 
    Which category had the highest total contracts value? 
---

## What Happens Next?

You now have a working Medallion pipeline with data quality enforcement, clean Silver data, and Gold tables ready for analysis. In **Lab 5**, you will package this entire pipeline as a **Databricks Asset Bundle** — enabling repeatable deployments through CI/CD.

Proceed to **Lab 5 — Asset Bundles (DABs)**.