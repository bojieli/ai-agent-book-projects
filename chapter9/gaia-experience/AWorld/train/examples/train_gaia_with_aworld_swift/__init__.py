from swift.trainers import TrainerFactory

TrainerFactory.TRAINER_MAPPING["aworld_grpo"] = 'train.examples.train_gaia_with_aworld_swift.AworldTrainer'
TrainerFactory.TRAINING_ARGS_MAPPING["aworld_grpo"] = 'train_gaia_with_aworld_swift.trainers.GRPOConfig'
