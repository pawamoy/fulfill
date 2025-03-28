#!/usr/bin/env python3

from contextlib import contextmanager
import os
import subprocess
import shutil
from pathlib import Path

PYTHON_VERSIONS = os.getenv('PYTHON_VERSIONS', '3.8 3.9 3.10 3.11 3.12 3.13').split()

exe = ""
prefix = ""


def shell(cmd: str) -> None:
    subprocess.run(cmd, shell=True, check=True)

@contextmanager
def environ(**kwargs):
    original = dict(os.environ)
    os.environ.update(kwargs)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)


def uv_install():
    uv_opts = ""
    if "UV_RESOLUTION" in os.environ:
        uv_opts = f"--resolution={os.getenv('UV_RESOLUTION')}"
    deps_files = ["pyproject.toml"]
    if Path("devdeps.txt").exists():
        deps_files.append("devdeps.txt")
    else:
        devdeps = Path(__file__).parent.joinpath("data", "devdeps.txt")
        deps_files.append(str(devdeps))
    cmd = f"uv pip compile {uv_opts} pyproject.toml {' '.join(deps_files)} | uv pip install -r -"
    shell(cmd)
    if "CI" not in os.environ:
        shell("uv pip install --no-deps -e .")
    else:
        shell("uv pip install --no-deps .")


def install():
    print("Installing dependencies (default environment)")
    default_venv = Path(".venv")
    if not default_venv.exists():
        shell("uv venv --python python")
    uv_install()

    if PYTHON_VERSIONS:
        for version in PYTHON_VERSIONS:
            print(f"Installing dependencies (python{version})")
            venv_path = Path(f".venvs/{version}")
            if not venv_path.exists():
                shell(f"uv venv --python {version} {venv_path}")
            with environ(VIRTUAL_ENV=str(venv_path.resolve())):
                uv_install()
            print()

def activate(path):
    global exe, prefix

    if (bin := Path(path, "bin")).exists():
        activate_script = bin / "activate_this.py"
    elif (scripts := Path(path, "Scripts")).exists():
        activate_script = scripts / "activate_this.py"
        exe = ".exe"
        prefix = f"{path}/Scripts/"
    else:
        raise ValueError(f"make: activate: Cannot find activation script in {path}")

    if not activate_script.exists():
        raise ValueError(f"make: activate: Cannot find activation script in {path}")

    exec(activate_script.read_text(), dict(__file__=str(activate_script)))


def run(version, cmd, *args):
    if version == "default":
        activate(".venv")
        subprocess.run([f"{prefix}{cmd}{exe}", *args], check=True)
    else:
        activate(f".venvs/{version}")
        os.environ["MULTIRUN"] = "1"
        subprocess.run([f"{prefix}{cmd}{exe}", *args], check=True)


def multirun(cmd, *args):
    if PYTHON_VERSIONS:
        for version in PYTHON_VERSIONS:
            run(version, cmd, *args)
    else:
        run("default", cmd, *args)


def allrun(cmd, *args):
    run("default", cmd, *args)
    if PYTHON_VERSIONS:
        multirun(cmd, *args)


def clean():
    paths_to_clean = [
        "build", "dist", "htmlcov", "site", ".coverage*", ".pdm-build"
    ]
    for path in paths_to_clean:
        shell(f"rm -rf {path}")
    
    cache_dirs = [
        ".cache", ".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__"
    ]
    for path in Path(".").rglob("*"):
        if any(path.match(pattern) for pattern in cache_dirs) and not (path.match(".venv") or path.match(".venvs")):
            shutil.rmtree(path)


def vscode():
    Path(".vscode").mkdir(parents=True, exist_ok=True)
    shell("cp -v config/vscode/* .vscode")


def options(*args):
    shift_count = 0
    opts = []
    for arg in args:
        if arg.startswith("-") or "=" in arg:
            opts.append(arg)
            shift_count += 1
        else:
            break
    return opts, shift_count
