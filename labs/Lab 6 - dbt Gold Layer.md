## 1) Prepare prerequisites
1. Make sure you have a Databricks workspace, a SQL warehouse or cluster you can use, and a way to authenticate, usually a personal access token (PAT) or OAuth setup. We will walk you through this
2. Install Python 3.9+ if you don’t already have it, and use a virtual environment so the dbt packages stay isolated from other projects.
3. If you plan to use Databricks from your local machine, confirm that your Databricks workspace has the permissions needed to create/query schemas and tables.

## 2) Create a virtual environment
Run this in a terminal:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

A virtual environment is recommended so your dbt installation is clean and repeatable.

## 3) Install dbt for Databricks
Install the adapter package:

```bash
pip install dbt-databricks
```

This package brings in dbt Core plus the Databricks adapter needed for local development against Databricks.

## 4) Initialize a dbt project
Within the eurex_pipeline repo, run the following command to initialize dbt:

```bash
dbt init 
```

When prompted, choose **Databricks** as the adapter. dbt will create the usual project structure such as `models/`, `tests/`, and `dbt_project.yml`. Below is an example of options you should select:
- Enter project name: eurex_dbt
- Database: Databricks
- Host: use your workspace URL eg `https://WORKSPACE-ID.gcp.databricks.com/`
- http_path: Go to  SQL Warehouses → Select a SQL Warehouse → Connection Details → copy the HTTP Path and paste it here
- access token: Get it here: Workspace → Settings → Developer → Access Tokens - Manage → Generate new token (copy the token and save it somewhere safe). Paste the token in the terminal to continue
- Select the option to use “Use Unity Catalog”
- Catalog: type in your catalog name
- schema: type in your schema name
- Threads: 4

## 5) Your `profiles.yml` file
dbt reads connection settings from `~/.dbt/profiles.yml` on your machine. One should have been created for you automatically after completing the steps above. A typical Databricks profile looks like this:

```yaml
eurex_dbt:
  target: dev
  outputs:
    dev:
      type: databricks
      catalog: main
      schema: analytics
      host: your-workspace.cloud.databricks.com
      http_path: /sql/1.0/warehouses/your-warehouse-id
      token: databricks_pat_here
      threads: 4
```

## 6) Test the connection
From your project directory, run:

```bash
cd eurex_dbt
dbt debug
```

This checks that dbt can find your profile and successfully connect to Databricks. If it fails, the most common issues are a wrong `http_path`, dbt not finding the profiles.yml file, an invalid token, or a schema/catalog permission problem.

## 7) Copy source code from the repo into your local files
In this repo under `eurex_pipeline/eurex_dbt/models/` copy the contents of both files `gold_eurex_top_movers` and `schema.yml` and paste them in your project with the same file names. Delete the other files which are within the models/ directory:

![dbt-proj](/labs/artifacts/screenshots/dbt-sturcture.png)

## 8) Run the dbt project

```bash
dbt run
```

dbt will build your models in the target schema. 

## Common setup issues
- If `dbt debug` cannot connect, check that your workspace URL and warehouse `http_path` are correct.
- If dbt cannot create objects, grant the necessary schema privileges in Databricks.
- If you prefer not to store secrets in plain text, use environment variables instead of hardcoding the token in `profiles.yml`.

## 9) Deploy a unified SDP + dbt job
To build one unified job where SDP handles bronze to gold and dbt also manages some gold tables, copy the Databricks Worklow `orchestration.job` file from this repo and paste it in your directory.

Your project structure should look like this:
```yml
.
├── README.md
├── databricks.yml
├── eurex_dbt
│   ├── README.md
│   ├── analyses
│   ├── dbt_project.yml
│   ├── logs
│   │   └── dbt.log
│   ├── macros
│   ├── models
│   │   ├── gold_eurex_top_movers.sql
│   │   └── schema.yml
│   ├── seeds
│   ├── snapshots
│   └── tests
├── logs
│   └── dbt.log
├── resources
│   ├── eurex_daily_stats_pipeline.pipeline.yml
│   └── orchestration.job.yml
└── src
    ├── 01_bronze
    │   └── bronze_eurex_daily_stats_pipeline.py
    ├── 02_silver
    │   ├── silver_eurex_daily_trading.sql
    │   └── silver_eurex_products.sql
    ├── 03_gold
    │   ├── gold_eurex.sql
    │   └── gold_eurex_product_performance.sql
   
```

### 10 Deploy the Bundle

1. Validate the bundle config before deploying:
   ```bash
   databricks bundle validate --profile gcp-workspace
   ```

2. Deploy to the development target:
   ```bash
   databricks bundle deploy --profile gcp-workspace