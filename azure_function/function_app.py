import csv
import io
import logging
import os
import json
from typing import Iterable, List, Sequence

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient
import pyodbc

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing."""


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value


def _build_sql_connection() -> pyodbc.Connection:
    server = _required_env("SYNAPSE_SQL_SERVER")
    database = _required_env("SYNAPSE_SQL_DATABASE")
    username = _required_env("SYNAPSE_SQL_USER")
    password = _required_env("SYNAPSE_SQL_PASSWORD")
    driver = os.getenv("SYNAPSE_SQL_DRIVER", "ODBC Driver 18 for SQL Server")

    connection_string = (
        f"Driver={{{driver}}};"
        f"Server=tcp:{server},1433;"
        f"Database={database};"
        f"Uid={username};"
        f"Pwd={password};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(connection_string)


def _download_csv_bytes(file_system: str, file_path: str) -> bytes:
    account_url = _required_env("ADLS_ACCOUNT_URL")
    credential = DefaultAzureCredential()
    service = DataLakeServiceClient(account_url=account_url, credential=credential)

    fs_client = service.get_file_system_client(file_system=file_system)
    file_client = fs_client.get_file_client(file_path)
    return file_client.download_file().readall()


def _parse_csv(content: bytes) -> tuple[List[str], List[Sequence[str]]]:
    text_stream = io.StringIO(content.decode("utf-8-sig"))
    reader = csv.reader(text_stream)
    headers = next(reader, None)
    if not headers:
        raise ValueError("CSV file is empty or missing headers")

    rows = [tuple(row) for row in reader if any(cell.strip() for cell in row)]
    return headers, rows


def _chunk_rows(rows: Iterable[Sequence[str]], batch_size: int) -> Iterable[List[Sequence[str]]]:
    batch: List[Sequence[str]] = []
    for row in rows:
        batch.append(row)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def _insert_rows(table_name: str, columns: Sequence[str], rows: List[Sequence[str]]) -> int:
    if not rows:
        return 0

    placeholders = ", ".join("?" for _ in columns)
    quoted_columns = ", ".join(f"[{col}]" for col in columns)
    sql = f"INSERT INTO {table_name} ({quoted_columns}) VALUES ({placeholders})"
    batch_size = int(os.getenv("INSERT_BATCH_SIZE", "2000"))

    inserted = 0
    with _build_sql_connection() as conn:
        cursor = conn.cursor()
        cursor.fast_executemany = True

        for batch in _chunk_rows(rows, batch_size=batch_size):
            cursor.executemany(sql, batch)
            inserted += len(batch)

        conn.commit()

    return inserted


@app.route(route="ingest/csv-to-synapse", methods=["POST"])
def ingest_csv_to_synapse(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP payload example:
    {
      "fileSystem": "landing",
      "filePath": "sales/2026/03/01/orders.csv",
      "targetTable": "dbo.orders_bronze"
    }
    """
    try:
        payload = req.get_json()
        file_system = payload["fileSystem"]
        file_path = payload["filePath"]
        target_table = payload["targetTable"]

        csv_content = _download_csv_bytes(file_system=file_system, file_path=file_path)
        headers, rows = _parse_csv(csv_content)
        inserted = _insert_rows(table_name=target_table, columns=headers, rows=rows)

        response_body = {
            "status": "success",
            "targetTable": target_table,
            "sourcePath": f"{file_system}/{file_path}",
            "insertedRows": inserted,
        }
        return func.HttpResponse(
            body=json.dumps(response_body),
            status_code=200,
            mimetype="application/json",
        )

    except (ValueError, KeyError, ConfigurationError) as ex:
        logging.exception("Bad request or configuration issue.")
        return func.HttpResponse(json.dumps({"status": "error", "message": str(ex)}), status_code=400, mimetype="application/json")
    except Exception as ex:  # noqa: BLE001
        logging.exception("Unhandled ingestion failure.")
        return func.HttpResponse(json.dumps({"status": "error", "message": str(ex)}), status_code=500, mimetype="application/json")
