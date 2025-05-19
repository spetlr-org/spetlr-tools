import sys
import types

import click

try:
    import winreg
except ImportError:
    winreg = None


# On non-Windows, make sure there is a winreg module so tests can patch it
try:
    import winreg
except ImportError:
    winreg = types.ModuleType("winreg")
    sys.modules["winreg"] = winreg


def set_user_env_var_windows(name: str, value: str):
    if winreg is None:
        raise RuntimeError("winreg is unavailable on this platform")
    # KEY_CURRENT_USER\Environment
    env_key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE
    )
    try:
        winreg.SetValueEx(env_key, name, 0, winreg.REG_EXPAND_SZ, value)
        val_str = (
            click.style(value, fg="red")
            if value.lower() == "false"
            else click.style(value, fg="green")
        )
        click.echo(f"Environment variable {name} set to {val_str}")
    finally:
        winreg.CloseKey(env_key)


def remove_user_env_var_windows(name: str):
    if winreg is None:
        raise RuntimeError("winreg is unavailable on this platform")
    env_key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
    )
    try:
        winreg.DeleteValue(env_key, name)
        click.secho(f"Environment variable {name} removed from registry", fg="green")
    except FileNotFoundError:
        click.secho(f"Environment variable {name} not found in registry", fg="red")
    finally:
        winreg.CloseKey(env_key)
