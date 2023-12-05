
# Datbricks CLI installation

The recommended installation scripts for the datsbricks CLI v2 from databricks (as 
recommended [here](https://docs.databricks.com/en/dev-tools/cli/install.html#)) are 
system-wide installations.

In some cases you may want to keep different versions of the cli in different python 
virtual environments. That is why we supply an installer that will install to you 
venv folder. Use as in the following examples.

```powershell
spetlr-databricks-cli latest        # print the latest available version
spetlr-databricks-cli uninstall     # removes any installed v1 or v2 cli from venv
spetlr-databricks-cli install       # installs latest datbricks cli to venv

spetlr-databricks-cli install --version "0.210.1" 
# fails because of an existing installation

# save the version to reuse is until you are ready to update
spetlr-databricks-cli latest > my.db.fixed.version.txt

spetlr-databricks-cli install --version @my.db.fixed.version.txt --force
# read version from file and overwrite existing installations
```
