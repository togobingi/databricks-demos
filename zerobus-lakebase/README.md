# Zerobus Ingest — Quick Start Guide

Zerobus Ingest enables near real-time data ingestion into Delta tables via **gRPC** (SDKs), **REST API**, or **OpenTelemetry**. gRPC is best for high-throughput streaming; REST for stateless/low-frequency writes.

## Prerequisites

- Databricks workspace (AWS)
- A service principal with client ID & secret
- A Unity Catalog target table
- SDK: Python 3.9+ | Java 8+ | Go 1.21+ | Node.js 16+ | Rust 1.70+

## 1. Create Target Table

```sql

CREATE TABLE CATALOG.SCHEMA.trading_events (
  event_id STRING,
  timestamp_utc TIMESTAMP,
  instrument_isin STRING,
  instrument_name STRING,
  venue STRING,
  order_type STRING,
  side STRING,
  quantity INT,
  price STRING,
  order_status STRING,
  filled_quantity INT,
  fill_price DOUBLE,
  participant_id STRING,
  latency_ms INT,
  flag_suspicious BOOLEAN,
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
    from datetime import datetime, timedelta
    import random
    import uuid

    venues = ["XETRA", "FRA", "STU"]
    order_types = ["LIMIT", "MARKET"]
    sides = ["BUY", "SELL"]
    order_statuses = ["NEW", "PARTIALLY_FILLED", "FILLED", "CANCELLED"]
    instrument_isins = ["DE000BASF111", "DE000AAPL123", "DE000GOOG456"]
    instrument_names = ["BASF", "APPLE", "GOOGLE"]
    participant_ids = ["P1", "P2", "P3"]

    base_time = datetime.utcnow()

    for i in range(1000):
        record_dict = {
            "event_id": str(uuid.uuid4()),
            "timestamp_utc": int((base_time + timedelta(seconds=i)).timestamp() * 1_000_000),
            "instrument_isin": random.choice(instrument_isins),
            "instrument_name": random.choice(instrument_names),
            "venue": random.choice(venues),
            "order_type": random.choice(order_types),
            "side": random.choice(sides),
            "quantity": random.randint(1, 1000),
            "price": str(round(random.uniform(10, 1000), 2)),
            "order_status": random.choice(order_statuses),
            "filled_quantity": random.randint(0, 1000),
            "fill_price": round(random.uniform(10, 1000), 2),
            "participant_id": random.choice(participant_ids),
            "latency_ms": random.randint(1, 100),
            "flag_suspicious": random.choice([True, False]),
            "temp": random.randint(15, 35),
            "humidity": random.randint(30, 90)
        }
        offset = stream.ingest_record_offset(record_dict)

        # Optional: Wait for durability confirmation
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
