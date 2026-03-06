## Azure Function + Synapse Medallion Reference

This repository contains:

1. `azure_function/function_app.py`: Azure Function (HTTP trigger) that reads CSV from ADLS Gen2 and inserts records into a Synapse dedicated SQL pool table.
2. `synapse/pipelines/medallion_ingestion_pipeline.json`: Synapse pipeline template implementing Bronze, Silver, Gold, and Purview metadata tagging.
3. `synapse/triggers/bronze_ingestion_schedule_trigger.json`: Parameterized schedule trigger.

### Azure Function configuration

Set these application settings:

- `ADLS_ACCOUNT_URL` (example: `https://<storage-account>.dfs.core.windows.net`)
- `SYNAPSE_SQL_SERVER` (example: `<workspace>.sql.azuresynapse.net`)
- `SYNAPSE_SQL_DATABASE`
- `SYNAPSE_SQL_USER`
- `SYNAPSE_SQL_PASSWORD`
- `SYNAPSE_SQL_DRIVER` (optional, default `ODBC Driver 18 for SQL Server`)
- `INSERT_BATCH_SIZE` (optional, default `2000`)

### HTTP request sample

```json
{
  "fileSystem": "landing",
  "filePath": "sales/2026/03/01/orders.csv",
  "targetTable": "dbo.orders_bronze"
}
```
