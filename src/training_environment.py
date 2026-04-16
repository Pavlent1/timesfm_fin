from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]


def normalize_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.as_posix()


def capture_pip_freeze(python_executable: str | None = None) -> list[str]:
    command = [python_executable or sys.executable, "-m", "pip", "freeze"]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    ]
    return sorted(lines)


def resolve_git_commit(repo_root: Path | None = None) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root or REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_bundle_manifest_identity(bundle_manifest_path: Path | None) -> str | None:
    if bundle_manifest_path is None:
        return None

    payload = json.loads(bundle_manifest_path.read_text(encoding="utf-8"))
    return payload.get("manifest_id")


def capture_training_environment(
    *,
    requirements_path: Path,
    config_path: Path,
    bundle_manifest_path: Path | None,
    python_executable: str | None = None,
    packages: Sequence[str] | None = None,
    git_commit: str | None = None,
    command: Sequence[str] | None = None,
) -> dict[str, object]:
    resolved_requirements = requirements_path.resolve()
    package_snapshot = list(packages) if packages is not None else capture_pip_freeze(python_executable)

    return {
        "manual_only": True,
        "captured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python_version": platform.python_version(),
        "python_executable": python_executable or sys.executable,
        "package_snapshot": package_snapshot,
        "git_commit": git_commit or resolve_git_commit(),
        "config_path": normalize_path(config_path),
        "requirements_file": str(resolved_requirements),
        "requirements_sha256": file_sha256(resolved_requirements),
        "bundle_manifest_path": normalize_path(bundle_manifest_path),
        "bundle_manifest_id": load_bundle_manifest_identity(bundle_manifest_path),
        "command": list(command) if command is not None else [],
    }


def write_environment_snapshot(snapshot: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
