# `src/train.py`

This is the primary fine-tuning implementation built on JAX, PaxML, and Praxis. It prepares CSV data into TensorFlow datasets, validates the effective training shape through `src/training_shapes.py`, masks training inputs, adapts the upstream patched decoder into a finance-specific fine-tuning model, runs pmapped training and evaluation steps, logs metrics, and saves PaxML checkpoints during training.

Key responsibilities:

- transform wide CSV price data into shuffled train and eval datasets
- build masked training inputs and unmasked eval batches that now respect the configured `context_len + output_len` window shape
- define the custom `PatchedDecoderFinetuneFinance` loss behavior on top of TimesFM's patched decoder
- configure the Pax learner and schedule
- initialize model state from the upstream TimesFM checkpoint
- run multi-device training, periodic evaluation, TensorBoard logging, and checkpoint persistence

Important interactions:

- uses helper functions from `src/utils.py`
- relies on `src/training_shapes.py` so `input_len`, `context_len`, `output_len`, `horizon_len`, and `output_patch_len` stay internally consistent
- is called by `src/main.py`
- shares several data-preparation and model-wrapper pieces with `src/evaluation.py`

Category: training pipeline.
