# 🏦 Eurex Data Engineering Workshop — Introduction

## Welcome

In this workshop you will build a real-world data pipeline using **Eurex** daily statistics data. You will work through 6 progressive exercises that mirror how data platform/engineering teams operate at financial institutions.


---

## 🎯 What You Will Build

| Lab | Topic | Key Skill |
|-----|-------|-----------|
| **Lab 1** | AutoLoader & Schema Evolution | Incremental file ingestion, handling schema drift |
| **Lab 2** | Bronze Lakeflow Pipeline | Reading data from a Unity Catalog Volume |
| **Lab 3** | Silver Lakeflow Pipeline | Transforming and cleaning data |
| **Lab 4** | Gold Lakeflow Pipeline | Building aggregate tables for downstream consumption |
| **Lab 5** | Using dbt to build Gold tables |
| **Lab 6** | Asset Bundles (DABs) | Infrastructure-as-code, CI/CD for Databricks |

---

## Prerequisites

Before starting, confirm you have:

- [ ] Access to the Databricks workspace: `https://<WORKSPACE-ID>.gcp.databricks.com`
- [ ] Your assigned **Catalog**: `main` (example)
- [ ] Your assigned **Schema**: `default` (example)
- [ ] The Eurex XLS file: `dailystat_20260428.xls` (You can find the file [here](https://www.eurex.com/ex-en/data/statistics/trading-statistics). **Please download the dataset for April 28**)
- [ ] Databricks CLI installed (needed for Lab 5 & 6 — instructions provided in that lab)



## About the Data

**Eurex Daily Statistics** is a daily report published by Deutsche Börse covering order book activity across Europe's largest derivatives exchange.


Key columns: `product_id`, `product_name`, `traded_contracts`, `volume_eur`, `pc_ratio`, `open_interest_prev_day`.

---

## 🗺️ Architecture Overview

**Bronze** — Raw ingestion: all sheets parsed as strings, nothing dropped.  
**Silver** — Typed, cleaned, DQ-validated. Bad rows captured by expectations.  
**Gold** — Business-ready aggregates: top products, segment volume, market sentiment.

## What Happens Next?

Proceed to **Lab 1 — AutoLoader & Schema Evolution** to get hands-on with incremental file ingestion before tackling the full Eurex pipeline in Lab 2.
