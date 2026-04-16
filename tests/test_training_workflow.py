from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.contract


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_environment_module():
    return pytest.importorskip("training_environment")


def test_training_environment_capture_records_python_packages_git_config_and_bundle_identity(
    monkeypatch,
    tmp_path,
) -> None:
    module = load_environment_module()
    requirements_path = tmp_path / "requirements.training.txt"
    requirements_path.write_text("timesfm[pax]==1.3.0\njax==0.4.26\n", encoding="utf-8")
    bundle_manifest_path = tmp_path / "dataset_manifest.json"
    bundle_manifest_path.write_text(
        json.dumps({"manifest_id": "bundle-123"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "capture_pip_freeze",
        lambda python_executable=None: ["timesfm==1.3.0", "jax==0.4.26"],
    )
    monkeypatch.setattr(module, "resolve_git_commit", lambda repo_root=None: "abc1234")

    snapshot = module.capture_training_environment(
        requirements_path=requirements_path,
        config_path=Path("configs/fine_tuning.py"),
        bundle_manifest_path=bundle_manifest_path,
        command=["python", "src/main.py"],
    )

    assert snapshot["manual_only"] is True
    assert snapshot["git_commit"] == "abc1234"
    assert snapshot["config_path"] == "configs/fine_tuning.py"
    assert snapshot["bundle_manifest_id"] == "bundle-123"
    assert snapshot["package_snapshot"] == ["timesfm==1.3.0", "jax==0.4.26"]
    assert snapshot["requirements_file"].endswith("requirements.training.txt")


def test_requirements_training_file_freezes_supported_manual_stack() -> None:
    load_environment_module()
    requirements_path = REPO_ROOT / "requirements.training.txt"
    if not requirements_path.exists():
        pytest.skip("03-03 requirements training freeze has not been implemented yet.")

    lines = [
        line.strip()
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

    assert "timesfm[pax]==1.3.0" in lines
    assert any(line.startswith("jax==") for line in lines)
    assert any(line.startswith("jaxlib==") for line in lines)
    assert any(line.startswith("paxml==") for line in lines)
    assert any(line.startswith("tensorflow") for line in lines)


def test_environment_snapshot_can_point_back_to_requirements_file(tmp_path) -> None:
    module = load_environment_module()
    requirements_path = tmp_path / "requirements.training.txt"
    requirements_path.write_text("timesfm[pax]==1.3.0\n", encoding="utf-8")

    snapshot = module.capture_training_environment(
        requirements_path=requirements_path,
        config_path=Path("configs/fine_tuning.py"),
        bundle_manifest_path=None,
        packages=["timesfm==1.3.0"],
        git_commit="deadbeef",
    )
    output_path = tmp_path / "environment_snapshot.json"
    module.write_environment_snapshot(snapshot, output_path)

    saved = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.exists()
    assert saved["requirements_file"] == str(requirements_path)
    assert saved["manual_only"] is True
