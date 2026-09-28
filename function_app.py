# coding: utf-8
"""
Azure Functions (Python v2) — Allianz VNet API demo.

HTTP trigger shape from Microsoft Learn:
  https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger
  https://learn.microsoft.com/en-us/samples/azure-samples/functions-quickstart-python-http-azd/functions-quickstart-python-azd/

VNet create: same begin_create_or_update call as the Azure-Samples files in
learn_samples/ (that GitHub repo was archived 22 Jun 2026). Current contract:
  https://learn.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.operations.virtualnetworksoperations?view=azure-python
Parameters use VirtualNetwork / AddressSpace / Subnet model classes because
azure-mgmt-network 33 rejects the archived sample's snake_case dict as ARM JSON.

Table create/query pattern from Azure SDK samples (verbatim pattern):
  learn_samples/sample_insert_delete_entities.py
  learn_samples/sample_query_table.py
  https://learn.microsoft.com/en-us/python/api/overview/azure/data-tables-readme?view=azure-python

Authentication (platform, little/no app code) — Microsoft Learn:
  https://learn.microsoft.com/en-us/azure/app-service/configure-authentication-provider-aad
  https://learn.microsoft.com/en-us/azure/app-service/configure-authentication-user-identities

Lines marked  # DEMO CHANGE  are the only intentional deviations from Learn/samples.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import azure.functions as func
from azure.core.exceptions import HttpResponseError, ResourceExistsError, ResourceNotFoundError
from azure.data.tables import TableClient
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import AddressSpace, Subnet, VirtualNetwork

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# DEMO CHANGE: in-memory store when STORAGE_CONNECTION is empty (local practice only)
_MEMORY_STORE: dict[str, dict] = {}


def _json_response(payload: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload, default=str),
        status_code=status_code,
        mimetype="application/json",
    )


def _caller_name(req: func.HttpRequest) -> str:
    """
    Easy Auth injects this header after Entra sign-in (Learn: user identities).
    Authorization = any authenticated user (assignment). Platform blocks anonymous
    when Easy Auth "Require authentication" is enabled.
    """
    # Learn: X-MS-CLIENT-PRINCIPAL-NAME
    name = req.headers.get("X-MS-CLIENT-PRINCIPAL-NAME")
    if name:
        return name
    # DEMO CHANGE: local-only label when Easy Auth is not present (func start)
    return "local-dev"


def _use_memory_store() -> bool:
    return not os.environ.get("STORAGE_CONNECTION", "").strip()


def _table_client() -> TableClient:
    """
    Pattern from azure-data-tables samples:
      TableClient.from_connection_string(conn_str, table_name)
      table_client.create_table()  # ignore if exists
    """
    conn = os.environ["STORAGE_CONNECTION"]
    table_name = os.environ.get("TABLE_NAME", "VnetCreations")
    table_client = TableClient.from_connection_string(conn, table_name)
    try:
        table_client.create_table()
    except HttpResponseError:
        # sample_insert_delete_entities.py: "Table already exists"
        pass
    except ResourceExistsError:
        pass
    return table_client


def _store_entity(entity: dict) -> None:
    if _use_memory_store():
        key = entity["RowKey"]
        if key in _MEMORY_STORE:
            raise ResourceExistsError("Entity already exists")
        _MEMORY_STORE[key] = entity
        return
    table_client = _table_client()
    table_client.create_entity(entity=entity)


def _list_entities() -> list[dict]:
    if _use_memory_store():
        return list(_MEMORY_STORE.values())
    table_client = _table_client()
    return list(table_client.query_entities(query_filter="PartitionKey eq 'vnet'"))


def _get_entity(name: str) -> dict:
    if _use_memory_store():
        if name not in _MEMORY_STORE:
            raise ResourceNotFoundError("Not found")
        return _MEMORY_STORE[name]
    table_client = _table_client()
    return table_client.get_entity(partition_key="vnet", row_key=name)


def _create_vnet_with_subnets(
    resource_group_name: str,
    vnet_name: str,
    location: str,
    address_prefixes: list[str],
    subnets: list[dict],
):
    """
    Same client + begin_create_or_update pattern as the archived Azure-Samples
    files and the current Learn API (VirtualNetworksOperations.begin_create_or_update).

    DEMO CHANGE: location / address_prefixes / subnets come from the HTTP body
    instead of hard-coded sample values. Subnet list shape is unchanged from
    manage_virtual_network_create.py:
      {"name": "...", "address_prefix": "..."}
    """
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID") or os.environ.get("SUBSCRIPTION_ID")
    if not subscription_id:
        raise ValueError(
            "Subscription ID not found. Set AZURE_SUBSCRIPTION_ID or SUBSCRIPTION_ID "
            "(same as manage_virtual_network_create.py)."
        )

    # Learn / sample: DefaultAzureCredential + NetworkManagementClient
    credential = DefaultAzureCredential()
    network_client = NetworkManagementClient(credential=credential, subscription_id=subscription_id)

    # Same fields as manage_virtual_network_create.py, represented by the
    # current SDK model classes. azure-mgmt-network 33 treats a plain dict as
    # raw ARM JSON, where the sample's snake_case keys are not valid.
    vnet_params = VirtualNetwork(
        location=location,
        address_space=AddressSpace(address_prefixes=address_prefixes),
        subnets=[
            Subnet(name=subnet["name"], address_prefix=subnet["address_prefix"])
            for subnet in subnets
        ],
    )

    logging.info("Creating virtual network %s in %s ...", vnet_name, resource_group_name)
    poller = network_client.virtual_networks.begin_create_or_update(
        resource_group_name,
        vnet_name,
        vnet_params,
    )
    # Sample uses .result(); continuation_token demo in create sample omitted for simplicity
    return poller.result()


def _entity_from_vnet(vnet, body: dict, created_by: str) -> dict:
    """Build a Table entity (PartitionKey/RowKey pattern from SDK table samples)."""
    subnet_ids = [s.id for s in (vnet.subnets or []) if getattr(s, "id", None)]
    return {
        "PartitionKey": "vnet",
        "RowKey": body["name"],
        "vnetId": vnet.id,
        "subnetIds": json.dumps(subnet_ids),
        "location": body["location"],
        "resourceGroup": body["resourceGroup"],
        "createdBy": created_by,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "requestJson": json.dumps(body),
    }


# ---------------------------------------------------------------------------
# HTTP triggers 
# ---------------------------------------------------------------------------


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Simple health endpoint (same idea as Learn HTTP GET sample)."""
    logging.info("Health check")
    return _json_response(
        {
            "status": "ok",
            "service": "allianz-vnet-api-demo",
            "dryRun": os.environ.get("DRY_RUN", "false").lower() == "true",
        }
    )


@app.route(route="vnets", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_vnet(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/vnets

    Learn HTTP POST pattern (get_json + validation + HttpResponse) from:
      functions-quickstart-python-http-azd httppost sample
    """
    logging.info("Processing POST /api/vnets")

    try:
        body = req.get_json()
    except ValueError:
        return _json_response({"error": "Invalid JSON in request body"}, 400)

    # DEMO CHANGE: required fields for this assignment
    name = body.get("name")
    location = body.get("location")
    address_space = body.get("addressSpace") or body.get("address_space")
    subnets_in = body.get("subnets")
    resource_group = body.get("resourceGroup") or body.get("resource_group")

    if not (
        isinstance(name, str)
        and isinstance(location, str)
        and isinstance(address_space, list)
        and address_space
        and isinstance(subnets_in, list)
        and len(subnets_in) >= 1
        and isinstance(resource_group, str)
    ):
        return _json_response(
            {
                "error": "Required: name, location, addressSpace[], subnets[], resourceGroup",
            },
            400,
        )

    # Map JSON to sample subnet objects: {"name", "address_prefix"}
    subnets = []
    for item in subnets_in:
        s_name = item.get("name")
        prefix = item.get("addressPrefix") or item.get("address_prefix")
        if not s_name or not prefix:
            return _json_response(
                {"error": "Each subnet needs name and addressPrefix"},
                400,
            )
        subnets.append({"name": s_name, "address_prefix": prefix})

    created_by = _caller_name(req)
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

    try:
        if dry_run:
           
            class _FakeSubnet:
                def __init__(self, sid: str):
                    self.id = sid

            class _FakeVnet:
                def __init__(self):
                    base = (
                        f"/subscriptions/dry-run/resourceGroups/{resource_group}"
                        f"/providers/Microsoft.Network/virtualNetworks/{name}"
                    )
                    self.id = base
                    self.subnets = [
                        _FakeSubnet(f"{base}/subnets/{s['name']}") for s in subnets
                    ]

            vnet = _FakeVnet()
        else:
            vnet = _create_vnet_with_subnets(
                resource_group_name=resource_group,
                vnet_name=name,
                location=location,
                address_prefixes=[str(x) for x in address_space],
                subnets=subnets,
            )

        entity = _entity_from_vnet(
            vnet,
            {
                "name": name,
                "location": location,
                "addressSpace": address_space,
                "subnets": [
                    {"name": s["name"], "addressPrefix": s["address_prefix"]} for s in subnets
                ],
                "resourceGroup": resource_group,
            },
            created_by,
        )
        entity["dryRun"] = dry_run

        # Persist — sample_insert_delete_entities.py create_entity pattern
        try:
            _store_entity(entity)
        except ResourceExistsError:
            # Same handling idea as the SDK sample
            return _json_response(
                {"error": f"Entity for VNet '{name}' already exists. Use GET to retrieve."},
                409,
            )

        return _json_response(
            {
                "name": name,
                "vnetId": entity["vnetId"],
                "subnetIds": json.loads(entity["subnetIds"]),
                "location": location,
                "resourceGroup": resource_group,
                "createdBy": created_by,
                "createdAt": entity["createdAt"],
                "dryRun": dry_run,
            },
            201,
        )
    except Exception as exc:
        logging.exception("create_vnet failed")
        return _json_response({"error": str(exc)}, 500)


@app.route(route="vnets", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def list_vnets(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/vnets

    Query pattern from learn_samples/sample_query_table.py:
      table_client.query_entities(query_filter=...)
    """
    logging.info("Processing GET /api/vnets")
    _ = _caller_name(req)

    try:
        # sample_query_table.py: query_entities(query_filter=...)
        queried = _list_entities()
        items = []
        for entity in queried:
            items.append(
                {
                    "name": entity.get("RowKey"),
                    "vnetId": entity.get("vnetId"),
                    "subnetIds": json.loads(entity.get("subnetIds") or "[]"),
                    "location": entity.get("location"),
                    "resourceGroup": entity.get("resourceGroup"),
                    "createdBy": entity.get("createdBy"),
                    "createdAt": entity.get("createdAt"),
                    "dryRun": entity.get("dryRun", False),
                }
            )
        return _json_response({"count": len(items), "items": items})
    except Exception as exc:
        logging.exception("list_vnets failed")
        return _json_response({"error": str(exc)}, 500)


@app.route(route="vnets/{name}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_vnet(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/vnets/{name}

    get_entity pattern from Azure Data Tables SDK (companion to insert sample).
    """
    name = req.route_params.get("name")
    logging.info("Processing GET /api/vnets/%s", name)
    _ = _caller_name(req)

    if not name:
        return _json_response({"error": "name is required"}, 400)

    try:
        try:
            entity = _get_entity(name)
        except ResourceNotFoundError:
            return _json_response({"error": f"VNet record '{name}' not found"}, 404)

        return _json_response(
            {
                "name": entity.get("RowKey"),
                "vnetId": entity.get("vnetId"),
                "subnetIds": json.loads(entity.get("subnetIds") or "[]"),
                "location": entity.get("location"),
                "resourceGroup": entity.get("resourceGroup"),
                "createdBy": entity.get("createdBy"),
                "createdAt": entity.get("createdAt"),
                "dryRun": entity.get("dryRun", False),
            }
        )
    except Exception as exc:
        logging.exception("get_vnet failed")
        return _json_response({"error": str(exc)}, 500)
