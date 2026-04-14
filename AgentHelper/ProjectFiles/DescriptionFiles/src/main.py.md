# `src/main.py`

This file is the legacy top-level training or evaluation entrypoint for the fine-tuning workflow. It defines `absl.flags`, loads the config file from `configs/fine_tuning.py`, constructs a `timesfm.TimesFm` model around either a supplied checkpoint path or the base Google checkpoint, and then dispatches to either `src/train.py` or `src/evaluation.py`.

Important behaviors:

- requires `workdir`, `dataset_path`, and `config`
- mutates `config.dataset_path` from the CLI flag before dispatch
- selects evaluation mode with `--do_eval`
- hardcodes the training model hyperparameters and uses `backend='gpu'`

Category: training/evaluation entrypoint.
