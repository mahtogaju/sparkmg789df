#!/usr/bin/env python3
"""Register Synapse assets in Purview and apply governance tags."""

import argparse
import json
import os
import requests
from azure.identity import DefaultAzureCredential


def get_token() -> str:
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    token = credential.get_token("https://purview.azure.net/.default")
    return token.token


def upsert_entity(endpoint: str, token: str, payload: dict) -> dict:
    url = f"{endpoint}/catalog/api/atlas/v2/entity"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    response.raise_for_status()
    return response.json()


def add_tags(endpoint: str, token: str, guid: str, tags: list[str]) -> None:
    url = f"{endpoint}/catalog/api/atlas/v2/entity/guid/{guid}/classifications"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = [{"typeName": tag} for tag in tags]
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    response.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--purview-account", default=os.environ.get("PURVIEW_ACCOUNT"), required=False)
    parser.add_argument("--sql-server", required=True)
    parser.add_argument("--sql-db", required=True)
    parser.add_argument("--table", default="dbo.FactSalesOrdersGold")
    parser.add_argument("--tags", nargs="+", default=["Domain_Sales", "Confidentiality_Internal", "PII_None"])
    args = parser.parse_args()

    if not args.purview_account:
        raise ValueError("Purview account name is required via --purview-account or PURVIEW_ACCOUNT env var")

    endpoint = f"https://{args.purview_account}.purview.azure.com"
    token = get_token()

    qualified_name = f"mssql://{args.sql_server}/{args.sql_db}/{args.table}"
    entity = {
        "entity": {
            "typeName": "azure_sql_table",
            "attributes": {
                "qualifiedName": qualified_name,
                "name": args.table,
                "owner": "DataEngineering"
            }
        }
    }

    result = upsert_entity(endpoint, token, entity)
    guid = result.get("guidAssignments", {}).get("-100")
    if not guid:
        raise RuntimeError("Unable to resolve entity GUID from Purview response")

    add_tags(endpoint, token, guid, args.tags)
    print(f"Tagged {args.table} with {args.tags}")


if __name__ == "__main__":
    main()
