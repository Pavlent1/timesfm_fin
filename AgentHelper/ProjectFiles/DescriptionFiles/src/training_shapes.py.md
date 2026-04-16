# `src/training_shapes.py`

Lightweight shape-validation helper shared by the legacy training entrypoint and the manual PostgreSQL wrapper.

Key responsibilities:

- define the validated training-shape contract for `context_len`, `input_len`, `output_len`, `horizon_len`, and `output_patch_len`
- enforce the legacy training constraint that `input_len == context_len` and `output_len == horizon_len`
- compute the implied prepared-bundle `window_length`
- reject bundle/config combinations that would silently keep using the wrong legacy shape

Important interactions:

- called by `src/main.py` before building `timesfm.TimesFmHparams`
- called by `src/train.py` before the pmapped training/eval loop
- called by `src/train_from_postgres.py` before copying configs or launching a real run

Category: training shape contract helper.
