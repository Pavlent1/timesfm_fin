# `src/main.py`

This file is the legacy top-level training or evaluation entrypoint for the fine-tuning workflow. It defines `absl.flags`, loads the config file from `configs/fine_tuning.py`, constructs a `timesfm.TimesFm` model around either a supplied checkpoint path, a supplied Hugging Face repo id, or the base Google checkpoint, and then dispatches to either `src/train.py` or `src/evaluation.py`.

Important behaviors:

- requires `workdir`, `dataset_path`, and `config`
- mutates `config.dataset_path` from the CLI flag before dispatch
- selects evaluation mode with `--do_eval`
- accepts either `--checkpoint_path` or `--checkpoint_repo_id` for explicit parent selection
- still falls back to the Google base checkpoint when neither explicit parent flag is provided
- now accepts an explicit `--backend` flag instead of hardcoding GPU

Category: training/evaluation entrypoint.
