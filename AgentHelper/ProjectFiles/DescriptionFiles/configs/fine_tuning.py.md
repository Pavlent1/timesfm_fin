# `configs/fine_tuning.py`

This file defines the default fine-tuning hyperparameter bundle for the older training pipeline. It returns an `ml_collections.ConfigDict` with dataset location, sequence lengths, optimizer settings, batch size, epoch count, random seed, and checkpoint cadence.

Its main role is to supply `src/main.py` with a locked config file that is then passed into `src/train.py` or `src/evaluation.py`. The values in this file are training-oriented rather than inference-oriented, so later agents should treat it as experiment configuration, not runtime application logic.

Category: training config.
