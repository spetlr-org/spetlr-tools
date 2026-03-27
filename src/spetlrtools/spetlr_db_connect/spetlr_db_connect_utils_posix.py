import os

import click

# On POSIX, append export or unset lines to the user's shell rc file


def set_user_env_var_posix(name: str, value: str):
    shell = os.environ.get("SHELL", "")
    rc_file = None
    if shell.endswith("bash"):
        rc_file = os.path.expanduser("~/.bashrc")
    elif shell.endswith("zsh"):
        rc_file = os.path.expanduser("~/.zshrc")
    if rc_file:
        line = f"export {name}={value}\n"
        with open(rc_file, "a") as f:
            f.write(f"\n# Added by spetlr-dbconnect-cli\n{line}")
        click.secho(
            f"Appended export to {rc_file}. Run 'source {rc_file}' or restart your shell.",
            fg="green",
        )
    else:
        click.echo(
            f"Please set {name}={value} in your shell environment manually.",
            fg="yellow",
        )


def remove_user_env_var_posix(name: str):
    shell = os.environ.get("SHELL", "")
    rc_file = None
    if shell.endswith("bash"):
        rc_file = os.path.expanduser("~/.bashrc")
    elif shell.endswith("zsh"):
        rc_file = os.path.expanduser("~/.zshrc")
    if rc_file:
        line = f"unset {name}\n"
        with open(rc_file, "a") as f:
            f.write(f"\n# Cleanup by spetlr-dbconnect-cli\n{line}")
        click.secho(
            f"Appended unset to {rc_file}. Run 'source {rc_file}' or restart your shell.",
            fg="green",
        )
    else:
        click.secho(
            f"Please remove {name} from your shell environment manually.", fg="yellow"
        )
