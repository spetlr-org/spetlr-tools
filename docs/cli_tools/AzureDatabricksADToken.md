
# Azure Databricks AD Token

If you want to use azure AD tokens to access the Databricks API
(instead of the personal access tokens that you can pull from the
web frontend), you can follow 
[this guide here](https://docs.microsoft.com/en-us/azure/databricks/dev-tools/api/latest/aad/app-aad-token).
Set the redirect URI to `localhost` exactly as in the example.

After setting up the initial web-app for authentication, you can use 
the command line tool provided by this package to get the token quickly.

```
$> spetlr-az-databricks-token --appId $appId --tenantId $tenantId --workspaceUrl $workspaceUrl
```

The parameters `appId` and `tenantId` correspond to the web-app that you registered.
If no further parameters are given the databricks token will be printed to
the console for use in your deployment pipeline.

If you set the optional parameter `workspaceUrl`, the tool will instead 
overwrite your `~/.databrickscfg` file with the provided workspace url
and with the newly generated token.
