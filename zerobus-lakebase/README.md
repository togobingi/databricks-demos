# Zerobus Ingest — Quick Start Guide

Zerobus Ingest enables near real-time data ingestion into Delta tables via **gRPC** (SDKs), **REST API**, or **OpenTelemetry**. gRPC is best for high-throughput streaming; REST for stateless/low-frequency writes.

## Prerequisites

- Databricks workspace (AWS)
- A service principal with client ID & secret
- A Unity Catalog target table
- SDK: Python 3.9+ | Java 8+ | Go 1.21+ | Node.js 16+ | Rust 1.70+

## 1. Create Target Table

```sql
CREATE TABLE main.default.air_quality (
    device_name STRING,
    temp INT,
    humidity LONG
);
```

## 2. Configure Service Principal Permissions

```sql
GRANT USE CATALOG ON CATALOG main TO `<service-principal-uuid>`;
GRANT USE SCHEMA ON SCHEMA main.default TO `<service-principal-uuid>`;
GRANT MODIFY, SELECT ON TABLE main.default.air_quality TO `<service-principal-uuid>`;
```

> **Note:** `MODIFY` + `SELECT` are required even if `ALL PRIVILEGES` is already granted.

## 3. Get Your Connection Details

From your workspace URL `https://dbc-a1b2c3d4-e5f6.cloud.databricks.com/?o=1234567890123456`:

| Parameter | Value |
|-----------|-------|
| `SERVER_ENDPOINT` | `https://<workspace-id>.zerobus.<region>.cloud.databricks.com` |
| `WORKSPACE_URL` | `https://dbc-a1b2c3d4-e5f6.cloud.databricks.com` |
| `TABLE_NAME` | `main.default.air_quality` |

## 4. Ingest Data

### Python

```bash
pip install databricks-zerobus-ingest-sdk
```

```python
from zerobus.sdk.sync import ZerobusSdk
from zerobus.sdk.shared import RecordType, StreamConfigurationOptions, TableProperties

sdk = ZerobusSdk(SERVER_ENDPOINT, WORKSPACE_URL)
stream = sdk.create_stream(
    CLIENT_ID, CLIENT_SECRET,
    TableProperties(TABLE_NAME),
    StreamConfigurationOptions(record_type=RecordType.JSON),
)

try:
    for i in range(100):
        record = {"device_name": f"sensor-{i}", "temp": 20 + i % 15, "humidity": 50 + i % 40}
        offset = stream.ingest_record_offset(record)
    stream.wait_for_offset(offset)
finally:
    stream.close()
```

### REST API (Beta)

```bash
# Get OAuth token
export OAUTH_TOKEN=$(curl -X POST \
  -u "$CLIENT_ID:$CLIENT_SECRET" \
  -d "grant_type=client_credentials&scope=all-apis" \
  -d "resource=api://databricks/workspaces/$WORKSPACE_ID/zerobusDirectWriteApi" \
  "$WORKSPACE_URL/oidc/v1/token" | jq -r '.access_token')

# Ingest records
curl -X POST "$ZEROBUS_ENDPOINT/zerobus/v1/tables/main.default.air_quality/insert" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OAUTH_TOKEN" \
  -d '[{"device_name":"sensor-1","temp":28,"humidity":60}]'
```

> OAuth tokens expire hourly. Body must be a JSON array of objects.

## Error Handling (Optional Callback)

```python
from zerobus.sdk.shared import AckCallback

class MyCallback(AckCallback):
    def on_ack(self, offset): print(f"Confirmed: {offset}")
    def on_error(self, offset, err): print(f"Failed {offset}: {err}")

options = StreamConfigurationOptions(record_type=RecordType.JSON, ack_callback=MyCallback())
```

## Which Interface Should I Use?

| Interface | Best For |
|-----------|----------|
| **gRPC (SDKs)** | High-volume streaming — persistent connections, up to 40x throughput (Python via Rust) |
| **REST API** | Low-frequency device fleets — stateless, simple HTTP |
| **OTLP** | Environments already using OpenTelemetry for traces/logs/metrics |
