# `src/utils.py`

This module contains small numerical helpers used by the older training and evaluation pipeline. It provides confusion-matrix utilities, return calculations, a warmup-plus-cosine learning-rate schedule, an SGD optimizer factory, and two loss helpers built on `optax`.

The file is shared by `src/train.py` and `src/evaluation.py`. Its functions are infrastructure for model training metrics rather than business logic, and several helpers assume JAX or Optax array types.

Category: training utility module.
