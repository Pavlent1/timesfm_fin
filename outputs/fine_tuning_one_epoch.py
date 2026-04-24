import ml_collections


def get_config():
  config = ml_collections.ConfigDict()

  config.dataset_path = ''

  config.context_len = config.input_len = 512
  config.output_len = 128
  config.horizon_len = 128

  config.learning_rate = 1e-4
  config.warmup_epochs = 1
  config.momentum = 0.9
  config.batch_size = 1
  config.num_epochs = 2
  config.seed = 0

  config.epochs_per_checkpoint = 1

  return config


def metrics():
  return [
      'train_loss',
      'eval_loss',
      'train_accuracy',
      'eval_accuracy',
      'steps_per_second',
      'train_learning_rate',
  ]
