import os
from absl import app
from absl import flags
from absl import logging
from clu import platform
import jax
from ml_collections import config_flags
import timesfm

import train
import evaluation
from training_shapes import resolve_training_shape

import warnings
warnings.filterwarnings("ignore")


FLAGS = flags.FLAGS

flags.DEFINE_string('workdir', None, 'Directory to store model data.')
flags.DEFINE_string('dataset_path', None, 'Path to training/test dataset')
flags.DEFINE_bool('do_eval', False, 'Evaluation mode.')
flags.DEFINE_string('checkpoint_path', None, 'Path to checkpoint.')
flags.DEFINE_string('checkpoint_repo_id', None, 'Hugging Face repo id for the parent checkpoint.')
flags.DEFINE_enum('backend', 'gpu', ['cpu', 'gpu', 'tpu'], 'Backend for TimesFM runtime.')

config_flags.DEFINE_config_file(
    'config',
    None,
    'File path to the training hyperparameter configuration.',
    lock_config=True,
)

def main(argv):
  config = FLAGS.config
  workdir = FLAGS.workdir
  do_eval = FLAGS.do_eval
  checkpoint_path = FLAGS.checkpoint_path
  checkpoint_repo_id = FLAGS.checkpoint_repo_id
  config.dataset_path = FLAGS.dataset_path
  training_shape = resolve_training_shape(config)

  hparams = timesfm.TimesFmHparams(
    context_len=training_shape.context_len,
    horizon_len=training_shape.horizon_len,
    input_patch_len=32,
    output_patch_len=training_shape.output_patch_len,
    num_layers=20,
    model_dims=1280,
    backend=FLAGS.backend
  )

  if checkpoint_path is not None:
    checkpoint = timesfm.TimesFmCheckpoint(
      version='jax',
      path=checkpoint_path,
    )
  elif checkpoint_repo_id is not None:
    checkpoint = timesfm.TimesFmCheckpoint(
      version='jax',
      huggingface_repo_id=checkpoint_repo_id,
    )
  else:
    checkpoint = timesfm.TimesFmCheckpoint(
      version='jax',
      huggingface_repo_id="google/timesfm-1.0-200m",
    )

  tfm = timesfm.TimesFm(hparams=hparams, checkpoint=checkpoint)
  
  if do_eval:
    evaluation.restore_and_evaluate(tfm, config, workdir)
  else:
    train.train_and_evaluate(tfm, config, workdir)


if __name__ == '__main__':
  flags.mark_flags_as_required(['config', 'workdir', 'dataset_path'])
  app.run(main)
