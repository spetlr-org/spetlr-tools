# !/usr/bin/env python
import argparse
import configparser
import json
import re
import subprocess
import sys
import tempfile
from io import TextIOBase
from pathlib import Path
from subprocess import run
from typing import List, TypedDict


class LibType(TypedDict):
    name: str
    version: str


class Pipr:
    def __init__(self, debug_out: TextIOBase = sys.stdout):
        try:
            import uv

            self.uv_path = uv.find_uv_bin()
        except ImportError:
            self.uv_path = None

        self.debug_out = debug_out

    def venv(self, path: str):
        if self.uv_path:
            run([self.uv_path, "venv", "--python", "3.11", "--seed", path])
        else:
            run([sys.executable, "-m", "venv", path])

        python = str(Path(path) / "bin" / "python")
        if not Path(python).exists():
            python = str(Path(path) / "Scripts" / "python.exe")

        run(
            [python, "-m", "pip", "install", "uv"],
            stdout=self.debug_out.buffer,
        )

        self.uv_path = subprocess.check_output(
            [python, "-c", "print('hello world')"], text=True
        ).strip()
        self.uv_path = subprocess.check_output(
            [python, "-c", "import uv;print(uv.find_uv_bin())"], text=True
        ).strip()

    def run(self, *args, **kwargs):
        if not kwargs:
            kwargs = dict(stdout=self.debug_out.buffer)
        return run([self.uv_path, "pip", *args], **kwargs)


def main():
    parser = argparse.ArgumentParser(
        description="Update requirement versions in specified file."
    )
    parser.add_argument(
        "in_file",
        type=str,
        help="The requirements file to read.",
    )
    parser.add_argument(
        "-o, --out-file",
        type=str,
        default=None,
        dest="out_file",
        help="The output to file.",
    )
    parser.add_argument("--cfg", action="store_const", const=True, default=False)
    parser.add_argument(
        "--cfg-file",
        type=str,
        default="setup.cfg",
        dest="cfg_file",
        help="specify your configuration file if it differs from setup.cfg",
    )
    parser.add_argument(
        "--reject",
        type=str,
        default="pip|pywin32",
        help="regex to exclude. Default: pip|pywin32",
    )
    args = parser.parse_args()

    if not args.out_file and not args.cfg:
        just_print = True
        debug_out = sys.stderr
    else:
        just_print = False
        debug_out = sys.stdout

    # validate arguments:
    if args.out_file:
        with open(args.out_file, "w") as f:
            pass
        print(f"Output will be in {args.out_file}.")
    if args.cfg:
        print(f"Output will be in {args.cfg_file}.")

    with open(args.in_file) as f:
        freeze = freeze_req(f.read(), reject=args.reject, debug_out=debug_out)

    if args.out_file:
        with open(args.out_file, "w") as f:
            f.write("\n".join(f"{lib['name']}=={lib['version']}" for lib in freeze))

    if args.cfg:
        injection = "".join(f"\n{lib['name']}=={lib['version']}" for lib in freeze)
        config = configparser.ConfigParser()
        config.read(args.cfg_file)
        config["options"]["install_requires"] = injection
        with open(args.cfg_file, "w") as f:
            config.write(f)

    if just_print:
        print("\n".join(f"{lib['name']}=={lib['version']}" for lib in freeze))


def freeze_req(
    requirements: str, reject: str = "", debug_out: TextIOBase = sys.stdout
) -> List[LibType]:
    pat = re.compile(reject)
    pipr = Pipr(debug_out=debug_out)

    with tempfile.TemporaryDirectory() as td:
        pipr.venv(td)

        rf_path = str(Path(td) / "reqs.txt")
        with open(rf_path, "w") as f:
            f.write(requirements)

        freeze_json = pipr.run(
            "list",
            "--format",
            "json",
            capture_output=True,
            text=True,
        )
        freeze = json.loads(freeze_json.stdout)
        return [lib for lib in freeze if not pat.match(lib["name"])]
