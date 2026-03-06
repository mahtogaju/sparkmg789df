# Enterprise Synapse Medallion Pipeline: Excel in ADLS Gen2 to Power BI

This repository contains a practical, end-to-end implementation pattern for an enterprise data pipeline using **GitHub + Azure Synapse Analytics + CI/CD**, designed for a source Excel file in **Azure Data Lake Storage Gen2 (ADLS Gen2)** and a serving layer in **Dedicated SQL Pool** for **Power BI**.

## What this example includes

- **Bronze**: Raw ingestion of Excel workbook from ADLS Gen2 into ADLS Bronze parquet and raw SQL landing table.
- **Silver**: Data quality and standardization transformations to curated parquet and SQL Silver table.
- **Gold**: Star-schema-style serving table in Dedicated SQL pool for Power BI semantic model.
- **Purview metadata tagging**: Script and process for catalog registration + governance tags.
- **Parameterized triggers**: Trigger definitions with dynamic window and file-name parameters.
- **GitHub CI/CD**: Workflow that validates and deploys Synapse artifacts and SQL scripts.

---

## Reference architecture

1. **Source**: `sales_orders.xlsx` lands in ADLS Gen2 path `raw/sales/orders/yyyy/MM/dd/`.
2. **Bronze pipeline** reads worksheet `Orders`, stores immutable parquet in `bronze/sales_orders/ingestion_date=.../`, and logs ingestion metadata.
3. **Silver pipeline** applies schema conformance, data type casting, null checks, deduplication, and writes to `silver/sales_orders/`.
4. **Gold pipeline** merges data into Dedicated SQL Pool table `dbo.FactSalesOrdersGold` and keeps dimensional surrogate key references.
5. **Power BI** connects to Dedicated SQL Pool and imports/reporting model is refreshed after Gold load.
6. **Purview** is updated with classifications and business metadata.
7. **CI/CD** promotes artifacts across environments (dev/test/prod) with environment-specific parameters.

---

## Repository layout

- `.github/workflows/synapse-cicd.yml` - CI/CD pipeline.
- `synapse/pipelines/` - Synapse pipeline JSON definitions.
- `synapse/triggers/` - parameterized trigger JSON.
- `synapse/datasets/` - datasets for ADLS and SQL assets.
- `synapse/linkedServices/` - linked service definitions.
- `synapse/sql/` - Bronze/Silver/Gold SQL DDL/DML scripts.
- `scripts/purview_register_and_tag.py` - metadata registration and tagging.
- `docs/runbook.md` - operational runbook and deployment steps.

---

## Environment parameters

Use environment variables or GitHub environment secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_SYNAPSE_WORKSPACE`
- `AZURE_RESOURCE_GROUP`
- `AZURE_DATA_LAKE_ACCOUNT`
- `AZURE_DATA_LAKE_CONTAINER`
- `DEDICATED_SQL_POOL`
- `PURVIEW_ACCOUNT`

---

## End-to-end flow execution

1. Commit to `main` or run workflow manually with target environment.
2. CI validates JSON and SQL templates.
3. CD publishes Synapse assets using workspace deployment task.
4. Trigger runs with runtime parameters:
   - `p_file_name` (default: `sales_orders.xlsx`)
   - `p_sheet_name` (default: `Orders`)
   - `p_window_start`, `p_window_end`
5. Bronze → Silver → Gold orchestration executes.
6. Purview script applies tags: `Domain=Sales`, `Confidentiality=Internal`, `PII=None`.
7. Optional post-load step calls Power BI dataset refresh API.

---

## Notes for production hardening

- Use private endpoints and managed VNET integration.
- Store secrets in Key Vault linked services only.
- Enable retry policies, alerts, and Azure Monitor dashboards.
- Add data quality assertions (Great Expectations / custom notebook tests).
- Implement schema drift strategy and backward-compatible contracts.

