# Postman step-by-step 

**Goal:** show health, create a VNet with two subnets, list records, and get
one record — first locally (safe), then on Azure with Entra auth.

---

## What you will demonstrate

| Step | Call | Proves |
|------|------|--------|
| Health | `GET /api/health` | API is up |
| Create | `POST /api/vnets` | VNet + **two** subnets created |
| List | `GET /api/vnets` | Records stored (Table Storage / memory) |
| Get | `GET /api/vnets/{name}` | One record retrieved |
| (Azure only) No token | `GET /api/health` without Bearer | Easy Auth returns **401** |

Importable files 

- `postman/Allianz-VNet-API.postman_collection.json`
- `postman/Allianz-VNet-API.postman_environment.json`

---

## Part A — Install and import Postman

### A1. Install Postman desktop

1. Download from <https://www.postman.com/downloads/>.
2. Install and open Postman.
3. Sign in or continue as guest (either works for this demo).

### A2. Import collection and environment

1. In Postman, select **Import** (top left).
2. Choose **files** and select both:
   - `postman/Allianz-VNet-API.postman_collection.json`
   - `postman/Allianz-VNet-API.postman_environment.json`
3. Select **Import**.
4. Confirm you see collection **Allianz VNet API Demo**.
5. At the **upper right** environment dropdown, select
   **Allianz VNet API - Demo**.


### A3. Open the environment (optional check)

1. Left sidebar → **Environments**.
2. Open **Allianz VNet API - Demo**.
3. Confirm these keys exist (values can stay as shipped for rehearsal):

| Variable | Purpose |
|----------|---------|
| `localBaseUrl` | Local host, usually `http://localhost:7071` |
| `localVnetName` | Name used by local create/get |
| `azureBaseUrl` | Deployed Function App URL |
| `accessToken` | Bearer token — **Current value only**, never commit |
| `resourceGroup` | Target Azure RG for live create |
| `azureVnetName` | Live VNet name (change before each live create) |
| `azureAddressSpace` | VNet CIDR |
| `azureSubnet1Prefix` / `azureSubnet2Prefix` | Two non-overlapping subnet CIDRs |

Leave `accessToken` **Current value** empty until Part C.

---

## Part B — Local dry-run demo (no Azure, no token)

Use this for practice and as a safe warm-up before the panel.

### B1. Start the local Function host

In PowerShell (Python 3.11 venv must be active):

```powershell
cd "C:\Users\singale\OneDrive - Allvue Systems, LLC\Documents\2026\Platform Repos\allianz-vnet-api-demo"
.\.venv\Scripts\Activate.ps1
python --version
func start
```

Wait until the host lists:

- `health: [GET] http://localhost:7071/api/health`
- `create_vnet: [POST] http://localhost:7071/api/vnets`
- `list_vnets: [GET] http://localhost:7071/api/vnets`
- `get_vnet: [GET] http://localhost:7071/api/vnets/{name}`

Keep this terminal running. Leave `DRY_RUN=true` in `local.settings.json`.

### B2. Confirm environment selection

Upper right → **Allianz VNet API - Demo**.

Confirm:

```text
localBaseUrl = http://localhost:7071
localVnetName = vnet-allianz-local-01
```

### B3. Run requests in order

In the collection, open folder **Local dry-run**.

#### 1 — Health

1. Select **1 - Health**.
2. Select **Send**.
3. Expect **Status: 200 OK**.
4. Body should look like:

```json
{
  "status": "ok",
  "service": "allianz-vnet-api-demo",
  "dryRun": true
}
```

Say: “Health proves the Function host is running. `dryRun: true` means no real
Azure VNet will be created.”

#### 2 — Create VNet (simulated)

1. Select **2 - Create VNet (simulated)**.
2. Open the **Body** tab and show the JSON (two subnets).
3. Select **Send** once.
4. Expect **Status: 201 Created**.
5. Confirm response has:
   - `"dryRun": true`
   - `"subnetIds"` with **length 2**
   - `"name"` matching `localVnetName`

Example body sent by the collection:

```json
{
  "name": "vnet-allianz-local-01",
  "location": "eastus",
  "resourceGroup": "rg-allianz-vnet-demo",
  "addressSpace": ["10.40.0.0/16"],
  "subnets": [
    { "name": "subnet-app", "addressPrefix": "10.40.1.0/24" },
    { "name": "subnet-db", "addressPrefix": "10.40.2.0/24" }
  ]
}
```

Say: “POST creates a VNet definition with two subnets in one request. Locally
this is simulated; on Azure the same body creates real resources.”

#### 3 — List VNet records

1. Select **3 - List VNet records**.
2. Select **Send**.
3. Expect **200** and `"count"` ≥ 1.

Say: “List returns stored API records, not a full Azure subscription inventory.”

#### 4 — Get VNet record

1. Select **4 - Get VNet record**.
2. Select **Send**.
3. Expect **200** and `"name": "vnet-allianz-local-01"`.

### B4. Local demo checklist

- [ ] Environment selected
- [ ] Health → 200, `dryRun: true`
- [ ] Create → 201, two `subnetIds`
- [ ] List → 200, count ≥ 1
- [ ] Get → 200, correct name
- [ ] Test scripts under **Test Results** pass (optional)

In-memory records disappear when you stop `func start`. That is expected.

---

## Part C — Azure authenticated demo (panel flow)

Prerequisites: Function App deployed, Easy Auth enabled, managed identity has
Network Contributor on the target resource group. Validated demo URL:

```text
https://allianz-vnet-api-60a75acd.azurewebsites.net
```

### C1. Set live-safe environment values

Environments → **Allianz VNet API - Demo** → edit **Current value** for:

```text
azureBaseUrl       = https://allianz-vnet-api-60a75acd.azurewebsites.net
resourceGroup      = rg-allianz-vnet-api-e2e
azureLocation      = eastus
azureVnetName      = vnet-allianz-panel-01
azureAddressSpace  = 10.90.0.0/16
azureSubnet1Prefix = 10.90.1.0/24
azureSubnet2Prefix = 10.90.2.0/24
```

Before every new live create:

1. Change `azureVnetName` (must be unique in the RG).
2. Use a free address space (subnets inside the VNet, not overlapping).
3. Save the environment.

Example valid CIDR relationship:

```text
VNet:     10.90.0.0/16
Subnet 1: 10.90.1.0/24
Subnet 2: 10.90.2.0/24
```

### C2. Obtain an Entra bearer token (once, before the demo)

Azure CLI supplies the short-lived token. Postman is the visible client — do
**not** put a client secret into Postman.

Copy the token **to the clipboard** so the terminal does not wrap it. A JWT
must stay one continuous line (`header.payload.signature`). Line breaks cause
Easy Auth errors such as `IDX12709` / `IDX12741`.

```powershell
az login
$ClientId = "5f21a0ca-f6cf-4284-85e6-b775f8cfc2ed"
az account get-access-token `
  --scope "api://$ClientId/user_impersonation" `
  --query accessToken `
  --output tsv | Set-Clipboard
```

Confirm the clipboard holds one line starting with `eyJ` and containing exactly
two `.` characters. Do not paste the token into chat, Notepad, or Word first —
those wrap lines and break the JWT.

In Postman:

1. Environments → **Allianz VNet API - Demo**.
2. Find `accessToken`.
3. Paste (**Ctrl+V**) into **Current value** only (not Initial value).
4. Save.
5. Confirm the environment is still selected upper right.
6. Optional emergency bypass: paste the same clipboard value directly into the
   request **Authorization → Bearer Token** field instead of `{{accessToken}}`.
7. Clear the PowerShell scrollback before screen sharing if the token was
   printed without `Set-Clipboard`.

Tokens expire in about one hour. Refresh 10–15 minutes before the panel with
the same `Set-Clipboard` command.

Never commit, screenshot, or paste the token into docs, chat, or GitHub.

### C3. Run Azure requests in order

Open folder **Azure authenticated demo**.

#### 1 — Health without token (expect 401)

1. Select **1 - Health without token (expect 401)**.
2. Note Auth is **No Auth** (folder bearer is overridden).
3. Select **Send**.
4. Expect **401 Unauthorized**.

Say: “Easy Auth rejects anonymous callers before Python runs.”

#### 2 — Authenticated health

1. Select **2 - Authenticated health**.
2. Auth inherits folder **Bearer Token** → `{{accessToken}}`.
3. Select **Send**.
4. Expect **200** and `"dryRun": false`.

```json
{
  "status": "ok",
  "service": "allianz-vnet-api-demo",
  "dryRun": false
}
```

Say: “Postman sends the Entra bearer token. Easy Auth validates it and forwards
the request to the Function.”

#### 3 — List VNet records

1. Select **3 - List VNet records**.
2. Select **Send**.
3. Expect **200**, with `count` and `items`.

#### 4 — Create VNet with two subnets

1. Select **4 - Create VNet with two subnets**.
2. Open **Body** and confirm name + CIDRs match the environment (unused).
3. Select **Send once** — do not click repeatedly.
4. Expect **201 Created**.
5. Confirm:
   - `"dryRun": false`
   - two `subnetIds`
   - `"createdBy"` is your display name (not `local-dev`)

Say: “One POST creates the VNet and both subnets. `createdBy` comes from the
validated token identity, not from the JSON body.”

#### 5 — Get created VNet record

1. Select **5 - Get created VNet record**.
2. Select **Send**.
3. Expect **200**, same name, two `subnetIds`.

### C4. Portal proof (recommended)

1. Azure Portal → Resource group `rg-allianz-vnet-api-e2e`.
2. Open the new Virtual Network.
3. **Subnets** blade → show **two** subnets.
4. Optionally open the Function App → **Authentication** to show Easy Auth.

### C5. Azure demo checklist

- [ ] Fresh token in `accessToken` Current value
- [ ] Correct environment selected
- [ ] Unique `azureVnetName` + free CIDRs
- [ ] No-auth health → **401**
- [ ] Auth health → **200**, `dryRun: false`
- [ ] Create → **201**, two subnets, real `createdBy`
- [ ] Get → **200**
- [ ] Portal shows VNet + two subnets
- [ ] Clear token Current value after the demo

---








