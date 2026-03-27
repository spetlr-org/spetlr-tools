import platform
import subprocess
import sys

import click

from spetlrtools.spetlr_db_connect.spetlr_db_connect_utils_posix import (
    remove_user_env_var_posix,
    set_user_env_var_posix,
)
from spetlrtools.spetlr_db_connect.spetlr_db_connect_utils_win import (
    remove_user_env_var_windows,
    set_user_env_var_windows,
)


@click.command()
@click.option(
    "--profile-name",
    "-p",
    default=None,
    help="The Databricks CLI profile name to configure (required unless toggling only)",
)
@click.option(
    "--host-url",
    "-u",
    default=None,
    help="Databricks host URL, e.g. https://adb-... (no trailing slash)",
)
@click.option(
    "--enable-connect",
    "enable_connect",
    flag_value=True,
    default=None,
    help="Enable SPETLR_DATABRICKS_CONNECT only",
)
@click.option(
    "--disable-connect",
    "enable_connect",
    flag_value=False,
    help="Disable SPETLR_DATABRICKS_CONNECT only",
)
@click.option(
    "--cleanup-env-vars",
    is_flag=True,
    help="Remove SPETLR_DATABRICKS_CONNECT, DATABRICKS_CONFIG_PROFILE, and DATABRICKS_HOST",
)
def main(
    profile_name: str, host_url: str, enable_connect: bool, cleanup_env_vars: bool
):
    """
    CLI to set, toggle, or cleanup environment variables and login to Databricks.
    """
    # Cleanup branch
    if cleanup_env_vars:
        if platform.system() == "Windows":
            for var in [
                "SPETLR_DATABRICKS_CONNECT",
                "DATABRICKS_CONFIG_PROFILE",
                "DATABRICKS_HOST",
            ]:
                remove_user_env_var_windows(var)
        else:
            for var in [
                "SPETLR_DATABRICKS_CONNECT",
                "DATABRICKS_CONFIG_PROFILE",
                "DATABRICKS_HOST",
            ]:
                remove_user_env_var_posix(var)
        sys.exit(0)

    setter_fn = (
        set_user_env_var_windows
        if platform.system() == "Windows"
        else set_user_env_var_posix
    )

    # Toggle-only branch
    if enable_connect is not None and not profile_name and not host_url:
        val = "true" if enable_connect else "false"
        setter_fn("SPETLR_DATABRICKS_CONNECT", val)
        sys.exit(0)

    # Full config branch: profile_name required
    if not profile_name:
        click.secho(
            "Error: --profile-name is required for configuration", fg="red", err=True
        )
        sys.exit(1)

    # Normalize host URL
    host = host_url.rstrip("/") if host_url else None

    # Set SPETLR_DATABRICKS_CONNECT
    val = "true" if (enable_connect or enable_connect is None) else "false"
    setter_fn("SPETLR_DATABRICKS_CONNECT", val)
    setter_fn("DATABRICKS_CONFIG_PROFILE", profile_name)
    if host:
        setter_fn("DATABRICKS_HOST", host)

    # Invoke Databricks CLI
    cmds = [
        [
            "databricks",
            "auth",
            "login",
            "--configure-cluster",
            "--profile",
            profile_name,
        ]
        + (["--host", host] if host else []),
        ["databricks", "auth", "env", "--profile", profile_name],
    ]
    for cmd in cmds:
        click.secho(f"Running: {' '.join(cmd)}", fg="cyan")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            click.secho(
                f"Command {' '.join(cmd)} failed with code {result.returncode}",
                fg="red",
            )
            sys.exit(result.returncode)


if __name__ == "__main__":
    main()
