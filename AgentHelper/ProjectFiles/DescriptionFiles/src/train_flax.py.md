# `src/train_flax.py`

This file is an older, explicitly deprecated alternative training implementation based on lower-level JAX and Flax patterns instead of PaxML/Praxis. The header comment says it remains mostly as reference code, and the implementation includes its own train and eval steps, checkpoint helpers, data preprocessing, and metric calculations.

Later agents should treat this file as legacy experimentation code, not the preferred training path. It still matters because it documents prior assumptions about masking, evaluation horizons, checkpoint handling, and optimizer setup that may explain older experiments or artifacts.

Category: deprecated training pipeline.
