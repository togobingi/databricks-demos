# dbt Docs on Databricks Apps

A Databricks asset bundle project that deploys dbt documentation as a web application on Databricks.

## Overview

This project sets up an integrated solution for:
- Running dbt commands (dependencies, runs, and documentation generation) on Databricks
- Deploying the generated dbt docs as a web application accessible within Databricks
- Managing infrastructure via Databricks Asset Bundles (DAB)

## Project Structure

```
dbt-docs-databricks-app/
├── asset-bundles/              # Databricks Asset Bundle configuration
│   ├── databricks.yml          # Main bundle configuration
│   └── resources/
│       └── job.yml             # Job and app resource definitions
└── databricks-apps/            # Web application code
    ├── app.yaml                # App deployment configuration
    ├── main.py                 # FastAPI application server
    └── requirements.txt        # Python dependencies
```

## Components

### Asset Bundles (`asset-bundles/`)

The Databricks Asset Bundle defines:

- **SQL Warehouse**: An auto-scaling "dbt SQL Warehouse" configured for running dbt commands
- **dbt Job** (`dbt_docs_test`): 
  - Runs `dbt deps`, `dbt run`, and `dbt docs generate` commands
  - Targets the `dbdemos_dbt_retail` schema
  - Uses the configured SQL warehouse and main catalog
  - Performance optimized with queue support
- **Databricks App** (`dbt_docs_apps`):
  - Deploys the generated dbt documentation
  - Serves the app from the dbt target path
  - Links to the dbt job for resource management

### Databricks App (`databricks-apps/`)

A FastAPI-based web application that:
- Serves the dbt documentation as a static site
- Routes the root path (`/`) to `index.html`
- Mounts all other static assets from the `root` directory
- Runs on port 8080

## Prerequisites

- Databricks workspace with API credentials configured
- dbt-databricks installed (version >= 1.0.0, < 2.0.0)
- Python 3.8 or higher
- Databricks CLI installed and configured

## Configuration

Before deployment, update these variables in `asset-bundles/databricks.yml`:

```yaml
variables:
  dbt_target_path: "[DBT-TARGET-PATH]"           # Path to dbt target directory
  dbt_project_directory: "[DBT-PROJECT-DIRECTORY]"  # Path to dbt project
```

Optionally configure your workspace:

```yaml
workspace:
  host: https://your-workspace.databricks.com
```

## Deployment

1. Validate the bundle configuration:
   ```bash
   databricks bundle validate
   ```

2. Deploy the assets:
   ```bash
   databricks bundle deploy
   ```

3. Run the dbt job:
   ```bash
   databricks bundle run dbt_docs_test
   ```

4. Access the deployed app from your Databricks workspace

## Dependencies

**Python packages** (for the web app):
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server

**dbt packages** (managed via job environment):
- `dbt-databricks>=1.0.0,<2.0.0` - dbt adapter for Databricks

## Running Locally

To run the FastAPI app locally for development:

```bash
cd databricks-apps/
pip install -r requirements.txt
uvicorn app:app --reload
```

Then navigate to `http://localhost:8000`

## Notes

- The SQL warehouse auto-stops after 10 minutes of inactivity
- The job uses serverless compute capability for cost efficiency
- Static files should be generated in the root directory
- The app mounts the entire target directory, making all assets accessible


