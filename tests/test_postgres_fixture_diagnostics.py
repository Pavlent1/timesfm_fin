from __future__ import annotations

import subprocess

import pytest

import conftest as postgres_test_support


def test_run_checked_command_reports_missing_docker_binary(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("docker")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as exc_info:
        postgres_test_support.run_checked_command("docker", "compose", "up", "-d", "postgres")

    message = str(exc_info.value)
    assert "Docker command failed while preparing PostgreSQL test fixtures." in message
    assert "docker compose up -d postgres" in message
    assert "installed and running" in message


def test_run_checked_command_reports_compose_failure_details(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["docker", "compose", "up", "-d", "postgres"],
            output="compose stdout",
            stderr="compose stderr",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as exc_info:
        postgres_test_support.run_checked_command("docker", "compose", "up", "-d", "postgres")

    message = str(exc_info.value)
    assert "Docker command failed while preparing PostgreSQL test fixtures." in message
    assert "code 1" in message
    assert "compose stdout" in message
    assert "compose stderr" in message
