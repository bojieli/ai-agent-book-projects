# veRL Training Process: Complete System Analysis

**Based on**: [SimpleVLA-RL: Scaling VLA Training via Reinforcement Learning](https://arxiv.org/pdf/2509.09674) (2025)

## Table of Contents
1. [Overall Architecture](#overall-architecture)
2. [Training Configuration](#training-configuration)
3. [Complete Training Loop](#complete-training-loop)
4. [Phase 1: Rollout with Dynamic Sampling](#phase-1-rollout-with-dynamic-sampling)
5. [Phase 2: Outcome Reward Modeling](#phase-2-outcome-reward-modeling)
6. [Phase 3: Advantage Estimation (GRPO)](#phase-3-advantage-estimation-grpo)
7. [Phase 4: Actor Update (PPO with Clip Higher)](#phase-4-actor-update-ppo-with-clip-higher)
8. [Phase 5: Validation](#phase-5-validation)
9. [Data Flow and Synchronization](#data-flow-and-synchronization)
10. [Performance Analysis](#performance-analysis)
11. [Key Paper Insights](#key-paper-insights)

---

## Overall Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Ray Framework                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ ActorRollout   │  │    Critic      │  │   RefPolicy    │   │
│  │   Worker       │  │    Worker      │  │    Worker      │   │
│  │  (8 GPUs)      │  │  (8 GPUs)      │  │  (8 GPUs)      │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
│         ↓                    ↓                    ↓             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Shared GPU Resource Pool                       │  │
│  │         [GPU 0, GPU 1, ..., GPU 7]                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │  RayTrainer     │
                    │  (Main Process) │
                    └─────────────────┘
```

**Key Components** (from `main_ppo.py:159-173`):
```python
role_worker_mapping = {
    Role.ActorRollout: ray.remote(RobActorRolloutRefWorker),  # VLA model for rollout & training
    Role.Critic: ray.remote(CriticWorker),                     # Value network (GAE only)
    Role.RefPolicy: ray.remote(RobActorRolloutRefWorker)      # Frozen reference policy (KL penalty)
}

resource_pool_spec = {
    'global_pool': [8] * 1,  # 8 GPUs on 1 node
}

mapping = {
    Role.ActorRollout: 'global_pool',
    Role.Critic: 'global_pool',
    Role.RefPolicy: 'global_pool',
}
```

**Worker Responsibilities**:
1. **ActorRollout Worker**: 
   - Generate rollouts in environments
   - Compute log probabilities
   - Update actor policy (backpropagation)
   - Compute entropy for exploration

2. **Critic Worker** (optional, only for GAE):
   - Estimate value function V(s)
   - Used for advantage estimation

3. **RefPolicy Worker** (optional, only if `kl_coef > 0`):
   - Compute reference log probabilities from frozen SFT model
   - Used for KL penalty regularization

---

## Training Configuration

From `run_openvla_oft_rl_twin2.sh`:

### Dataset Configuration
```bash
data.task_suite_name=robotwin2_beat_block_hammer
data.num_trials_per_task=1000           # 1000 task instances
data.n_samples=8                        # 8 rollouts per task instance
data.train_batch_size=64                # 64 task instances per training step
data.val_batch_size=256                 # 256 for validation
data.oversample_factor=1                # No oversampling
```

### Model Configuration
```bash
actor_rollout_ref.model.path=$SFT_MODEL_PATH              # OpenVLA-7B SFT model
actor_rollout_ref.model.vla=openvla-oft
actor_rollout_ref.model.action_token_len=14               # 14 tokens per action
actor_rollout_ref.model.action_chunks_len=25              # 25 action chunks per VLA call
```

### Training Configuration
```bash
# Optimization
actor_rollout_ref.actor.optim.lr=5e-6
actor_rollout_ref.actor.ppo_mini_batch_size=128           # Mini-batch size for PPO updates
actor_rollout_ref.actor.ppo_micro_batch_size=8            # Micro-batch size (= num_gpus)

# PPO Hyperparameters  
actor_rollout_ref.actor.clip_ratio_high=0.28             # PPO clip ratio upper bound
actor_rollout_ref.actor.clip_ratio_low=0.2               # PPO clip ratio lower bound
actor_rollout_ref.actor.entropy_coeff=0.0                # No entropy bonus
actor_rollout_ref.actor.grad_clip=1                      # Gradient clipping

# Advantage Estimation
algorithm.adv_estimator=grpo                              # GRPO (Group Relative Policy Optimization)
algorithm.kl_ctrl.kl_coef=0.00                           # No KL penalty (RefPolicy disabled)

# Training Schedule
trainer.total_epochs=100                                  # 100 epochs
trainer.save_freq=20                                      # Save checkpoint every 20 steps
trainer.test_freq=4                                       # Validate every 4 steps
trainer.val_before_train=True                             # Run validation before training
```

### Computed Training Parameters

**IMPORTANT: Terminology Clarification**

There are THREE different types of "steps" in this system:

1. **Training Steps (global_steps)**: Main training loop iterations
   - This is what we mean by "1500 steps"
   - One training step = collect rollouts + update policy
   
2. **Environment Steps**: Physical actions executed in simulation
   - Maximum 200 per rollout for beat_block_hammer task
   - These are the actual robot control steps
   
3. **VLA Inference Steps**: Number of VLA model forward passes
   - 200 env steps ÷ 25 action_chunks_len = 8 VLA calls per rollout
   - Each VLA call generates 25 action chunks

**Dataset Size** (from `rob_dataset.py:171-197`):
```python
# For RoboTwin 2.0, loads pre-collected feasible seeds
train_dataset_size = num_trials_per_task = 1000 task instances

# Training dataloader
train_batch_size = 64 * oversample_factor = 64
shuffle = True
drop_last = True

# Training steps per epoch (NOT environment steps!)
steps_per_epoch = train_dataset_size // train_batch_size 
                = 1000 // 64 = 15 training steps (last 40 samples dropped)
```

**Total Training Steps** (from `ray_trainer.py:329-334`):
```python
total_training_steps = len(train_dataloader) * total_epochs
                     = 15 * 100 = 1500 training steps (per config)
```

**⚠️ INCONSISTENCY ALERT**: The paper ([SimpleVLA-RL](https://arxiv.org/pdf/2509.09674), Figure 3) shows training curves up to **300 RL Training Steps**, not 1500!

This means either:
1. **Paper uses fewer epochs**: `300 / 15 = 20 epochs` instead of 100
2. **Config is for extended training**: The provided config may be for experiments beyond the paper
3. **Partial results shown**: Paper may show early results from longer runs

**Most likely**: The paper experiments used `trainer.total_epochs=20` (300 steps), while the provided config has `trainer.total_epochs=100` for extended training.

---

## Complete Training Loop

### High-Level Structure (from `ray_trainer.py:469-717`)

```python
def fit(self):
    global_steps = 0
    
    # ========== Initial Validation (Optional) ==========
    if val_before_train:
        val_metrics = self._validate(global_steps=0)
        # Runs 256 rollouts without training
    
    # ========== Main Training Loop ==========
    for epoch in range(total_epochs):  # 100 epochs
        self.train_dataloader.start_new_epoch()
        
        while True:  # Inner loop: process all batches in epoch
            # ------------------ Step 1: Rollout ------------------
            # Collect batch_size * n_samples = 64 * 8 = 512 rollouts
            valid_batch = []
            while len(valid_batch) < batch_size * n_samples:
                batch_dict = train_dataloader.get_next_batch()  # Get 64 task instances
                
                # Generate 8 rollouts per task instance
                gen_batch_output = actor_rollout_wg.generate_sequences(batch_dict)
                
                # Verify success and compute raw scores
                scores_tensor = reward_fn.verify(gen_batch_output)
                
                # Filter by accuracy if enabled
                filtered_batch = self.filter(scores_tensor, gen_batch_output, n_samples=8)
                
                valid_batch.append(filtered_batch)
            
            # ------------------ Step 2: Reference Policy (Optional) ------------------
            if use_reference_policy:
                ref_log_prob = ref_policy_wg.compute_ref_log_prob(valid_batch)
                valid_batch.union(ref_log_prob)
            
            # ------------------ Step 3: Reward Computation ------------------
            reward_tensor_dict, reward_metrics = reward_fn(valid_batch)
            valid_batch['token_level_scores'] = reward_tensor_dict['all']
            
            # Apply KL penalty if using reference policy
            valid_batch, kl_metrics = apply_kl_penalty(valid_batch, kl_ctrl)
            
            # ------------------ Step 4: Advantage Estimation ------------------
            valid_batch = compute_advantage(valid_batch, gamma, lam, adv_estimator='grpo')
            
            # ------------------ Step 5: Actor Update (Backpropagation) ------------------
            if global_steps >= critic_warmup:
                actor_output = actor_rollout_wg.update_actor(valid_batch)
                entropy_output = actor_rollout_wg.compute_entropy(valid_batch)
            
            # ------------------ Step 6: Validation ------------------
            if (global_steps + 1) % test_freq == 0:  # Every 4 steps
                val_metrics = self._validate(global_steps)
            
            # ------------------ Step 7: Checkpoint Saving ------------------
            if (global_steps + 1) % save_freq == 0:  # Every 20 steps
                actor_rollout_wg.save_checkpoint(checkpoint_path)
            
            global_steps += 1
            
            if len(valid_batch) == 0:  # Epoch exhausted
                break
    
    # ========== Final Validation ==========
    val_metrics = self._validate(global_steps=global_steps)
```

### Training Summary

| Metric | Value | Calculation | Notes |
|--------|-------|-------------|-------|
| **Epochs (Config File)** | 100 | `trainer.total_epochs=100` | Extended training |
| **Epochs (Paper)** | **20** | Inferred from Figure 3 | **Actual paper experiments** |
| **Training Steps per Epoch** | 15 | `1000 tasks // 64 batch_size` | Main loop iterations |
| **Total Training Steps (Config)** | 1,500 | `15 × 100 epochs` | If using config as-is |
| **Total Training Steps (Paper)** | **300** | `15 × 20 epochs` | **Shown in Figure 3** |
| **Rollouts per Training Step** | 512 | `64 tasks × 8 samples` | - |
| **Total Rollouts (Paper)** | **153,600** | `300 × 512 rollouts` | **For 300 steps** |
| **Env Steps per Rollout** | ~50-200 | Varies by task success | Physical robot actions |
| **VLA Calls per Rollout** | ~2-8 | `env_steps / 25` | Model forward passes |
| **Total Env Steps (Paper)** | ~15M | `153.6k × 100 avg` | **For 300 steps** |
| **Total VLA Inferences (Paper)** | ~600k | `153.6k × 4 avg` | **For 300 steps** |
| **Validations (Paper)** | **75** | `300 // 4 test_freq` | Every 4 training steps |
| **Checkpoints (Paper)** | **15** | `300 // 20 save_freq` | Every 20 training steps |

---

## Phase 1: Rollout

### Rollout Process (from `ray_trainer.py:513-556`)

```python
# 1. Load task batch from dataset
batch_dict = train_dataloader.get_next_batch()
# Returns: {
#   'task_suite_name': ['robotwin2_beat_block_hammer'] * 64,
#   'task_id': [-1] * 64,
#   'trial_id': [seed_1, seed_2, ..., seed_64],  # From pre-collected feasible seeds
#   'trial_seed': [seed_1, seed_2, ..., seed_64],
# }

# 2. Prepare generation batch
gen_batch = DataProto.from_single_dict(batch_dict)
gen_batch.select(batch_keys=['task_id', 'trial_id', 'trial_seed'])

# 3. Expand to n_samples copies (for GRPO/RLOO)
batch_lst = [[batch[i] for _ in range(n_samples)] for i in range(len(batch))]
# Creates 64 × 8 = 512 copies

# 4. Set generation config
gen_batch.meta_info = {
    'eos_token_id': tokenizer.eos_token_id,
    'n_samples': 8,  # Number of samples per task
    'pad_token_id': tokenizer.pad_token_id,
}

# 5. Generate rollouts (distributed across 8 GPUs)
gen_batch_output = actor_rollout_wg.generate_sequences(gen_batch)
```

### Inside `generate_sequences` (from `rob_rollout.py:495-507`)

```python
def generate_sequences(self, prompts):
    batch_size = prompts.batch.batch_size[0]  # 512
    
    # Use different batch sizes for training vs validation
    if prompts.meta_info.get('n_samples') is None:
        micro_batch_size = val_micro_batch_size  # 8 (validation)
    else:
        micro_batch_size = config.micro_batch_size  # 1 (training)
    
    num_chunks = max(batch_size // micro_batch_size, 1)  # 512 // 1 = 512 chunks
    batch_prompts = prompts.chunk(chunks=num_chunks)
    
    # Process each chunk sequentially (but distributed across GPUs by Ray)
    output = [self._generate_minibatch(p) for p in batch_prompts]
    output = DataProto.concat(output)
    
    return output
```

### Detailed Rollout Execution (from `rob_rollout.py:609-775`)

For each minibatch (1 task instance with n_samples=8):

```python
def _generate_minibatch_robotwin(prompts):
    # Extract task information
    batch_size = 8  # n_samples
    task_id = [-1] * 8
    trial_id = [same_seed] * 8  # All 8 samples use same seed
    trial_seed = [same_seed] * 8
    task_suite_name = ['robotwin2_beat_block_hammer'] * 8
    
    # ========== 1. Initialize Environments (Parallel) ==========
    env_wrappers = []
    for idx in range(8):
        wrapper = RobotwinEnvWrapper(task_name, trial_id[idx], trial_seed[idx], ...)
        env_wrappers.append(wrapper)
    
    # Initialize all 8 environments in parallel using ThreadPoolExecutor
    init_futures = [thread_pool.submit(w.initialize) for w in env_wrappers]
    wait_for_completion(init_futures)  # ~5-15 seconds (SAPIEN scene creation)
    
    # ========== 2. Collect Initial Observations ==========
    inputs = []
    task_descriptions = []
    for wrapper in env_wrappers:
        obs = wrapper.get_obs()  # Get RGB + proprioception
        instruction = wrapper.get_instruction()
        inputs.append(obs_to_input(obs))
        task_descriptions.append(instruction)
    
    # ========== 3. Main Rollout Loop ==========
    max_steps = 200  # Maximum ENVIRONMENT steps for beat_block_hammer
                     # This is NOT the same as training steps!
                     # These are physical robot control steps
    step = 0  # Current environment step counter
    vla_history = []
    
    while step < max_steps:
        active_indices = [i for i, w in enumerate(env_wrappers) if w.active]
        
        if len(active_indices) == 0:
            break  # All environments done
        
        # --- 3.1 Process VLA Input ---
        vla_input = process_input(inputs, task_descriptions)
        # Converts images to tensors, tokenizes text, normalizes proprio
        # Transfers to GPU, pads sequences
        # Shape: {
        #   'input_ids': (8, seq_len),
        #   'pixel_values': (8, num_images*patches, vision_dim),
        #   'proprio': (8, 14),
        #   'attention_mask': (8, seq_len),
        # }
        
        # --- 3.2 VLA Inference (GPU) ---
        vla_output = _generate_one_step(vla_input)
        # Forward pass through OpenVLA model:
        # - Vision encoder: Extract image features
        # - LLM: Generate action tokens (14 tokens × 25 chunks = 350 tokens)
        # - Action decoder: Convert tokens to continuous actions
        # Output: actions shape (8, 25, 14)
        #   - 25 action chunks
        #   - 14 dimensions (7 DOF × 2 arms)
        
        # --- 3.3 Execute Actions (CPU, Parallel) ---
        step_futures = []
        for idx in active_indices:
            future = thread_pool.submit(env_wrappers[idx].step, vla_output['action'][idx])
            step_futures.append((idx, future))
        
        # Wait for all environments to finish executing 25 action chunks
        new_inputs = []
        for idx, future in step_futures:
            obs, done = future.result()  # ~1500ms for 25 steps
            new_inputs.append(obs_to_input(obs))
            if done:
                env_wrappers[idx].active = False
        
        # --- 3.4 Store Trajectory Data ---
        vla_history.append({
            'responses': vla_output['responses'],        # (8, 25*14) action tokens
            'input_ids': vla_output['input_ids'],        # (8, seq_len) input tokens
            'attention_mask': vla_output['attention_mask'],
            'pixel_values': vla_output['pixel_values'],
            'action': vla_output['action'],              # (8, 25, 14) continuous actions
            'proprio': vla_output['proprio'],            # (8, 14) proprioception
            'step': step
        })
        
        inputs = new_inputs
        step += 25  # Advance by action_chunks_len (environment steps, not training steps!)
                    # After this loop, step will be at most 200 (max_steps)
    
    # ========== 4. Environment Cleanup ==========
    cleanup_futures = [thread_pool.submit(w.close) for w in env_wrappers]
    wait_for_completion(cleanup_futures)
    torch.cuda.empty_cache()
    
    # ========== 5. Prepare Output Batch ==========
    output_batch = prepare_output_batch(vla_history, task_records, batch_size=8)
    # Concatenates all timesteps: shape (8, num_steps, ...)
    # Adds metadata: complete (bool), finish_step (int)
    
    return output_batch
```

### Rollout Output Format

```python
output_batch = {
    'responses': Tensor(8, num_steps, 350),        # Action tokens (25*14)
    'input_ids': Tensor(8, num_steps, seq_len),    # Input token IDs
    'attention_mask': Tensor(8, num_steps, seq_len),
    'pixel_values': Tensor(8, num_steps, patches, dim),
    'proprio': Tensor(8, num_steps, 14),           # Proprioception
    'complete': Tensor(8),                          # Success flags
    'finish_step': Tensor(8),                       # Number of steps executed
}
```

### Rollout Timing Breakdown

For 1 task instance with 8 samples:

| Phase | Duration | Notes |
|-------|----------|-------|
| Environment Init | 5-15s | SAPIEN scene creation (parallel) |
| VLA Inference (×8 steps) | ~2.4s | 300ms × 8, GPU 100% |
| Action Execution (×8 steps) | ~12s | 1500ms × 8, CPU-bound |
| Environment Cleanup | 1-3s | Close scenes, save videos |
| **Total** | **20-30s** | Per minibatch |

For full training step (512 rollouts = 64 tasks × 8 samples):
- With 8 GPUs processing in parallel: **~30-40 seconds**
- Ray schedules 64 tasks across 8 workers dynamically

---

## Phase 2: Reward Computation

### 2.1 Verification (from `ray_trainer.py:559-570`)

```python
# Called during rollout collection
scores_tensor, reward_metrics, format_metrics, _ = reward_fn.verify(roll_batch)
```

### Verification Logic (from `main_ppo.py:42-60`)

```python
def verify(self, data):
    completes = data.batch['complete'].tolist()  # Success flags from environments
    batch_size = data.batch['responses'].size(0)  # 512
    
    # Convert boolean success to float rewards
    score = [float(item) for item in completes]  # [0.0, 1.0, 0.0, ...]
    
    # Format correctness (always 1.0 for VLA)
    format = [1.0] * batch_size
    
    # Store in batch
    data.batch['acc'] = torch.tensor(score, dtype=torch.float32)
    data.batch['format_correctness'] = torch.tensor(format, dtype=torch.float32)
    
    # Compute metrics
    reward_metrics = {'all': data.batch['acc'].mean().item()}  # Average success rate
    format_metrics = {'all': 1.0}
    
    return score, reward_metrics, format_metrics, reward_format_metrics
```

### 2.2 Filtering (from `ray_trainer.py:573-578`)

```python
if config.data.filter_accuracy:
    # Filter rollouts by average success rate per task
    # Keeps tasks with success rate in [accuracy_lower_bound, accuracy_upper_bound]
    # Default: [0.1, 0.9]
    filtered_batch = self.filter(scores_tensor, roll_batch, n_samples=8)
```

### Dynamic Sampling (Paper Section 3.3)

**Key Insight from Paper**: This implements "Dynamic Sampling" from the paper, which ensures non-zero advantage estimates and stable gradients by filtering out groups where all trajectories either succeed or fail.

**Mathematical Formulation** (Equation 10 from paper):
```
0 < |{traj_i(a_i, s_i) | is_successful(traj_i(a_i, s_i))}| < G
```
Where G is the group size (n_samples = 8).

**Implementation** (from `ray_trainer.py:755-816`):

```python
def filter(reward_tensor, batch, n_samples=8):
    # Reshape to (num_tasks, n_samples)
    reward_matrix = reward_tensor.sum(-1).reshape(-1, n_samples)  # (64, 8)
    
    # Compute average success rate per task group
    acc_tensor = torch.mean(reward_matrix, dim=-1)  # (64,)
    # Example: [0.0, 0.25, 0.5, 0.75, 1.0, ...]
    
    # Dynamic Sampling: Filter by accuracy bounds
    # Keeps only groups with MIXED outcomes (not all success or all failure)
    acc_mask = (acc_tensor >= 0.1) & (acc_tensor <= 0.9)
    # 0.1 threshold: excludes all-failure groups (0.0)
    # 0.9 threshold: excludes all-success groups (1.0)
    
    # Expand mask to cover all samples in kept groups
    final_mask = acc_mask.repeat_interleave(n_samples)  # (64*8,)
    
    # Apply mask
    filtered_batch = batch.slice(final_mask)
    
    return filtered_batch
```

**Dynamic Sampling Benefits** (from paper):
1. **Non-zero advantages**: Groups with all success/failure have zero variance, leading to zero advantages
2. **Stable gradients**: Mixed outcomes provide meaningful learning signal
3. **Curriculum learning**: Naturally focuses on tasks of appropriate difficulty
4. **Proven effective in LLM RL**: Based on recent LLM RL research (Yu et al., 2025; Cui et al., 2025a)

**Filtering Effect**:
- Original batch: 64 tasks × 8 samples = 512 rollouts
- After Dynamic Sampling: ~30-50 tasks × 8 samples = ~240-400 rollouts (varies)
- Excluded: ~20% all-failure groups + ~10% all-success groups
- Remaining: ~70% mixed-outcome groups for effective training

### 2.3 Outcome Reward Modeling (Paper Section 3.2)

**Key Insight from Paper**: SimpleVLA-RL uses **outcome-only rewards** (success/failure) without hand-crafted process rewards. This is inspired by LLM RL success (DeepSeek-R1) and addresses the scalability challenges of designing dense rewards for every task.

### 2.3.1 Reward Shaping (from `ray_trainer.py:631-647`)

```python
def reward_fn(batch):
    # Initialize reward tensors
    reward_tensor = torch.zeros_like(batch['responses'], dtype=torch.float32)  # (N, num_steps, 350)
    verifier_reward = torch.zeros_like(batch['responses'], dtype=torch.float32)
    
    # Reshape to (N, num_steps * 350)
    reward_tensor = reward_tensor.reshape((reward_tensor.shape[0], -1))
    verifier_reward = verifier_reward.reshape((verifier_reward.shape[0], -1))
    
    # Compute valid response length
    valid_response_length = batch['finish_step'] * action_token_len  # finish_step × 14
    
    # Place reward at the end of trajectory (sparse reward)
    verifier_score = batch['acc'].cpu().numpy().tolist()  # [0.0, 1.0, 0.0, ...]
    for i in range(verifier_reward.shape[0]):
        verifier_reward[i, valid_response_length[i] - 1] += verifier_score[i]
    
    reward_tensor_dict = {'gt_scores': verifier_reward}
    
    # Apply reward coefficient
    if config.verifier.reward_coef != 0:
        reward_tensor += config.verifier.reward_coef * reward_tensor_dict['gt_scores']
    
    reward_tensor_dict['all'] = reward_tensor
    
    return reward_tensor_dict, reward_metrics
```

**Reward Structure**:
```
Trajectory:  [a_0, a_1, a_2, ..., a_T]
Rewards:     [0.0, 0.0, 0.0, ..., r_T]  # Sparse reward at end
                                  ↑
                                  Success (1.0) or Failure (0.0)
```

---

## Phase 3: Advantage Estimation (GRPO)

**Algorithm**: Group Relative Policy Optimization (GRPO)

**Key Insight from Paper**: GRPO is specifically designed for outcome-based rewards in RL. Instead of traditional GAE which requires value functions and dense rewards, GRPO uses relative comparisons within groups of trajectories from the same task.

### 3.1 KL Penalty (Optional) (from `ray_trainer.py:642-647`)

```python
batch, kl_metrics = apply_kl_penalty(
    batch, 
    kl_ctrl=self.kl_ctrl,
    kl_penalty='kl',
    action_token_len=14,
    action_chunks_len=25
)
```

### KL Penalty Logic (from `ray_trainer.py:85-120`)

```python
def apply_kl_penalty(data, kl_ctrl, kl_penalty='kl', action_token_len=14, action_chunks_len=25):
    responses = data.batch['responses']  # (N, num_steps, 350)
    
    # Compute trajectory length
    traj_length = responses.size(1) * action_chunks_len  # num_steps × 25
    token_level_scores = data.batch['token_level_scores']  # Raw rewards
    
    # Compute response mask (valid tokens)
    finish_step = data.batch['finish_step'] * action_token_len  # finish_step × 14
    steps = torch.arange(traj_length * action_token_len)
    steps_expanded = steps.unsqueeze(0).expand(batch_size, -1)
    response_mask = steps_expanded < finish_step.unsqueeze(1)
    
    # Compute KL divergence if reference policy is used
    if 'ref_log_prob' in data.batch.keys():
        # KL = log π(a|s) - log π_ref(a|s)
        kld = old_log_probs - ref_log_prob  # (N, response_length)
        kld = kld * response_mask
        beta = kl_ctrl.value  # KL coefficient (adaptive or fixed)
    else:
        beta = 0
        kld = torch.zeros_like(response_mask, dtype=torch.float32)
    
    # Apply KL penalty to rewards
    token_level_rewards = token_level_scores - beta * kld
    
    # Update KL controller
    current_kl = masked_mean(kld, mask=response_mask, axis=-1).mean().item()
    kl_ctrl.update(current_kl=current_kl, n_steps=batch_size)
    
    data.batch['token_level_rewards'] = token_level_rewards
    
    metrics = {'critic/kl': current_kl, 'critic/kl_coeff': beta}
    return data, metrics
```

### 3.2 Advantage Computation (from `ray_trainer.py:649-655`)

```python
batch = compute_advantage(
    batch,
    gamma=1.0,                         # config.algorithm.gamma (not shown in script)
    lam=0.95,                          # config.algorithm.lam (not shown in script)
    adv_estimator='grpo',              # Group Relative Policy Optimization
    config=config
)
```

### GRPO Advantage Estimation (from `ray_trainer.py:160-173`)

```python
def compute_advantage(data, gamma, lam, adv_estimator='grpo', config):
    responses = data.batch['responses']
    response_length = responses.size(1) * responses.size(2)  # num_steps × 350
    
    # Compute response mask
    finish_step = data.batch['finish_step'] * action_token_len
    steps = torch.arange(response_length)
    steps_expanded = steps.unsqueeze(0).expand(batch_size, -1)
    response_mask = steps_expanded < finish_step.unsqueeze(1)
    
    token_level_rewards = data.batch['token_level_rewards']
    index = data.non_tensor_batch['uid']  # Unique ID per task
    
    # GRPO: Group samples by task, use mean as baseline
    advantages, returns = core_algos.compute_grpo_outcome_advantage(
        token_level_rewards=token_level_rewards,
        eos_mask=response_mask,
        index=index  # Groups samples from same task
    )
    
    data.batch['advantages'] = advantages
    data.batch['returns'] = returns
    
    return data
```

### GRPO Algorithm (Paper Section 2.3 & `verl/trainer/ppo/core_algos.py`)

**Paper Definition**: GRPO is an outcome-based advantage estimation method that groups trajectories from the same prompt/task and uses the group mean as a baseline.

**Why GRPO for VLA?**
1. **No value function needed**: Unlike GAE, doesn't require training a separate critic
2. **Works with sparse rewards**: Designed for outcome-only rewards (success/failure)
3. **Relative learning**: Encourages better actions relative to other attempts at the same task
4. **Variance reduction**: Group mean provides better baseline than zero

```python
def compute_grpo_outcome_advantage(token_level_rewards, eos_mask, index):
    """
    Group Relative Policy Optimization (GRPO)
    
    Paper Formula (Section 2.3):
    A_i = R_i - (1/N) Σ_{j=1}^N R_j
    
    Where:
    - R_i: Total return for trajectory i
    - N: Number of samples per task group (n_samples = 8)
    - A_i: Advantage (how much better than group average)
    
    Process:
    1. Compute total return for each sample: R_i = Σ rewards
    2. Group samples by task (using unique ID)
    3. Compute group baseline: b = mean(R_1, ..., R_N)
    4. Compute advantages: A_i = R_i - b
    
    This encourages relative improvement within each task group.
    """
    batch_size = token_level_rewards.size(0)
    
    # Compute total returns (sum of rewards over trajectory)
    returns = (token_level_rewards * eos_mask).sum(-1)  # (batch_size,)
    
    # Group by task index (uid)
    unique_indices = torch.unique(index)
    advantages = torch.zeros_like(returns)
    
    for idx in unique_indices:
        mask = (index == idx)  # All 8 samples from same task
        group_returns = returns[mask]  # N=8 samples
        
        # Compute group baseline (mean return across 8 samples)
        baseline = group_returns.mean()
        
        # Compute relative advantages (how much better than average)
        group_advantages = group_returns - baseline
        advantages[mask] = group_advantages
    
    # Broadcast advantages to all timesteps
    advantages_broadcast = advantages.unsqueeze(-1).expand_as(token_level_rewards)
    advantages_broadcast = advantages_broadcast * eos_mask
    
    returns_broadcast = returns.unsqueeze(-1).expand_as(token_level_rewards)
    returns_broadcast = returns_broadcast * eos_mask
    
    return advantages_broadcast, returns_broadcast
```

**GRPO Example**:
```
Task 1 (8 samples):
- Returns: [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0]
- Baseline: mean = 0.5
- Advantages: [-0.5, 0.5, -0.5, 0.5, -0.5, 0.5, 0.5, -0.5]

Task 2 (8 samples):
- Returns: [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0]
- Baseline: mean = 0.25
- Advantages: [-0.25, -0.25, -0.25, -0.25, 0.75, 0.75, -0.25, -0.25]
```

---

## Phase 4: Actor Update (PPO with Clip Higher)

**Algorithm**: Proximal Policy Optimization (PPO) with modified clipping range

**Key Insight from Paper** (Section 3.3 - "Clipping Higher"): 
- Standard PPO clips ratio to `[1-ε, 1+ε]` typically `[0.8, 1.2]`
- SimpleVLA-RL increases upper bound to 1.28: `[0.8, 1.28]`
- **Rationale**: Higher upper bound allows more exploration by not restricting probability increase of low-probability actions
- **Inspired by**: DAPO (Yu et al., 2025) for LLM RL
- **Result**: Shown in Figure 3(b) - ~10% improvement over baseline by step 300

### 4.1 Update Trigger (from `ray_trainer.py:660-671`)

```python
if global_steps >= critic_warmup:  # Default: critic_warmup = 0
    # Update actor using PPO
    batch.meta_info['is_filtered'] = True
    batch.meta_info['train_mode'] = False
    
    actor_output = actor_rollout_wg.update_actor(batch)
    
    # Compute entropy for exploration
    entropy_output = actor_rollout_wg.compute_entropy(data=batch)
```

### 4.2 PPO Update (in ActorRolloutRefWorker)

```python
def update_actor(self, batch):
    """
    Proximal Policy Optimization (PPO) update
    
    Batch contains:
    - responses: (N, num_steps, 350) action tokens
    - old_log_probs: log π_old(a|s)
    - advantages: A(s, a)
    - returns: R(s, a)
    - attention_mask: valid token mask
    """
    
    # ========== PPO Configuration ==========
    ppo_mini_batch_size = 128   # Mini-batch size for PPO updates
    ppo_micro_batch_size = 8    # Micro-batch size (= num_gpus)
    clip_ratio_low = 0.2        # PPO clip lower bound (1 - 0.2 = 0.8)
    clip_ratio_high = 0.28      # PPO clip upper bound (1 + 0.28 = 1.28) ← CLIP HIGHER!
    num_ppo_epochs = 1          # Number of PPO epochs (default: 1)
    
    # Note: clip_ratio_high = 0.28 means clipping at 1.28 (not 1.2)
    # This is the "Clip Higher" enhancement from the paper
    
    # ========== Prepare Data ==========
    batch_size = len(batch)  # After filtering: ~240-400 rollouts
    
    # Shuffle data for mini-batch SGD
    indices = torch.randperm(batch_size)
    shuffled_batch = batch.slice(indices)
    
    # ========== Mini-Batch Loop ==========
    num_mini_batches = batch_size // ppo_mini_batch_size  # ~2-3 mini-batches
    
    metrics = defaultdict(list)
    
    for mini_batch_idx in range(num_mini_batches):
        start = mini_batch_idx * ppo_mini_batch_size
        end = start + ppo_mini_batch_size
        mini_batch = shuffled_batch.slice(range(start, end))
        
        # ========== Micro-Batch Loop (for memory efficiency) ==========
        num_micro_batches = ppo_mini_batch_size // ppo_micro_batch_size  # 128 // 8 = 16
        
        accumulated_loss = 0.0
        
        for micro_batch_idx in range(num_micro_batches):
            micro_start = micro_batch_idx * ppo_micro_batch_size
            micro_end = micro_start + ppo_micro_batch_size
            micro_batch = mini_batch.slice(range(micro_start, micro_end))
            
            # --- Forward Pass ---
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                output = model(
                    input_ids=micro_batch['input_ids'],
                    pixel_values=micro_batch['pixel_values'],
                    proprio=micro_batch['proprio'],
                    attention_mask=micro_batch['attention_mask'],
                    labels=micro_batch['responses'],  # Teacher forcing
                )
                
                logits = output.logits  # (micro_batch_size, seq_len, vocab_size)
                
                # Compute log probabilities
                log_probs = F.log_softmax(logits, dim=-1)
                
                # Gather log probs for actual actions
                action_log_probs = torch.gather(
                    log_probs, 
                    dim=-1, 
                    index=micro_batch['responses'].unsqueeze(-1)
                ).squeeze(-1)  # (micro_batch_size, seq_len)
                
                # Get old log probs from rollout
                old_log_probs = micro_batch['old_log_probs']
                
                # Compute probability ratio: π(a|s) / π_old(a|s)
                ratio = torch.exp(action_log_probs - old_log_probs)
                
                # Get advantages
                advantages = micro_batch['advantages']
                
                # Normalize advantages (per micro-batch)
                advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
                
                # --- PPO Clipped Objective with "Clip Higher" ---
                # Standard PPO: L_CLIP = min(ratio * A, clip(ratio, 0.8, 1.2) * A)
                # SimpleVLA-RL: L_CLIP = min(ratio * A, clip(ratio, 0.8, 1.28) * A)
                # The 1.28 upper bound allows more exploration!
                clipped_ratio = torch.clamp(ratio, 1 - clip_ratio_low, 1 + clip_ratio_high)
                # = torch.clamp(ratio, 0.8, 1.28)
                
                loss_unclipped = ratio * advantages
                loss_clipped = clipped_ratio * advantages
                
                policy_loss = -torch.min(loss_unclipped, loss_clipped)
                
                # Apply mask to only valid tokens
                response_mask = micro_batch['attention_mask'][:, -action_log_probs.size(1):]
                policy_loss = (policy_loss * response_mask).sum() / response_mask.sum()
                
                # Value loss (if using critic)
                # value_loss = F.mse_loss(values, returns)
                
                # Total loss
                loss = policy_loss  # + value_coef * value_loss
                
                # Normalize by num_micro_batches for gradient accumulation
                loss = loss / num_micro_batches
            
            # --- Backward Pass ---
            loss.backward()
            
            accumulated_loss += loss.item()
            
            # Store metrics
            metrics['actor/policy_loss'].append(policy_loss.item())
            metrics['actor/ratio_mean'].append(ratio.mean().item())
            metrics['actor/ratio_max'].append(ratio.max().item())
            metrics['actor/ratio_min'].append(ratio.min().item())
            metrics['actor/clip_fraction'].append(
                ((ratio < 1 - clip_ratio_low) | (ratio > 1 + clip_ratio_high)).float().mean().item()
            )
        
        # --- Gradient Clipping and Optimizer Step (after accumulating micro-batches) ---
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        optimizer.zero_grad()
    
    # Average metrics
    for key in metrics:
        metrics[key] = np.mean(metrics[key])
    
    return DataProto(meta_info={'metrics': metrics})
```

### PPO Update Summary

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Batch Size** | ~240-400 | After accuracy filtering |
| **Mini-Batch Size** | 128 | For PPO updates |
| **Micro-Batch Size** | 8 | For memory efficiency |
| **Num Mini-Batches** | ~2-3 | 240-400 // 128 |
| **Num Micro-Batches** | 16 | 128 // 8 |
| **Clip Ratio** | [0.2, 0.28] | PPO clipping range |
| **Learning Rate** | 5e-6 | Adam optimizer |
| **Gradient Clipping** | 1.0 | Max norm |

**Timing**:
- Forward + Backward per micro-batch: ~500ms
- Total per mini-batch: 16 × 500ms = 8s
- Total per step: 2-3 × 8s = ~16-24s

### 4.3 Entropy Computation (from `ray_trainer.py:666`)

```python
entropy_output = actor_rollout_wg.compute_entropy(data=batch)
```

**Purpose**: Measure policy entropy for exploration monitoring
```python
def compute_entropy(data):
    # Forward pass to get logits
    logits = model(...)
    
    # Compute entropy: H = -Σ p(a) log p(a)
    probs = F.softmax(logits, dim=-1)
    log_probs = F.log_softmax(logits, dim=-1)
    entropy = -(probs * log_probs).sum(-1)  # (batch_size, seq_len)
    
    # Average over valid tokens
    entropy_mean = (entropy * response_mask).sum() / response_mask.sum()
    
    return DataProto(meta_info={'metrics': {'actor/entropy': entropy_mean.item()}})
```

---

## Phase 5: Validation

### 5.1 Validation Trigger (from `ray_trainer.py:673-679`)

```python
if (global_steps + 1) % test_freq == 0:  # Every 4 steps
    val_metrics = self._validate(global_steps=global_steps+1)
    val_metrics = {f'val/{key}': val for key, val in val_metrics.items()}
    logger.log(data=val_metrics, step=global_steps)
```

### 5.2 Validation Process (from `ray_trainer.py:336-391`)

```python
def _validate(self, global_steps=0):
    reward_tensor_lst = []
    data_source_lst = []
    
    # Loop over validation dataloader
    for test_data in val_dataloader:  # 256 / 256 = 1 batch
        test_batch = DataProto.from_single_dict(test_data)
        
        # Set validation config
        test_batch.meta_info = {
            'eos_token_id': tokenizer.eos_token_id,
            'pad_token_id': tokenizer.pad_token_id,
            'recompute_log_prob': False,
            'do_sample': False,           # Greedy sampling for validation
            'validate': True,              # Validation mode flag
            'global_steps': global_steps   # For video naming
        }
        
        # Generate rollouts (no n_samples, single rollout per task)
        test_output_gen_batch = actor_rollout_wg.generate_sequences(test_batch)
        # Uses val_micro_batch_size = 8 (larger than training micro_batch_size = 1)
        
        test_batch = test_batch.union(test_output_gen_batch)
        
        # Evaluate using reward function
        verifier_score, reward_metrics, format_metrics, _ = val_reward_fn.verify(test_batch)
        reward_tensor = torch.tensor(verifier_score, dtype=torch.float32).unsqueeze(-1)
        
        # Log metrics
        for k, v in reward_metrics.items():
            metric_dict['test_reward/' + k] = v
        
        reward_tensor_lst.append(reward_tensor)
        data_source_lst.append(test_batch.non_tensor_batch['data_source'])
    
    # Aggregate results
    reward_tensor = torch.cat(reward_tensor_lst, dim=0).sum(-1).cpu()  # (256,)
    data_sources = np.concatenate(data_source_lst, axis=0)
    
    # Compute metrics by data source
    data_source_reward = {}
    for i in range(reward_tensor.shape[0]):
        data_source = data_sources[i]
        if data_source not in data_source_reward:
            data_source_reward[data_source] = []
        data_source_reward[data_source].append(reward_tensor[i].item())
    
    metric_dict = {}
    for data_source, rewards in data_source_reward.items():
        metric_dict[f'test_score/{data_source}'] = np.mean(rewards)
    
    metric_dict[f'test_score/all'] = reward_tensor.mean().item()
    
    return metric_dict
```

### Validation Dataset (from `rob_dataset.py:136-209`)

```python
# For validation
val_dataset = Robotwin_Dataset(
    task_suite_name='robotwin2_beat_block_hammer',
    num_trials_per_task=128,  # Overridden for validation
    train_val='valid'
)

# Loads two types of seeds:
# 1. IID seeds: From training distribution (128 seeds)
# 2. OOD seeds: From eval distribution (128 seeds)
# Total: 256 task instances

# Data source labels:
# - 'robotwin2_beat_block_hammer_train_iid'
# - 'robotwin2_beat_block_hammer_eval_ood'
```

### Validation Metrics

```python
{
    'val/test_score/robotwin2_beat_block_hammer_train_iid': 0.65,  # IID success rate
    'val/test_score/robotwin2_beat_block_hammer_eval_ood': 0.42,   # OOD success rate
    'val/test_score/all': 0.535,                                   # Overall success rate
}
```

**Validation Timing**:
- 256 rollouts with val_micro_batch_size=8
- Distributed across 8 GPUs: 256 / 8 = 32 rollouts per GPU
- Per rollout: ~20-30s
- Total: ~30-40s (parallel execution)

---

## Data Flow and Synchronization

### Overall Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                      Training Step i                              │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ↓
   ┌──────────────────────────────────────────────────────────┐
   │  1. Dataset Sampling                                      │
   │     - Sample 64 task instances from dataset              │
   │     - Each with unique feasible seed                     │
   │     - Expand to 64 × 8 = 512 copies for n_samples       │
   └──────────────────────────────────────────────────────────┘
                              │
                              ↓
   ┌──────────────────────────────────────────────────────────┐
   │  2. Rollout (Distributed across 8 GPUs via Ray)          │
   │     - Each GPU processes ~64 rollouts (8 tasks × 8)      │
   │     - Initialize environments                            │
   │     - VLA inference + action execution loop              │
   │     - Collect trajectory data                            │
   │     - Output: (512, num_steps, ...)                      │
   └──────────────────────────────────────────────────────────┘
                              │
                              ↓
   ┌──────────────────────────────────────────────────────────┐
   │  3. Verification & Filtering (Main Process)              │
   │     - Compute success flags                              │
   │     - Filter by accuracy: keep 10%-90% success rate      │
   │     - Output: (~300, num_steps, ...)                     │
   └──────────────────────────────────────────────────────────┘
                              │
                              ↓
   ┌──────────────────────────────────────────────────────────┐
   │  4. Reference Policy (Optional, Distributed)             │
   │     - Compute log π_ref(a|s) for KL penalty              │
   │     - Only if kl_coef > 0                                │
   └──────────────────────────────────────────────────────────┘
                              │
                              ↓
   ┌──────────────────────────────────────────────────────────┐
   │  5. Reward Computation (Main Process)                    │
   │     - Apply reward shaping (sparse reward at end)        │
   │     - Apply KL penalty if using ref policy               │
   │     - Output: token_level_rewards                        │
   └──────────────────────────────────────────────────────────┘
                              │
                              ↓
   ┌──────────────────────────────────────────────────────────┐
   │  6. Advantage Estimation (Main Process)                  │
   │     - GRPO: Group samples by task                        │
   │     - Compute advantages = returns - group_mean          │
   │     - Output: advantages, returns                        │
   └──────────────────────────────────────────────────────────┘
                              │
                              ↓
   ┌──────────────────────────────────────────────────────────┐
   │  7. Actor Update (Distributed across 8 GPUs)             │
   │     - PPO mini-batch loop (2-3 mini-batches)            │
   │     - Micro-batch loop (16 micro-batches per mini-batch)│
   │     - Forward + backward + gradient accumulation         │
   │     - Gradient clipping + optimizer step                 │
   │     - Output: actor_metrics                              │
   └──────────────────────────────────────────────────────────┘
                              │
                              ↓
   ┌──────────────────────────────────────────────────────────┐
   │  8. Entropy Computation (Distributed)                    │
   │     - Measure policy entropy for exploration monitoring  │
   │     - Output: entropy_metrics                            │
   └──────────────────────────────────────────────────────────┘
                              │
                              ↓
   ┌──────────────────────────────────────────────────────────┐
   │  9. Validation (Every 4 steps, Distributed)              │
   │     - 256 rollouts (greedy sampling)                     │
   │     - Compute success rates (IID and OOD)                │
   │     - Output: val_metrics                                │
   └──────────────────────────────────────────────────────────┘
                              │
                              ↓
   ┌──────────────────────────────────────────────────────────┐
   │  10. Checkpoint Saving (Every 20 steps)                  │
   │      - Save actor model weights                          │
   │      - Save critic model weights (if GAE)                │
   │      - Save optimizer state                              │
   └──────────────────────────────────────────────────────────┘
                              │
                              ↓
                      global_steps += 1
```

### Ray Distributed Execution

```python
# Worker allocation (8 GPUs)
actor_rollout_wg.world_size = 8   # 8 workers, 1 per GPU
actor_rollout_wg.local_size = 8   # All on same node

# When calling actor_rollout_wg.generate_sequences(batch)
# Ray automatically distributes workload:

batch_size = 512  # 64 tasks × 8 samples
world_size = 8
micro_batch_size = 1

# Each GPU processes:
local_batch_size = batch_size // world_size = 512 // 8 = 64 rollouts

# Ray scheduling:
# GPU 0: processes rollouts [0:64]
# GPU 1: processes rollouts [64:128]
# GPU 2: processes rollouts [128:192]
# ...
# GPU 7: processes rollouts [448:512]

# All GPUs run in parallel, synchronization at end
```

### FSDP Model Sharding

```bash
actor_rollout_ref.actor.fsdp_config.param_offload=False
actor_rollout_ref.actor.fsdp_config.grad_offload=True
actor_rollout_ref.actor.fsdp_config.optimizer_offload=True
```

**FSDP Strategy**:
- **Param Offload**: Disabled → Parameters stay on GPU
- **Grad Offload**: Enabled → Gradients offloaded to CPU after backward
- **Optimizer Offload**: Enabled → Optimizer states kept on CPU

**Model Sharding**:
```
OpenVLA-7B Model:
├── Vision Backbone (400M-700M params)  → Sharded across 8 GPUs
├── Projector (8M params)               → Sharded across 8 GPUs
├── LLM (7B params)                     → Sharded across 8 GPUs
└── Total: ~7.5B params                 → ~940MB per GPU (in bfloat16)
```

---

## Performance Analysis

### Training Step Timing Breakdown

**ORIGINAL ESTIMATE (WRONG!)**:

| Phase | Estimated Duration | GPU Util | Notes |
|-------|----------|----------|-------|
| **1. Rollout** | 30-40s | 15% | Bottleneck: CPU physics simulation |
| **2. Verification & Filtering** | 1-2s | 0% | CPU operations |
| **3. Reference Policy** | 2-3s | 80% | If kl_coef > 0 (disabled in config) |
| **4. Reward Computation** | <1s | 0% | CPU tensor operations |
| **5. Advantage Estimation** | <1s | 0% | CPU tensor operations |
| **6. Actor Update** | 16-24s | 90% | PPO mini-batch loop |
| **7. Entropy Computation** | 1-2s | 80% | Additional forward pass |
| **8. Logging** | <1s | 0% | Write metrics to WandB |
| **Total per step** | **50-70s** | **30-40%** | Average GPU utilization |

**ACTUAL REALITY (from user logs)**:

| Phase | Actual Duration | GPU Util | Notes |
|-------|----------|----------|-------|
| **1. Rollout** | 1070-1100s (~18 min) | 15-20% | Collects ~896 rollouts (to get 512 after filtering) |
| **2. Verification & Filtering** | 4-5s | 0% | Filters 896 → 512 rollouts |
| **3. Reference Policy** | 0s | 0% | Disabled (kl_coef=0) |
| **4. Reward Computation** | <1s | 0% | CPU tensor operations |
| **5. Advantage Estimation** | 0.14-0.20s | 0% | GRPO computation |
| **6. Actor Update (PPO)** | 140-145s (~2.4 min) | 90% | 4 mini-batches, dataloader_length=4 |
| **7. Entropy Computation** | <1s | 80% | Included in actor update |
| **8. Logging** | <1s | 0% | Write metrics to WandB |
| **Total per training step** | **1220-1300s (~20-22 min)** | **20%** | Average GPU utilization |

**Additional Operations**:
- **Validation** (every 4 training steps): +30-40s (256 rollouts)
- **Checkpoint Saving** (every 20 training steps): +10-20s

**Why Rollout is So Slow**:
- Each rollout takes ~1.2 seconds (includes env init, 8 VLA calls, 200 env steps, cleanup)
- Need to collect 896 rollouts to get 512 valid ones after filtering (75% efficiency)
- 896 × 1.2s = 1075 seconds ≈ 18 minutes

### Full Training Timeline

**PAPER EXPERIMENTS (300 steps, 20 epochs)**:
```
Total Training Duration:
= 300 training_steps × 1230 seconds/step
= 369,000 seconds
= 102.5 hours
≈ 4.3 days (with 8 GPUs running continuously)
```

**IF USING FULL CONFIG (1500 steps, 100 epochs)**:
```
Total Training Duration:
= 1500 training_steps × 1230 seconds/step
= 1,845,000 seconds
= 512.5 hours
≈ 21.4 days (with 8 GPUs running continuously)
```

### Rollout Statistics

**For Paper (300 steps)**:
| Metric | Value |
|--------|-------|
| **Total Rollouts** | 153,600 |
| **Successful Rollouts** | ~60,000-80,000 (depends on learning) |
| **Failed Rollouts** | ~70,000-90,000 |
| **Filtered Out** | ~40,000 (accuracy filtering) |
| **Used for Training** | ~110,000-120,000 |

**For Full Config (1500 steps)**:
| Metric | Value |
|--------|-------|
| **Total Rollouts** | 768,000 |
| **Successful Rollouts** | ~300,000-400,000 (depends on learning) |
| **Failed Rollouts** | ~400,000-500,000 |
| **Filtered Out** | ~200,000 (accuracy filtering) |
| **Used for Training** | ~500,000-600,000 |

### GPU Memory Usage

```
Per GPU (Rollout Phase):
├── Model Parameters (sharded): ~940MB
├── Activation Memory: ~1.5GB
├── Environment Buffers: ~500MB
├── KV Cache: ~2GB
└── Total: ~5GB / 40GB (12.5%)

Per GPU (Training Phase):
├── Model Parameters (sharded): ~940MB
├── Gradients: ~940MB
├── Activation Memory: ~3GB
├── Optimizer States (offloaded to CPU): 0MB
└── Total: ~5GB / 40GB (12.5%)

Peak Memory: ~6GB / 40GB (15%)
```

---

---

## Key Paper Insights

### What Makes SimpleVLA-RL Work?

Based on [SimpleVLA-RL: Scaling VLA Training via Reinforcement Learning](https://arxiv.org/pdf/2509.09674), the framework achieves state-of-the-art performance through **three key enhancements**:

#### 1. **Dynamic Sampling** (Section 3.3, Equation 10)

**Problem**: Groups with all success or all failure have zero advantage variance, leading to unstable gradients.

**Solution**: During rollout collection, exclude groups where all trajectories either succeed or fail:
```
0 < |{traj_i | is_successful(traj_i)}| < G
```

**Implementation**: `data.accuracy_lower_bound=0.1` and `data.accuracy_upper_bound=0.9`

**Result**: ~15% improvement over baseline (Figure 3a)

**Benefit**: 
- Non-zero advantages ensure meaningful learning signal
- Natural curriculum learning (focuses on appropriate difficulty)
- Proven effective in LLM RL (Yu et al., 2025; Cui et al., 2025a)

---

#### 2. **Clipping Higher** (Section 3.3)

**Problem**: Standard PPO's symmetric clipping `[0.8, 1.2]` restricts exploration by limiting probability increases.

**Solution**: Modify clipping range to `[0.8, 1.28]` (asymmetric):
```python
clip_ratio_high = 0.28  # Upper bound at 1.28 (not 1.2)
clip_ratio_low = 0.2    # Lower bound at 0.8
```

**Implementation**: `actor_rollout_ref.actor.clip_ratio_high=0.28`

**Result**: ~10% improvement over baseline (Figure 3b)

**Benefit**:
- Allows larger probability increases for low-probability actions
- Encourages exploration of new action patterns
- Inspired by DAPO (Yu et al., 2025) for LLM RL

---

#### 3. **Higher Rollout Temperature** (Section 3.3)

**Problem**: Low temperature (1.0) during rollout leads to deterministic, repetitive trajectories.

**Solution**: Increase sampling temperature from 1.0 to 1.6 during rollout phase:
```bash
actor_rollout_ref.rollout.temperature=1.6
```

**Implementation**: Used during `generate_action_verl()` in rollout, not during training

**Result**: ~15% improvement over baseline (Figure 3c)

**Benefit**:
- Generates diverse trajectories for better exploration
- Critical for discovering new successful strategies
- Widely used in recent LLM RL work (Liu et al., 2025c; An et al., 2025)

---

### Novel Phenomenon: "Pushcut"

**Discovery** (Section 6.1): During RL training, the policy discovered a previously unseen action pattern called "pushcut":
- SFT model only learns to grasp-and-lift objects
- After RL, model learns to **push** objects toward target while moving
- This "sliding" strategy is more efficient than pure lifting
- **Not seen in any training demonstrations!**

**Significance**: 
- Shows RL enables emergence of novel, optimal strategies
- Goes beyond imitation of human demonstrations
- Similar to AlphaGo discovering unconventional moves

---

### Performance Results (from Paper)

**LIBERO Benchmark** (Figure 3):
- Baseline SFT: ~60% success rate (Long)
- With all enhancements: ~90% success rate (Long) at 300 steps
- **+30 percentage points improvement**

**RoboTwin 2.0 Benchmark** (Table 1):
- Outperforms π₀ (previous SOTA) on multiple tasks
- Example: beat_block_hammer task success rate improvement

**Real-World Experiments** (Section 5.3):
- Successfully generalizes to real robot hardware
- Demonstrates sim-to-real transfer capability

---

### Why RL Works for VLA (Paper's Main Argument)

**Parallel to LLM RL Success**:
1. **DeepSeek-R1** showed RL dramatically improves step-by-step reasoning
2. **VLA = step-by-step action planning** (analogous to CoT reasoning)
3. RL enables learning from **outcome rewards only** (no hand-crafted process rewards)

**Key Advantages**:
1. **Addresses Data Scarcity**: No need for massive human demonstration data
2. **Improves Generalization**: RL naturally explores beyond training distribution
3. **Discovers Novel Patterns**: Like "pushcut" - goes beyond imitation
4. **Scalable**: Only requires environment simulator, not human operators

---

## Summary

### Key Characteristics of veRL Training

1. **GRPO + PPO Pipeline**: Separates advantage estimation (GRPO) from policy update (PPO)
   - GRPO works with sparse outcome rewards
   - PPO provides stable policy updates

2. **Three Critical Enhancements**: Dynamic Sampling + Clip Higher + Higher Temperature
   - Each provides ~10-15% improvement independently
   - Combined effect: ~30% improvement over baseline SFT

3. **Outcome-Only Rewards**: No hand-crafted process rewards
   - Success/failure at trajectory end
   - Inspired by LLM RL (DeepSeek-R1)
   - Scalable to new tasks

4. **Exploration-Focused**: Multiple mechanisms encourage exploration
   - Dynamic sampling focuses on learnable tasks
   - Clip higher allows larger policy updates
   - High temperature generates diverse rollouts

5. **300-Step Training**: Paper shows convergence at 300 training steps (~4.3 days)
   - Much faster than expected for robotic RL
   - Config has 1500 steps for extended experiments

### System Bottlenecks

1. **Rollout is 87.8% of time**: Physics simulation dominates
   - Each training step: ~18 minutes rollout, ~2.4 minutes training
   - Need ~896 rollouts to get 512 valid (after filtering)

2. **Dynamic Sampling reduces effective batch size**: ~30% overhead
   - Required for stable training
   - Worthwhile tradeoff for better learning

3. **Low GPU utilization during rollout**: ~15-20%
   - VLA inference only 300ms vs 1500ms physics
   - Fundamental limitation of CPU-based simulators

### Recommendations for Improvement

**Based on Paper**:
1. **Tune the three key hyperparameters**:
   - `data.accuracy_lower_bound` and `data.accuracy_upper_bound` (Dynamic Sampling)
   - `actor_rollout_ref.actor.clip_ratio_high` (Clip Higher)
   - `actor_rollout_ref.rollout.temperature` (Exploration)

2. **Task-Specific Tuning**:
   - Harder tasks may need wider accuracy bounds (0.05-0.95)
   - Easier tasks may need higher temperature (1.8-2.0)

**Based on Implementation Analysis**:
1. **Increase Rollout Throughput**:
   - Use GPU-accelerated simulator (Isaac Gym/Sim)
   - Reduce action chunk length (25 → 10-15)
   - Pipeline CPU/GPU work

2. **Optimize Training Efficiency**:
   - Increase n_samples for better GRPO baselines
   - Use multiple PPO epochs if overfitting is not a concern
   - Adjust filtering to keep more data if collection is expensive

3. **Monitor Key Metrics**:
   - `actor/pg_clipfrac`: Should be 2-5% (too high = policy changing too fast)
   - `critic/advantages/mean`: Should be near 0 (GRPO working correctly)
   - Dynamic sampling efficiency: Aim for 70-80% retention rate

