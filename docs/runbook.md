# Operational Runbook

## 1) Initial setup

1. Create ADLS Gen2 container `landing` with folders:
   - `raw/sales/orders/`
   - `bronze/sales_orders/`
   - `silver/sales_orders/`
2. Upload sample file `sales_orders.xlsx` into raw path.
3. Create dedicated SQL pool database objects using scripts in `synapse/sql/`.
4. Create Purview classifications (`Domain_Sales`, `Confidentiality_Internal`, `PII_None`) if not already present.

## 2) Pipeline deployment

1. Configure GitHub environment secrets.
2. Trigger workflow `synapse-cicd` with environment input (`dev`, `test`, `prod`).
3. Validate deployed artifacts in Synapse Studio.

## 3) Trigger configuration

- Publish `trg_master_hourly_param` and set to Started.
- Override runtime parameters as needed for backfill.

## 4) Data quality checkpoints

- Bronze row count >= source worksheet row count.
- Silver rejects are logged and monitored.
- Gold load has no duplicate `(OrderId, ProductId)`.

## 5) Power BI

1. Connect to dedicated SQL pool table `dbo.FactSalesOrdersGold`.
2. Build semantic model measures (Revenue, Average Order Value, Orders Count).
3. Schedule refresh aligned with trigger completion SLA.
