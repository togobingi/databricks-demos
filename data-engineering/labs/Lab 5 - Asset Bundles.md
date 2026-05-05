# 📦 Lab 5 – Databricks Asset Bundles (DABs)

## 🎯 Learning Objectives
By the end of this lab, you will:
- Install and authenticate the **Databricks CLI**
- Understand what a **Databricks Asset Bundle** is and why teams use them
- Generate a bundle definition from the existing Eurex pipeline using `bundle generate`
- Review the generated `databricks.yml` and understand its structure
- Deploy and run the bundle from the command line

## Introduction

**What are Asset Bundles?**

Databricks Asset Bundles (DABs) are the infrastructure-as-code approach for Databricks. Instead of clicking through the UI to configure jobs and pipelines, you define everything in a `databricks.yml` file — then deploy it to any workspace with a single command.

Benefits:
- **Version control**: your pipeline config lives in Git alongside your code
- **Environment promotion**: the same bundle deploys to dev, staging, and production
- **Repeatability**: no more "works on my laptop" pipeline configs

**How it fits the Eurex pipeline:**

The Eurex SDP pipeline and its orchestrating job are already defined in `databricks.yml` at the root of this repository. In this lab, you will see how that file was generated from an existing pipeline — which is the most common starting point.

---

## Instructions

### Step 0: Make a new directory on your local device
```bash
mkdir etl_pipeline
cd etl_pipeline
```

### Step 1: Install the Databricks CLI

> Skip this step if you already have the CLI installed. Check with `databricks --version`.

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
```

**Windows (PowerShell):**
```powershell
iex "& { $(irm https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh) }"
```

**Verify:**
```bash
databricks --version
```

---

### Step 2: Configure a Profile

A **profile** stores your workspace URL and authentication token so you don't pass them on every command.

1. Run the configure command:
   ```bash
   databricks configure --profile gcp-workspace
   ```

2. When prompted, enter:
   - **Databricks Host**: `https://WORKSPACE-ID.8.gcp.databricks.com`
   - **Token**: *(your personal access token — create one in User Settings → Developer → Access Tokens)*

3. Verify the connection:
   ```bash
   databricks workspace list / --profile gcp-workspace
   ```
   You should see your workspace root directories.


---
### Step 3: Create a Declarative Automation Bundle (DABs) project
In your directory, run `databricks bundle init --profile gcp-workspace`. This will prompt you to fill out some options:
   - Template to use:  Select `default-python`
   - Name of project: eurex_dabs
   - Choose no for the next options that follow
   - For catalog: input your Unity catalog name
   - For schema: select **no, I will customize the schema configuration later in databricks.yml**

You should now have an empty DABs project.

### Step 4: Generate a Bundle from the Existing Pipeline

The `bundle generate` command inspects a live pipeline or job and produces the YAML definition for you.

1. From the root of this repository, run the following. Replace the pipeline ID with your pipeline ID. You can find the pipeline ID in the pipeline **Settings** in the UI:

   ```bash
   databricks bundle generate pipeline \
     --existing-pipeline-id 2a424a12-1234-123e-bd89-e432b8890e4c \
     --profile gcp-workspace
   ```

2. This generates (or updates) `databricks.yml` with a `pipelines:` block for the Eurex DLT pipeline

3. Open the generated file and find the pipeline definition:

   ```yaml
   resources:
      pipelines:
         etl_dry_run_project:
            name: ETL dry run project
            configuration:
            "bad_rows": "('Product Settle Type','--')"
            libraries:
            - glob:
                  include: ../src/01_bronze/**
            - glob:
                  include: ../src/02_silver/**
            - glob:
                  include: ../src/03_gold/**
            catalog: main
            channel: CURRENT
            continuous: false
            environment:
            dependencies:
               - xlrd>=2.0.1
   ```

---

### Step 4: Understand the Bundle Structure

Review the full `databricks.yml` file at the root of this repository. Key sections:

| Section | What it does |
|---------|-------------|
| `bundle.name` | Unique name for this bundle |
| `workspace.host` | Target workspace URL |
| `variables` | Reusable values (catalog, schema, GCS path) |
| `resources.jobs` | Workflow job definitions |
| `resources.pipelines` | DLT pipeline definitions |
| `targets` | Environment-specific overrides (dev vs production) |

> 💡 In `development` mode, Databricks automatically prefixes all resource names with `[dev <your_username>]` so your dev resources don't collide with production ones.

---

### Step 5: Deploy the Bundle

1. Validate the bundle config before deploying:
   ```bash
   databricks bundle validate --profile gcp-workspace
   ```

2. Deploy to the development target:
   ```bash
   databricks bundle deploy --profile gcp-workspace
   ```

3. Check the deployed resources in the Databricks UI:
   - **Jobs & Pipelines** → find `[dev <username>] Eurex — Full Lakeflow Pipeline`

---

### Step 6:  Run the Pipeline via the CLI

Instead of clicking **Start** in the UI, trigger the run from the terminal:

```bash
databricks bundle run eurex_pipeline_runner --profile gcp-workspace
```

This runs the `eurex_pipeline_runner` pipeline defined in `databricks.yml`.


---

### (Optional) Step 7: Promote to Production

Examine the `production` target in `databricks.yml`:

```yaml
targets:
  production:
    mode: production
    workspace:
      root_path: /bundle/${bundle.name}/prod
```

In production mode:
- Resource names no longer have the `[dev]` prefix
- The bundle enforces stricter permissions and deployment settings

To deploy to production (you won't do this in the workshop, but this is the command):
```bash
databricks bundle deploy --target production --profile gcp-workspace
```

---

## Final Steps

If you run into issues, reference the full `databricks.yml` at the root of this repository — it contains the working configuration for all Eurex resources.

Useful CLI commands for troubleshooting:

```bash
# List deployed resources
databricks bundle summary --profile gcp-workspace

# Destroy dev resources (clean up after the workshop)
databricks bundle destroy --profile gcp-workspace
```

---

## What Happens Next?

You have completed all 5 labs. You have:

1. **Lab 1** — Ingested CSV files incrementally with AutoLoader and handled schema drift
2. **Lab 2** — Built a production-grade DLT pipeline with DQ expectations, filtering, and Gold aggregates
3. **Lab 3** — Packaged everything as an Asset Bundle deployable via CLI or CI/CD

The next step for a real-world deployment would be to connect this bundle to a **CI/CD pipeline** (GitHub Actions, Azure DevOps, etc.) so that every merge to `main` automatically deploys to production.

An optional but recommended step is to inlcude a dbt project in our pipeline.
