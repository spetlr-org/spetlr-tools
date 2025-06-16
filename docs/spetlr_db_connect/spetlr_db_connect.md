# spetlr-dbconnect-cli

A lightweight CLI to manage SPETLR Databricks-Connect environment variables and streamline Databricks CLI authentication workflows.

---

## Prerequisites

- **Python** ≥ 3.8  
- **Databricks-Connect** version matching your cluster’s DBR.  
  For a DBR 14.3.x cluster, install:
  ```bash
  pip install databricks-connect==14.3.*
  ```
- **Databricks CLI** installed and configured (our tool will invoke `databricks auth login` and `databricks auth env`).

---

## Installation

### From local source
```bash
# In the spetlr-tools repo root
pip install -e .
```

### From PyPI
```bash
pip install spetlr-tools
```

---

## Usage

```
spetlr-dbconnect-cli [OPTIONS] [-- COMMAND [ARGS]...]
```

### Options

| Flag                                   | Description                                                                                     |
|----------------------------------------|-------------------------------------------------------------------------------------------------|
| `-p, --profile-name <name>`            | Databricks CLI profile name to configure (required for full config)                             |
| `-u, --host-url <url>`                 | Databricks host URL (no trailing slash), e.g. `https://adb-1234.azuredatabricks.net`           |
| `--enable-connect`                     | Enable `SPETLR_DATABRICKS_CONNECT=true` only                                                    |
| `--disable-connect`                    | Disable `SPETLR_DATABRICKS_CONNECT=false` only                                                  |
| `--cleanup-env-vars`                   | Remove `SPETLR_DATABRICKS_CONNECT`, `DATABRICKS_CONFIG_PROFILE`, and `DATABRICKS_HOST`          |
| `--help`                               | Show this message and exit                                                                     |

### Examples

#### 1. Full configuration  
Sets profile, host, connector flag, and runs the Databricks CLI authentication:
```bash
spetlr-dbconnect-cli   --profile-name myprofile   --host-url https://adb-1234.azuredatabricks.net   --enable-connect
```
This will:
1. Write user-level env vars:
   - `SPETLR_DATABRICKS_CONNECT=true`
   - `DATABRICKS_CONFIG_PROFILE=myprofile`
   - `DATABRICKS_HOST=https://adb-1234.azuredatabricks.net`
2. Invoke:
   ```bash
   databricks auth login --configure-cluster --profile myprofile --host https://adb-1234.azuredatabricks.net
   databricks auth env   --profile myprofile
   ```

#### 2. Toggle only  
Mark only the connect flag without changing profile/host:
```bash
spetlr-dbconnect-cli --disable-connect
```
Sets `SPETLR_DATABRICKS_CONNECT=false` and exits.

#### 3. Cleanup  
Remove all related environment variables:
```bash
spetlr-dbconnect-cli --cleanup-env-vars
```

---

## Restart / Shell-Reload Note

> **Why you may not see the new var immediately**  
> On Windows, PowerShell (and most shells) load **user** registry variables only at startup. Writing to `HKEY_CURRENT_USER\Environment` affects **new** shells, not ones already open.

To pick up changes in your session:

1. **Close & reopen** your PowerShell window.  
2. Or use the “Immediate verification” trick above to spawn a new process with the updated vars.

After restarting, confirm with:
```powershell
Get-ChildItem Env:SPETLR_DATABRICKS_CONNECT
```
or in Python:
```python
import os
print(os.environ.get("SPETLR_DATABRICKS_CONNECT"))
```

---

With this CLI in place, SPETLR’s `Spark.get()` will detect `SPETLR_DATABRICKS_CONNECT=true` and automatically use Databricks-Connect when you submit Spark jobs.
