## Step 3: Add Transformations & Expectations to the Silver Layer

Let's create some silver tables in SQL this time.

Now create two new files `silver_eurex_daily_trading.sql` and `silver_eurex_products.sql` under the `02_silver` folder. 

You can find the source code for these files in `eurex_pipeline/src/02_silver/`. Copy and paste the content into the respective files you just created.

### Filter Out Summary Rows

Eurex XLS sheets include total/summary rows at the bottom of each product group. These rows have generic labels like `"Sum"` which skew aggregations in Gold.

Inside both `silver` table files, add a filter **at the bottom of the query**:

   ```sql
   AND sub_category NOT IN ('Sum'); -- or WHERE sub_category NOT IN ('Sum')
   ```

### Remove bad rows
If you explore the `product_code` column in the bronze dataset, you may notice some rows which contain entries like `Product Settle Type` and `'--'`. We would like to remove these as they will affect our reporting. 

We could simply add a filter to our code; However to ensure we implement [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) code, we will create a global configuration variable which we can dynamically reference from anywhere in the pipeline like this: `${bad_rows}`.

1. In the Pipeline UI, click on the **Settings** button, then under the **Configurations** section, click on **Edit Configurations** and add the following value then save it.
- key: `bad_rows`
- value: `('Product Settle Type','--')`

2. At the bottom of both silver files, add the following filter to remove any row with these values from your dataset:
 ```sql
     WHERE product_code NOT IN ${bad_rows} -- OR AND product_code NOT IN ${bad_rows}
 ```

![bad-rows](/data-engineering/labs/artifacts/screenshots/bad_rows.png)

### Append the view names with your name 
Before running the pipeline, make sure you append the view names with your name as you did in lab 2. Then, click on **Run pipeline** on the top right, and you should see the new materialised silver views created in the UI.



### Add data quality expectations 

Data quality expectations prevent bad rows from reaching the Silver table and make failures visible in the pipeline UI.

1. In the `silver_eurex_daily_trading`.sql file, two expectations are already defined. Add a third to catch rows with zero or negative traded contracts:

   ```sql
   CONSTRAINT valid_traded_contracts EXPECT (traded_contracts >= 0)
   ```

   Place it alongside the existing constraints, like this:

```sql
 CREATE OR REFRESH MATERIALIZED VIEW silver_eurex_daily_trading (
  CONSTRAINT valid_volume_eur EXPECT (volume_eur >= 0),
  CONSTRAINT valid_report_date EXPECT (report_date IS NOT NULL) ON VIOLATION FAIL UPDATE,
  CONSTRAINT valid_traded_contracts EXPECT (traded_contracts >= 0) ON VIOLATION DROP ROW
)
   ```


2. **What is the difference between expectation types?**
   - `EXPECT ... ON VIOLATION DROP ROW` — It drops the row if the condition fails 
   - `EXPECT` — It "warns" and records the violation for monitoring, but keeps the rows
   Learn more details [here](https://docs.databricks.com/aws/en/ldp/expectations#action-on-invalid-record)

> 💡 After running the pipeline, click on the Silver table node in the pipeline UI to see the **Expectations** column and then the panel. It shows how many rows passed and failed each expectation. 

![Expectations](/data-engineering/labs/artifacts/screenshots/expectations.png)


## What Happens Next?

You now have implemented quality checks and removed corrupted rows from the silver table. Its now time to build our gold aka "consumer-aligned" data products. Head on over to **Lab 4** to continue.