# New-computer setup — from nothing to working demo

## 1. Before using the computer

You need:

- Windows 10 or 11 with permission to install applications;
- a GitHub account that can read this repository;
- an Azure account and active subscription;
- permission to create resources in the chosen subscription/resource group;
- permission to assign an Azure RBAC role; and
- permission to create or manage a Microsoft Entra app registration.


## 2. Install Windows package support

Open **PowerShell as your normal user**, not Administrator unless an installer
requires it:

```powershell
winget --version
```

If `winget` is unavailable, install or update **App Installer** from Microsoft
Store.

## 3. Install Git

```powershell
winget install --id Git.Git --exact
```

Close and reopen PowerShell:

```powershell
git --version
```

Validated development version: `git 2.50.1.windows.1`. A newer Git version is
normally acceptable.

Configure the name/email that your own commits should use:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## 4. Clone the repository

Choose a development folder:

```powershell
New-Item -ItemType Directory -Force "$HOME\source"
Set-Location "$HOME\source"
git clone https://github.com/sanjayIngale/vnet-api-demo-submission
Set-Location vnet-api-demo-submission
git status
```

Expected:

```text
On branch main
nothing to commit, working tree clean
```

If GitHub authentication fails for a public repository, verify the URL in a
browser. Remove an invalid stored credential from Windows Credential Manager
only if it is interfering with Git.

## 5. Install Python 3.11

```powershell
winget install --id Python.Python.3.11 --exact
```

Python 3.11 can exist beside Python 3.14. Do not uninstall another version.

Restart PowerShell:

```powershell
py -3.11 --version
```

Validated version:

```text
Python 3.11.9
```

Any current Python `3.11.x` patch version should work.

## 6. Install Azure CLI

```powershell
winget install --id Microsoft.AzureCLI --exact
```

Restart PowerShell:

```powershell
az --version
```

Validated version: Azure CLI `2.90.0`. A newer compatible version should work.

## 7. Install Azure Functions Core Tools v4

Use Microsoft's current Windows instructions:

<https://learn.microsoft.com/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools>

If the package is available in your `winget` source:

```powershell
winget install --id Microsoft.Azure.FunctionsCoreTools --exact
```

Restart PowerShell:

```powershell
func --version
```

Validated version:

```text
4.15.1
```

The important requirement is major version `4`.

## 8. Install Postman Desktop

Download:

<https://www.postman.com/downloads/>

Or, if available:

```powershell
winget install --id Postman.Postman --exact
```

Use the desktop application. The web application requires the Postman Desktop
Agent to call `localhost`.

## 9. Verify all tools

Open a **new** PowerShell window:

```powershell
git --version
py -3.11 --version
az --version
func --version
```


## 10. Create the Python environment

From the cloned repository:

```powershell
Set-Location "$HOME\source\vnet-api-demo-submission"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Expected direct packages:

```text
azure-functions==1.25.0
azure-identity==1.25.3
azure-mgmt-network==33.0.0
azure-data-tables==12.7.0
```

Verify:

```powershell
pip show azure-functions azure-identity azure-mgmt-network azure-data-tables
```

If PowerShell blocks `Activate.ps1`:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Review the prompt and approve only if permitted by your organisation. As an
alternative, call `.venv\Scripts\python.exe` directly without activation.

## 11. Create safe local settings

```powershell
Copy-Item local.settings.json.example local.settings.json
```

Confirm:

```json
"DRY_RUN": "true",
"STORAGE_CONNECTION": ""
```

Never add `local.settings.json` to Git:

```powershell
git check-ignore -v local.settings.json
```

Expected: `.gitignore` is reported as the matching rule.

## 12. Start the local API

```powershell
.\.venv\Scripts\Activate.ps1
python --version
func start
```

Expected routes:

```text
GET  http://localhost:7071/api/health
POST http://localhost:7071/api/vnets
GET  http://localhost:7071/api/vnets
GET  http://localhost:7071/api/vnets/{name}
```

If `UseDevelopmentStorage=true` reports an emulator connection error, install
and run Azurite using the official guide:

<https://learn.microsoft.com/azure/storage/common/storage-use-azurite>

This project has only HTTP triggers and uses its own in-memory data store in
dry-run mode, so many Core Tools versions do not need an active emulator.

## 13. Import Postman and prove local operation

1. Open Postman.
2. Select **Import**.
3. Import:
   - `postman/Allianz-VNet-API.postman_collection.json`
   - `postman/Allianz-VNet-API.postman_environment.json`
4. Select environment **Allianz VNet API - Demo**.
5. Run the **Local dry-run** requests in numeric order.

Expected:

| Request | Status | Important result |
|---------|--------|------------------|
| Health | 200 | `dryRun: true` |
| Create simulated | 201 | two simulated subnet IDs |
| List | 200 | count at least 1 |
| Get | 200 | matching local VNet name |

No Azure resource has been created.

## 14. Sign in to Azure

In a separate PowerShell window:

```powershell
az login
az account list --output table
az account set --subscription "<subscription-id-or-name>"
az account show --query "{subscription:name,id:id,tenant:tenantId,user:user.name}" --output table
```

Write down:

- subscription ID;
- tenant ID; and
- selected subscription name.

Do not copy tokens, keys, or secrets into notes.

## 15. Register Azure resource providers

Registration is normally a one-time subscription operation:

```powershell
az provider register --namespace Microsoft.Network --wait
az provider register --namespace Microsoft.Web --wait
az provider register --namespace Microsoft.Storage --wait
az provider register --namespace Microsoft.Insights --wait
```

Verify:

```powershell
az provider show --namespace Microsoft.Network --query registrationState -o tsv
az provider show --namespace Microsoft.Web --query registrationState -o tsv
az provider show --namespace Microsoft.Storage --query registrationState -o tsv
az provider show --namespace Microsoft.Insights --query registrationState -o tsv
```

Expected for each:

```text
Registered
```

If registration is forbidden, ask the subscription administrator.

## 16. Define unique Azure names

Use a fresh suffix because storage and Function names are globally unique:

```powershell
$Location = "eastus"
$Suffix = Get-Random -Minimum 10000 -Maximum 99999
$ResourceGroup = "rg-allianz-vnet-demo-$Suffix"
$StorageAccount = "allianzvnet$Suffix"
$FunctionApp = "allianz-vnet-api-$Suffix"
$TableName = "VnetCreations"
$SubscriptionId = az account show --query id --output tsv
$TenantId = az account show --query tenantId --output tsv

$ResourceGroup
$StorageAccount
$FunctionApp
$SubscriptionId
$TenantId
```

Save these non-secret values. Do not close the terminal because later commands
use the variables.

## 17. Create Azure resources

### Resource group

```powershell
az group create --name $ResourceGroup --location $Location --output table
```

### Storage account

```powershell
az storage account create `
  --name $StorageAccount `
  --resource-group $ResourceGroup `
  --location $Location `
  --sku Standard_LRS `
  --kind StorageV2 `
  --output table
```

Obtain the connection string without printing it:

```powershell
$StorageConnection = az storage account show-connection-string `
  --name $StorageAccount `
  --resource-group $ResourceGroup `
  --query connectionString `
  --output tsv

if (-not $StorageConnection) { throw "Storage connection string was not returned" }
```

Create the table:

```powershell
az storage table create `
  --name $TableName `
  --connection-string $StorageConnection `
  --output table
```

### Function App

```powershell
az functionapp create `
  --resource-group $ResourceGroup `
  --consumption-plan-location $Location `
  --runtime python `
  --runtime-version 3.11 `
  --functions-version 4 `
  --os-type Linux `
  --name $FunctionApp `
  --storage-account $StorageAccount `
  --output table
```

Set application values:

```powershell
az functionapp config appsettings set `
  --resource-group $ResourceGroup `
  --name $FunctionApp `
  --settings `
    "DRY_RUN=false" `
    "AZURE_SUBSCRIPTION_ID=$SubscriptionId" `
    "STORAGE_CONNECTION=$StorageConnection" `
    "TABLE_NAME=$TableName" `
  --output none
```

Clear the local variable after Azure stores it:

```powershell
$StorageConnection = $null
```

## 18. Enable Managed Identity and RBAC

Create the system-assigned identity:

```powershell
$PrincipalId = az functionapp identity assign `
  --resource-group $ResourceGroup `
  --name $FunctionApp `
  --query principalId `
  --output tsv

$ResourceGroupId = az group show `
  --name $ResourceGroup `
  --query id `
  --output tsv
```

Assign least-privilege network access:

```powershell
az role assignment create `
  --assignee-object-id $PrincipalId `
  --assignee-principal-type ServicePrincipal `
  --role "Network Contributor" `
  --scope $ResourceGroupId `
  --output table
```

If this returns `AuthorizationFailed`, your account may be Contributor but
lack permission to assign roles. Give `$PrincipalId` and `$ResourceGroupId` to
an Azure RBAC administrator and ask them to run the assignment.

Verify:

```powershell
az role assignment list `
  --assignee-object-id $PrincipalId `
  --scope $ResourceGroupId `
  --query "[].{role:roleDefinitionName,scope:scope}" `
  --output table
```

## 19. Deploy the Python Function

Return to the repository and activate Python 3.11:

```powershell
Set-Location "$HOME\source\vnet-api-demo-submission"
.\.venv\Scripts\Activate.ps1
python --version
func azure functionapp publish $FunctionApp
```

Expected:

- remote build succeeds;
- four functions/triggers are listed; and
- synchronization succeeds.

Do not test anonymous success yet; authentication is configured next.

## 20. Configure Microsoft Entra Easy Auth v2

Use the Azure Portal for a first build:

1. Open the new Function App.
2. Select **Settings → Authentication**.
3. Select **Add identity provider**.
4. Provider: **Microsoft**.
5. Tenant type: current workforce tenant.
6. App registration: create new.
7. Restrict access: **Require authentication**.
8. Unauthenticated requests: **HTTP 401 Unauthorized**.
9. Token store: enabled.
10. Save.

Open the provider and verify the issuer is:

```text
https://login.microsoftonline.com/<tenant-id>/v2.0
```

Do not accept the legacy issuer:

```text
https://sts.windows.net/<tenant-id>/
```

Copy:

- Application (client) ID; and
- Directory (tenant) ID.

## 21. Expose the delegated scope

In **Microsoft Entra ID → App registrations → your application**:

1. Select **Expose an API**.
2. Add/accept Application ID URI `api://<client-id>`.
3. Add scope `user_impersonation`.
4. Who can consent: Admins and users.
5. Display name: `Access VNet API`.
6. State: enabled.
7. Save.

Under **Authorized client applications**:

1. Add client ID `04b07795-8ddb-461a-bbee-02f9e1bf7b46`
   (Microsoft Azure CLI).
2. Select `user_impersonation`.
3. Add application.

If you cannot create/update the registration, ask an Entra app administrator
to complete these steps.

## 22. Update Postman for the new environment

In environment **Allianz VNet API - Demo**, replace:

```text
azureBaseUrl = https://<your-function-app>.azurewebsites.net
tenantId      = <your-tenant-id>
clientId      = <your-client-id>
resourceGroup = <your-resource-group>
azureVnetName = vnet-allianz-demo-01
```

Choose a fresh address range:

```text
azureAddressSpace  = 10.90.0.0/16
azureSubnet1Prefix = 10.90.1.0/24
azureSubnet2Prefix = 10.90.2.0/24
```

The subnets must be inside the VNet range and must not overlap.

## 23. Obtain a user token

```powershell
$ClientId = "<your-client-id>"

az account get-access-token `
  --scope "api://$ClientId/user_impersonation" `
  --query accessToken `
  --output tsv | Set-Clipboard
```

Paste (**Ctrl+V**) into Postman environment variable `accessToken` **Current
value** only, then Save. Use `Set-Clipboard` so the JWT is not line-wrapped
(`IDX12709` / `IDX12741`). Never save it in Git, chat, or show it during
screen sharing.

If consent is required, verify the authorised Azure CLI application in section
21 or ask a tenant administrator.

## 24. Complete Azure verification

Run Postman folder **Azure authenticated demo** in order:

| Step | Expected |
|------|----------|
| Health without token | 401 |
| Authenticated health | 200 and `dryRun: false` |
| List records | 200 |
| Create VNet | 201, two real subnet IDs, caller name |
| Get created record | 200, same IDs |

Do not repeatedly select Send on the create request. Azure provisioning can
take several seconds.

Verify independently:

1. Azure Portal → Resource group → VNet → Address space.
2. VNet → Subnets → both subnet rows.
3. Storage account → Storage browser → Tables → `VnetCreations`.
4. Confirm the row key equals the VNet name.

## 25. Clean-machine success checklist

- [ ] Repository cloned and working tree clean
- [ ] Python 3.11 virtual environment active
- [ ] Exact dependencies installed
- [ ] Local health returns 200 and `dryRun: true`
- [ ] Local simulated POST/list/get pass
- [ ] Correct Azure subscription selected
- [ ] Four resource providers registered
- [ ] Resource group, storage, table, and Function App created
- [ ] Managed Identity enabled
- [ ] Network Contributor scoped to only the demo resource group
- [ ] Four HTTP functions deployed
- [ ] Easy Auth v2 issuer verified
- [ ] Anonymous deployed request returns 401
- [ ] Valid Entra user token returns 200
- [ ] Live POST returns 201 with two subnet IDs
- [ ] GET returns the persisted table record
- [ ] Azure Portal shows the VNet and subnets
- [ ] No token, key, secret, or `local.settings.json` in Git

## 26. Permission-error recovery

| Error | Owner of the fix |
|-------|------------------|
| Cannot create resource group | Subscription Owner/Contributor administrator |
| Provider registration denied | Subscription Owner |
| Role assignment denied | Owner, User Access Administrator, or RBAC Administrator |
| App registration creation denied | Entra Application/Cloud Application Administrator |
| Admin consent required | Entra tenant administrator |
| Storage key listing denied | Storage account/Resource Group Owner or appropriate custom role |

Record the exact error, operation, resource scope, and principal ID. Do not ask
for subscription Owner if a narrower administrator action solves the problem.

## 27. Rebuild and dependency notes

`requirements.txt` pins the four direct packages to versions proven by live
Azure testing on 27–28 September 2026.

Pinned direct dependencies improve repeatability but are not a complete
transitive lock. For a production build, generate and review a full lock file
using an approved tool such as `pip-tools`, and use automated dependency
updates.

Do not casually upgrade `azure-mgmt-network`: version 33 exposed the archived
sample dictionary incompatibility that led to the current model-object fix.
After any upgrade, rerun local validation and an isolated live Azure test.

## 28. Cleanup

After the assignment:

```powershell
az group delete --name $ResourceGroup --yes --no-wait
az ad app delete --id $ClientId
```

Deleting the resource group does not delete the Entra app registration.

Also:

- clear Postman's `accessToken` Current value;
- stop `func start` with `Ctrl+C`; and
- optionally remove `.venv/`.

