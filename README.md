# Allianz demo — Azure VNet API (Learn-based)

Azure Functions (Python) API that **creates a VNet with multiple subnets**,
**stores** results in **Table Storage**, and **retrieves** them.
Auth: **Easy Auth + Microsoft Entra**. Authorization: **any authenticated user**.

Built from **Microsoft Learn / Azure Samples code**, with only assignment-needed
changes.


## Layout

```text
allianz-vnet-api-demo/
├── function_app.py              # HTTP API (Learn Functions + wired samples)
├── learn_samples/               # Official samples DOWNLOADED VERBATIM
│   ├── manage_virtual_network.py
│   ├── manage_virtual_network_create.py
│   ├── manage_subnet.py
│   ├── sample_insert_delete_entities.py
│   ├── sample_query_table.py
│   └── SOURCE.md
├── host.json
├── requirements.txt
├── local.settings.json.example
├── postman/                     # Importable collection + safe environment
│   ├── Allianz-VNet-API.postman_collection.json
│   └── Allianz-VNet-API.postman_environment.json
├── infra/
│   └── authsettingsV2.json      # Easy Auth v2 shape; placeholder IDs
└── docs/
    ├── architecture.md
    └── api.md
```

---

## Quick start (local dry-run)

```powershell
cd allianz-vnet-api-demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy local.settings.json.example local.settings.json
func start
```

Import the files under `postman/`, select **Allianz VNet API - Demo**, and run
the **Local dry-run** folder. Full Postman steps:
[docs/POSTMAN-STEP-BY-STEP.md](docs/POSTMAN-STEP-BY-STEP.md).

Azure deploy and Easy Auth:
[docs/NEW-COMPUTER-SETUP.md](docs/NEW-COMPUTER-SETUP.md).

Postman is the primary demonstration client. Azure CLI is used only for setup
and to obtain a short-lived Entra bearer token.

---

## Official sources (summary)

Full table, including archived vs current: [learn_samples/SOURCE.md](learn_samples/SOURCE.md).

- VNet **current API**: [`begin_create_or_update`](https://learn.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.operations.virtualnetworksoperations?view=azure-python)
- VNet **provenance sample** (archived 22 Jun 2026): [Azure-Samples python-management](https://github.com/Azure-Samples/azure-samples-python-management/tree/main/samples/network/virtual_network)
- Tables: [Learn tables samples](https://learn.microsoft.com/en-us/samples/azure/azure-sdk-for-python/tables-samples/)
- Functions HTTP: [Learn HTTP trigger](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger)
- Easy Auth: [Configure Entra](https://learn.microsoft.com/en-us/azure/app-service/configure-authentication-provider-aad)

---

## Assignment mapping

| Requirement | How |
|-------------|-----|
| Azure API | Azure Functions |
| VNet + multiple subnets | Sample `begin_create_or_update` + subnet list |
| Store results | Table `create_entity` |
| Retrieve | `query_entities` / `get_entity` |
| Auth | Easy Auth (Entra) |
| AuthZ open to authenticated users | No app roles; Require authentication only |
| Python | Yes |
| Demonstration client | Importable Postman collection |
| GitHub docs | This repo |

---
