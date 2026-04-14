from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.contract


REPO_ROOT = Path(__file__).resolve().parents[1]


def find_powershell() -> str:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        pytest.skip("PowerShell is not available in this environment.")
    return powershell


def test_run_crypto_backtest_wrapper_builds_expected_docker_command(tmp_path) -> None:
    powershell = find_powershell()
    docker_cmd = tmp_path / "docker.cmd"
    docker_log = tmp_path / "docker.log"
    docker_cmd.write_text(
        "@echo off\r\n"
        f">> \"{docker_log}\" echo %*\r\n"
        "exit /b 0\r\n",
        encoding="ascii",
    )

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path};{env['PATH']}"

    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(REPO_ROOT / "scripts" / "run_crypto_backtest.ps1"),
            "-SkipBuild",
            "-Live",
            "-Backend",
            "gpu",
            "-Symbol",
            "ETHUSDT",
            "-Day",
            "2024-04-01",
            "-ContextLen",
            "64",
            "-HorizonLen",
            "8",
            "-Stride",
            "4",
            "-BatchSize",
            "16",
            "-Freq",
            "2",
            "-MaxWindows",
            "5",
            "-OutputCsv",
            "/workspace/live.csv",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    logged_command = docker_log.read_text(encoding="utf-8").strip()

    assert "Running crypto minute backtest" in result.stdout
    assert "run --rm --gpus all" in logged_command
    assert "--add-host host.docker.internal:host-gateway" in logged_command
    assert "-e POSTGRES_HOST=host.docker.internal" in logged_command
    assert "-e POSTGRES_PORT=54329" in logged_command
    assert f"-v {REPO_ROOT}:/workspace" in logged_command
    assert "--entrypoint python" in logged_command
    assert "src/crypto_minute_backtest.py" in logged_command
    assert "--symbol ETHUSDT" in logged_command
    assert "--context-len 64" in logged_command
    assert "--horizon-len 8" in logged_command
    assert "--stride 4" in logged_command
    assert "--batch-size 16" in logged_command
    assert "--backend gpu" in logged_command
    assert "--freq 2" in logged_command
    assert "--day 2024-04-01" in logged_command
    assert "--max-windows 5" in logged_command
    assert "--mode live" in logged_command
    assert "--output-csv /workspace/live.csv" in logged_command
    assert "--db-path" not in logged_command


def test_run_crypto_backtest_wrapper_defaults_to_cpu_backend(tmp_path) -> None:
    powershell = find_powershell()
    docker_cmd = tmp_path / "docker.cmd"
    docker_log = tmp_path / "docker.log"
    docker_cmd.write_text(
        "@echo off\r\n"
        f">> \"{docker_log}\" echo %*\r\n"
        "exit /b 0\r\n",
        encoding="ascii",
    )

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path};{env['PATH']}"

    subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(REPO_ROOT / "scripts" / "run_crypto_backtest.ps1"),
            "-SkipBuild",
            "-Day",
            "2024-04-01",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    logged_command = docker_log.read_text(encoding="utf-8").strip()

    assert "--backend cpu" in logged_command
    assert "--gpus all" not in logged_command
    assert "--day 2024-04-01" in logged_command
    assert "--mode live" not in logged_command


def test_dockerfile_installs_shared_runtime_requirements_for_backtest() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY requirements.inference.txt /workspace/requirements.inference.txt" in dockerfile
    assert '"timesfm[pax]==1.3.0"' in dockerfile
    assert "-r /workspace/requirements.inference.txt" in dockerfile


def test_setup_windows_script_rejects_non_310_python(tmp_path) -> None:
    powershell = find_powershell()
    python_cmd = tmp_path / "python.cmd"
    python_cmd.write_text(
        "@echo off\r\n"
        "if \"%1\"==\"-c\" (\r\n"
        "  echo 3.11.9\r\n"
        "  exit /b 0\r\n"
        ")\r\n"
        "exit /b 0\r\n",
        encoding="ascii",
    )

    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(REPO_ROOT / "scripts" / "setup_windows.ps1"),
            "-PythonExe",
            str(python_cmd),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "needs Python 3.10" in combined_output
    assert "Found Python 3.11.9" in combined_output
