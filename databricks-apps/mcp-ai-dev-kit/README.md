# mcp-ai-dev-kit

A Databricks App that serves the [Databricks AI Dev Kit](https://github.com/databricks-solutions/ai-dev-kit) to all workspace users. It gives all workspace users access to the included tools and skills through Genie Code — without anyone needing to install the AI Dev Kit locally or have a Claude subscription.

When deployed (or redeployed), the app pulls the latest code from GitHub and:

1. **Distributes skills to the workspace** — uploads all AI Dev Kit skills to `Workspace/.assistant/skills/` so Genie Code can use them natively 
2. **Serves MCP tools over HTTP** — exposes all AI Dev Kit tools as a custom MCP server for Genie Code

**App name:** `mcp-ai-dev-kit` — find it under **Compute > Apps** in the workspace, or in **Genie Code Settings > MCP Servers** when adding a server.

## Architecture

![Architecture Diagram](architecture.png)

### How It Works

On startup, the app:

1. `git clone --depth 1` pulls the latest AI Dev Kit from GitHub (~3-5s)
2. **Distributes skills** from three sources to `Workspace/.assistant/skills/`:
   - Databricks skills (from the cloned repo)
   - MLflow skills (fetched from [mlflow/skills](https://github.com/mlflow/skills))
   - APX skills (fetched from [databricks-solutions/apx](https://github.com/databricks-solutions/apx))
3. Imports the FastMCP server, auto-registering all tools via `@mcp.tool` decorators
4. Registers skills as MCP prompts for non-native clients
5. `mcp.http_app()` creates a stateless Starlette ASGI app with CORS middleware
6. uvicorn serves the MCP endpoint at `/mcp` on port 8000

Every redeploy starts a fresh container with a new clone — always the latest tools and skills.

### Two Ways Genie Code Benefits

| Capability | How It Works | MCP Needed? |
|-----------|-------------|-------------|
| **Skills** (instructions, patterns, best practices) | Uploaded to `Workspace/.assistant/skills/` — Genie Code loads them natively and contextually | No |
| **Tools** (executable functions like `execute_sql`) | Served at `/mcp` via MCP Streamable HTTP | Yes |

**For Genie Code users:** Skills are the primary value. Genie Code already has native execution capabilities (SQL, compute, etc.), so the MCP tools are mostly useful for non-native clients.

**For Claude Code / Cursor users:** Both skills (as MCP prompts) and tools are available via the `/mcp` endpoint.

### Protocol Stack

MCP (Model Context Protocol) is a JSON-RPC 2.0 protocol. Streamable HTTP is its transport layer:

```
Client (Claude Code)                         Server (this app)
        |                                            |
        |  POST /mcp                                 |
        |  {"jsonrpc":"2.0",                         |
        |   "method":"tools/call",                   |
        |   "params":{"name":"execute_sql",...}}      |
        |  ----------------------------------------> |
        |                                            |
        |  200 OK                                    |
        |  {"jsonrpc":"2.0",                         |
        |   "result":{"content":[...]}}              |
        |  <---------------------------------------- |
```

No FastAPI wrapper is used. FastMCP's `http_app()` creates a Starlette ASGI app directly. Per [Genie Code MCP docs](https://docs.databricks.com/aws/en/genie-code/mcp), the app is configured as stateless (`stateless_http=True`) with CORS enabled.

### Authentication

The Databricks Apps platform automatically injects service principal credentials. The AI Dev Kit's auth module detects these and uses OAuth M2M to call Databricks APIs. No custom auth code is needed.

## What's Distributed

### Skills (uploaded to workspace)

Skills are uploaded to `Workspace/.assistant/skills/` on every deploy. Genie Code loads them automatically and contextually — they don't bloat the context window. Users can also invoke them with `@` mentions.

**Databricks skills** (from [ai-dev-kit](https://github.com/databricks-solutions/ai-dev-kit)):

| Skill | What It Teaches |
|-------|----------------|
| `databricks-aibi-dashboards` | Creating AI/BI Lakeview dashboards |
| `databricks-spark-declarative-pipelines` | Building Lakeflow data pipelines |
| `databricks-model-serving` | Deploying ML models and AI agents |
| `databricks-vector-search` | Building RAG and semantic search |
| `databricks-dbsql` | Advanced SQL features, stored procedures |
| `databricks-jobs` | Creating and managing workflow jobs |
| `databricks-unity-catalog` | System tables, volumes, lineage |
| `databricks-genie` | Creating Genie Spaces for natural language SQL |
| `databricks-agent-bricks` | Knowledge Assistants, Genie Spaces, Supervisor Agents |
| `databricks-ai-functions` | Built-in AI functions in SQL/PySpark |
| `databricks-app-python` | Building Python Databricks Apps |
| `databricks-bundles` | Declarative Automation Bundles (CI/CD) |
| `databricks-iceberg` | Apache Iceberg tables and interop |
| `databricks-metric-views` | Governed business metrics in YAML |
| `databricks-mlflow-evaluation` | MLflow 3 GenAI agent evaluation |
| `databricks-python-sdk` | Databricks SDK, Connect, CLI |
| `databricks-spark-structured-streaming` | Spark Structured Streaming |
| `databricks-synthetic-data-gen` | Generating realistic test data |
| `databricks-execution-compute` | Code execution, compute management |
| `databricks-docs` | Documentation reference lookup |
| `databricks-config` | Workspace connections and authentication |
| `databricks-lakebase-autoscale` | Lakebase Autoscaling patterns |
| `databricks-lakebase-provisioned` | Lakebase Provisioned patterns |
| `databricks-unstructured-pdf-generation` | PDF generation for test/demo data |
| `databricks-zerobus-ingest` | Real-time ingestion via gRPC |
| `spark-python-data-source` | Custom Spark data source connectors |

**MLflow skills** (from [mlflow/skills](https://github.com/mlflow/skills)):

| Skill | What It Teaches |
|-------|----------------|
| `agent-evaluation` | End-to-end agent evaluation workflow |
| `analyze-mlflow-chat-session` | Debug multi-turn conversations |
| `analyze-mlflow-trace` | Analyze MLflow traces |
| `instrumenting-with-mlflow-tracing` | Add tracing instrumentation |
| `mlflow-onboarding` | Getting started with MLflow |
| `querying-mlflow-metrics` | Query MLflow metrics |
| `retrieving-mlflow-traces` | Retrieve and inspect traces |
| `searching-mlflow-docs` | Search MLflow documentation |

**APX skills** (from [databricks-solutions/apx](https://github.com/databricks-solutions/apx)):

| Skill | What It Teaches |
|-------|----------------|
| `databricks-app-apx` | Building Databricks Apps with React/Next.js (APX framework) |

### MCP Tools (served at `/mcp`)

All AI Dev Kit tools are exposed as a custom MCP server:

| Category | Examples |
|----------|---------|
| SQL & Data | `execute_sql`, `execute_sql_multi`, `get_table_stats_and_schema` |
| Compute | `list_compute`, `manage_cluster`, `manage_sql_warehouse` |
| Jobs | `manage_jobs`, `manage_job_runs` |
| Pipelines | `create_or_update_pipeline`, `run_pipeline`, `get_pipeline_events` |
| Dashboards | `create_or_update_dashboard`, `publish_dashboard` |
| Model Serving | `query_serving_endpoint`, `list_serving_endpoints` |
| AI Agents | `manage_ka` (Knowledge Assistants), `manage_mas` (Supervisor Agents) |
| Unity Catalog | `manage_uc_objects`, `manage_uc_grants`, `manage_uc_tags`, `manage_uc_sharing` |
| Vector Search | `create_or_update_vs_index`, `query_vs_index` |
| Genie Spaces | `create_or_update_genie`, `ask_genie` |
| Lakebase | `create_or_update_lakebase_database`, `generate_lakebase_credential` |
| Files & Volumes | `upload_to_volume`, `download_from_volume`, `upload_to_workspace` |
| Apps | `create_or_update_app`, `get_app` |
| Metrics | `manage_metric_views` |

## Connecting

### Genie Code (skills — no setup needed)

Skills are automatically available after the app is deployed. Genie Code loads them contextually when relevant. Users can also invoke them with `@skill-name`.

### Genie Code (MCP tools — optional)

If you also want Genie Code to use the MCP tools:

1. Open Genie Code Settings (gear icon)
2. Under **MCP Servers**, click **Add Server**
3. Select `mcp-ai-dev-kit` from the Databricks App list
4. Choose which tools to enable (max 15 per server)
5. Click **Save**

> **Note:** Genie Code has native execution capabilities, so MCP tools may be redundant for most use cases. The skills (distributed automatically) provide the primary value.

### Claude Code / Cursor / Other MCP Clients

```json
{
  "mcpServers": {
    "databricks-ai-dev-kit": {
      "url": "https://<app-url>/mcp",
      "transport": "streamable-http"
    }
  }
}
```

### Programmatically

```python
from databricks_mcp import DatabricksMCPClient
from databricks.sdk import WorkspaceClient

workspace_client = WorkspaceClient(profile="<your-profile>")
mcp_client = DatabricksMCPClient(
    server_url="https://<app-url>/mcp",
    workspace_client=workspace_client,
)
tools = mcp_client.list_tools()
```

## Deployment

### Method 1: Skills Notebook (Quickest — No App Required)

If you only need the **Databricks skills** for Genie Code (and don't need the MCP tools served over HTTP for non-native clients), this is the fastest path. The notebook fetches the latest skills directly from GitHub and uploads them to your personal workspace skills folder. No app deployment, no service principal, no UC grants.

1. Clone this repo as a **Git Folder** in the workspace
2. Open `add_skills_from_ai_dev_kit.ipynb`
3. Attach to any cluster and **Run All**
4. The notebook installs each skill into `/Workspace/Users/<you>/.assistant/skills/<skill-name>/` and prints a per-skill progress log

Re-run the notebook any time to pull the latest version of each skill from GitHub.

> **Scope of this method:** Installs the **26 Databricks skills only**, scoped to your user. It does *not* install MLflow or APX skills, and it does *not* serve MCP tools. For full coverage (all three skill sources, MCP tools served at `/mcp`, workspace-wide skill distribution), use Method 2.

### Method 2: Databricks CLI (Full App Deployment)

#### Prerequisites

- Databricks CLI authenticated to the target workspace
- The target workspace must support Databricks Apps

#### First-Time Deploy

```bash
# Authenticate
databricks auth login --host https://<workspace-url>

# Create the app (mcp- prefix required for Genie Code discovery)
databricks apps create mcp-ai-dev-kit

# Sync source files to workspace
DBUSER=$(databricks current-user me | jq -r .userName)
databricks sync ./mcp-ai-dev-kit "/Users/$DBUSER/mcp-ai-dev-kit"

# Deploy
databricks apps deploy mcp-ai-dev-kit \
  --source-code-path "/Workspace/Users/$DBUSER/mcp-ai-dev-kit"
```

### Redeploy (Pull Latest Skills + Tools)

```bash
databricks apps deploy mcp-ai-dev-kit \
  --source-code-path "/Workspace/Users/$DBUSER/mcp-ai-dev-kit"
```

Each redeploy starts a fresh container that clones the latest code from GitHub and re-distributes all skills to the workspace.

### Grant Data Access

The app's service principal needs Unity Catalog permissions to access data on behalf of users (required for MCP tools, not for skills):

```sql
-- Find the SP client ID from: databricks apps get mcp-ai-dev-kit
GRANT USE CATALOG ON CATALOG <catalog> TO `<sp-client-id>`;
GRANT USE SCHEMA ON SCHEMA <catalog>.<schema> TO `<sp-client-id>`;
GRANT SELECT ON SCHEMA <catalog>.<schema> TO `<sp-client-id>`;
```

## File Structure

```
mcp-ai-dev-kit/
├── README.md                          # This document
├── architecture.png                   # Architecture diagram
├── add_skills_from_ai_dev_kit.ipynb   # Skills-only installer (run inside Databricks)
├── app.yaml                           # Databricks App config (uvicorn command + env vars)
├── main.py                            # Clone repo, distribute skills, register MCP tools, serve HTTP
└── requirements.txt                   # Combined dependencies from AI Dev Kit
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Skills distributed to workspace | Genie Code reads skills natively from `Workspace/.assistant/skills/` — no MCP overhead, no timeouts |
| Skills from 3 sources | Databricks (ai-dev-kit), MLflow (mlflow/skills), APX (databricks-solutions/apx) — complete coverage |
| MCP tools also served | Non-native clients (Claude Code, Cursor) need MCP for tool execution |
| No Lakebase | Not GA on GCP. App is stateless — no database needed. |
| No FastAPI | FastMCP's `http_app()` creates a Starlette ASGI app directly. FastAPI would add a redundant layer. |
| Shallow git clone at startup | Simple, zero-dependency way to always get latest code. ~3-5s cold start. |
| `stateless_http=True` | Required by Genie Code per [docs](https://docs.databricks.com/aws/en/genie-code/mcp). |
| CORS scoped to workspace | Uses `DATABRICKS_HOST` to restrict CORS origins to the workspace URL. |
| Best-effort skill distribution | Skill upload failures are logged but don't prevent the app from starting. |
