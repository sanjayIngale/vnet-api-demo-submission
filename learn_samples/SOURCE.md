# Official sample sources

Microsoft copyright / MIT License headers are retained inside each file.

## Provenance samples 

| File | Source | Status |
|------|--------|--------|
| `manage_virtual_network.py` | https://github.com/Azure-Samples/azure-samples-python-management/blob/main/samples/network/virtual_network/manage_virtual_network.py | Archived 22 Jun 2026 |
| `manage_virtual_network_create.py` | https://github.com/Azure-Samples/azure-samples-python-management/blob/main/samples/network/virtual_network/manage_virtual_network_create.py | Archived 22 Jun 2026 |
| `manage_subnet.py` | https://github.com/Azure-Samples/azure-samples-python-management/blob/main/samples/network/virtual_network/manage_subnet.py | Archived 22 Jun 2026 |
| `sample_insert_delete_entities.py` | https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/tables/azure-data-tables/samples/sample_insert_delete_entities.py | Current |
| `sample_query_table.py` | https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/tables/azure-data-tables/samples/sample_query_table.py | Current |

## Current Microsoft references (what the running code follows)

| Capability | Current documentation |
|------------|------------------------|
| `NetworkManagementClient` | https://learn.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.networkmanagementclient?view=azure-python |
| `begin_create_or_update` | https://learn.microsoft.com/en-us/python/api/azure-mgmt-network/azure.mgmt.network.operations.virtualnetworksoperations?view=azure-python |
| Network SDK package | https://learn.microsoft.com/en-us/python/api/overview/azure/mgmt-network-readme?view=azure-python |
| Table `create_entity` / `query_entities` | https://learn.microsoft.com/en-us/python/api/overview/azure/data-tables-readme?view=azure-python |
| Table samples (Learn) | https://learn.microsoft.com/en-us/samples/azure/azure-sdk-for-python/tables-samples/ |
| Functions HTTP trigger (Python v2) | https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger |
| Functions HTTP azd quickstart | https://learn.microsoft.com/en-us/samples/azure-samples/functions-quickstart-python-http-azd/functions-quickstart-python-azd/ |
| Easy Auth + Microsoft Entra | https://learn.microsoft.com/en-us/azure/app-service/configure-authentication-provider-aad |
| Caller identity headers | https://learn.microsoft.com/en-us/azure/app-service/configure-authentication-user-identities |

## How this demo uses them

`function_app.py` keeps the same SDK *calls* (`DefaultAzureCredential`,
`NetworkManagementClient`, `begin_create_or_update`, `TableClient.create_entity`,
`query_entities`, `get_entity`).

