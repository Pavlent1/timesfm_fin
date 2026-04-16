from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


DEFAULT_CONTEXT_LEN = 512
DEFAULT_INPUT_LEN = 512
DEFAULT_OUTPUT_LEN = 128
DEFAULT_HORIZON_LEN = 128
DEFAULT_OUTPUT_PATCH_LEN = 128


@dataclass(frozen=True)
class TrainingShape:
    context_len: int
    input_len: int
    output_len: int
    horizon_len: int
    output_patch_len: int

    @property
    def window_length(self) -> int:
        return self.context_len + self.output_len

    def to_dict(self) -> dict[str, int]:
        payload = asdict(self)
        payload["window_length"] = self.window_length
        return payload


def _config_value(config: Any, name: str, default: int) -> int:
    if isinstance(config, Mapping):
        value = config.get(name, default)
    else:
        value = getattr(config, name, default)
    return int(value)


def resolve_training_shape(
    config: Any,
    *,
    overrides: Mapping[str, int | None] | None = None,
) -> TrainingShape:
    overrides = overrides or {}
    shape = TrainingShape(
        context_len=int(overrides.get("context_len") or _config_value(config, "context_len", DEFAULT_CONTEXT_LEN)),
        input_len=int(overrides.get("input_len") or _config_value(config, "input_len", DEFAULT_INPUT_LEN)),
        output_len=int(overrides.get("output_len") or _config_value(config, "output_len", DEFAULT_OUTPUT_LEN)),
        horizon_len=int(overrides.get("horizon_len") or _config_value(config, "horizon_len", DEFAULT_HORIZON_LEN)),
        output_patch_len=int(
            overrides.get("output_patch_len")
            or _config_value(config, "output_patch_len", DEFAULT_OUTPUT_PATCH_LEN)
        ),
    )
    validate_training_shape(shape)
    return shape


def validate_training_shape(shape: TrainingShape) -> None:
    values = shape.to_dict()
    for key, value in values.items():
        if value <= 0:
            raise ValueError(f"{key} must be a positive integer.")

    if shape.input_len != shape.context_len:
        raise ValueError(
            "The legacy TimesFM training path requires input_len to match context_len."
        )

    if shape.output_len != shape.horizon_len:
        raise ValueError(
            "The legacy TimesFM training path requires output_len and horizon_len to match."
        )

    if shape.output_patch_len < shape.output_len:
        raise ValueError(
            "output_patch_len must be greater than or equal to output_len."
        )

    if shape.context_len <= shape.output_len:
        raise ValueError(
            "context_len must be greater than output_len for random masking."
        )


def validate_bundle_window_length(*, window_length: int, shape: TrainingShape) -> None:
    expected = shape.window_length
    if int(window_length) != expected:
        raise ValueError(
            "Prepared bundle window_length does not match the effective training shape. "
            f"Expected {expected}, got {window_length}."
        )
