## Request flow

1. Postman sends an HTTP request and an Entra bearer token.
2. Easy Auth validates the token before Python executes.
3. The route validates the JSON request.
4. `DefaultAzureCredential` uses the Function App's system-assigned Managed
   Identity in Azure.
5. The Network SDK creates the VNet and every requested subnet.
6. The result and caller identity are stored in Table Storage.
7. The API returns JSON and an HTTP status code.

## Security boundaries

- Easy Auth requires authentication but intentionally performs no role/group
  restriction: the assignment permits every authenticated user.
- Managed Identity has Network Contributor scoped to one resource group.
- No Azure management password or service-principal secret is stored in Python.
- The current demo uses a storage connection string. A production enhancement
  would use Managed Identity and the appropriate Table data role.

