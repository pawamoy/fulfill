"""Module that contains the command line application."""

# Why does this file exist, and why not put this in `__main__`?
#
# You might be tempted to import things from `__main__` later,
# but that will cause problems: the code will get executed twice:
#
# - When you run `python -m fulfill` python will execute
#   `__main__.py` as a script. That means there won't be any
#   `fulfill.__main__` in `sys.modules`.
# - When you import `__main__` it will get executed again (as a module) because
#   there's no `fulfill.__main__` in `sys.modules`.

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
from typing import Any

from duty.cli import main as duty

from fulfill import debug, commands


duties = Path(__file__).parent / "data" / "duties.py"


class _DebugInfo(argparse.Action):
    def __init__(self, nargs: int | str | None = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        debug.print_debug_info()
        sys.exit(0)


def get_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser.

    Returns:
        An argparse parser.
    """
    parser = argparse.ArgumentParser(prog="fulfill")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {debug.get_version()}")
    parser.add_argument("--debug-info", action=_DebugInfo, help="Print debug information.")
    return parser


def main(args: list[str] | None = None) -> int:
    """Run the main program.

    This function is executed when you type `fulfill` or `python -m fulfill`.

    Parameters:
        args: Arguments passed from the command line.

    Returns:
        An exit code.
    """
    # parser = get_parser()
    # opts = parser.parse_args(args=args)
    # print(opts)
    # return 0

    if len(sys.argv) == 1 or sys.argv[1] == "help":
        if len(sys.argv) > 2:
            commands.run("default", "duty", "-d", str(duties), "--help", sys.argv[2])
        else:
            print("Available commands")
            print("  help                  Print this help. Add task name to print help.")
            print("  install               Create all virtual environments and install dependencies.")
            print("  run                   Run a command in the default virtual environment.")
            print("  multirun              Run a command for all configured Python versions.")
            print("  allrun                Run a command in all virtual environments.")
            print("  3.x                   Run a command in the virtual environment for Python 3.x.")
            print("  clean                 Delete build artifacts and cache files.")
            print("  vscode                Configure VSCode to work on this project.")
            if Path(".venv").exists():
                print("\nAvailable tasks")
                commands.run("default", "duty", "-d", str(duties), "--list")
        return 0

    while len(sys.argv) > 1:
        cmd = sys.argv[1]
        sys.argv.pop(1)

        if cmd == "run":
            commands.run("default", *sys.argv[1:])
            return 0

        if cmd == "multirun":
            commands.multirun(*sys.argv[1:])
            return 0

        if cmd == "allrun":
            commands.allrun(*sys.argv[1:])
            return 0

        if cmd.startswith("3."):
            commands.run(cmd, *sys.argv[1:])
            return 0

        opts, shift_count = commands.options(*sys.argv[1:])
        sys.argv = sys.argv[shift_count + 1:]

        if cmd == "clean":
            commands.clean()
        elif cmd == "install":
            commands.install()
        elif cmd == "vscode":
            commands.vscode()
        elif cmd == "check":
            commands.multirun("duty", "-d", str(duties), "check-quality", "check-types", "check-docs")
            commands.run("default", "duty", "-d", str(duties), "check-api")
        elif cmd in {"check-quality", "check-docs", "check-types", "test"}:
            commands.multirun("duty", "-d", str(duties), cmd, *opts)
        else:
            commands.run("default", "duty", "-d", str(duties), cmd, *opts)

    return 0
