# `src/evaluation.py`

This module restores the fine-tuning model stack for offline evaluation across multiple forecast horizons. It rebuilds the Pax task and model wrapper, loads evaluation data through `src.train.preprocess_csv`, reuses `src.train.eval_step`, and logs loss plus classification-style accuracy for each requested horizon length.

Key responsibilities:

- reconstruct the same patched-decoder task shape used during fine-tuning
- initialize model state from the supplied TimesFM checkpoint-backed model object
- iterate over evaluation batches for several horizon lengths
- compute horizon-specific losses and confusion-matrix accuracy summaries

Important interactions:

- called by `src/main.py` when `--do_eval` is set
- imports several helpers directly from `src/train.py`
- uses `src/utils.py` for accuracy and metric support

Category: evaluation pipeline.
