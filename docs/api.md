# API

Deployed base URL (replace with your Function App hostname):

```text
https://<function-app>.azurewebsites.net
```

All deployed endpoints require a Microsoft Entra bearer token validated by
Easy Auth. Local `func start` dry-run requests do not require a token because
the local host does not run the Azure Easy Auth gateway.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health |
| POST | `/api/vnets` | Create VNet + subnets; store entity |
| GET | `/api/vnets` | List stored entities |
| GET | `/api/vnets/{name}` | Get one entity |

## POST body

```json
{
  "name": "vnet-allianz-demo-01",
  "location": "eastus",
  "addressSpace": ["10.40.0.0/16"],
  "subnets": [
    { "name": "subnet-app", "addressPrefix": "10.40.1.0/24" },
    { "name": "subnet-db", "addressPrefix": "10.40.2.0/24" }
  ],
  "resourceGroup": "rg-allianz-vnet-demo"
}
```

Required request fields:

| Field | Type | Meaning |
|-------|------|---------|
| `name` | string | VNet name |
| `location` | string | Azure region, for example `eastus` |
| `resourceGroup` | string | Existing target resource group |
| `addressSpace` | non-empty string array | VNet CIDR ranges |
| `subnets` | non-empty object array | Subnet definitions |
| `subnets[].name` | string | Subnet name |
| `subnets[].addressPrefix` | string | Subnet CIDR inside the VNet range |

## Responses

| Operation | Success | Common errors |
|-----------|---------|---------------|
| Health | `200` | `401` without valid authentication |
| Create | `201` | `400` invalid JSON/fields, `401` unauthenticated, `500` Azure failure |
| List | `200` | `401` unauthenticated, `500` storage failure |
| Get one | `200` | `401` unauthenticated, `404` missing record |

Successful create:

```json
{
  "name": "vnet-allianz-demo-01",
  "vnetId": "/subscriptions/.../virtualNetworks/vnet-allianz-demo-01",
  "subnetIds": [
    "/subscriptions/.../subnets/subnet-app",
    "/subscriptions/.../subnets/subnet-db"
  ],
  "location": "eastus",
  "resourceGroup": "rg-allianz-vnet-demo",
  "createdBy": "Authenticated User",
  "createdAt": "2026-09-28T00:00:00+00:00",
  "dryRun": false
}
```

`createdBy` comes from Easy Auth's validated caller headers, not from the POST
body.

## Postman

Import:

- `postman/Allianz-VNet-API.postman_collection.json`
- `postman/Allianz-VNet-API.postman_environment.json`

