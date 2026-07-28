## English

## Scaling Vision-Language-Action Model Training via Reinforcement Learning

**Project URL**: [https://github.com/PRIME-RL/SimpleVLA-RL/](https://github.com/PRIME-RL/SimpleVLA-RL/)

**SimpleVLA-RL** Overview. SimpleVLA-RL is an efficient VLA reinforcement learning framework that improves long-horizon planning under data-scarce conditions, outperforms supervised fine-tuning (SFT) in both simulated and real-world tasks, reveals the novel "pushcut" action phenomenon, and enhances generalization across space, objects, and goals.

---

# 📑 Table of Contents

- [🎉 Latest News](#-latest-news)
- [📖 Project Overview](#-project-overview)
  - [Research Background](#research-background)
  - [Core Innovations](#core-innovations)
  - [Technical Architecture](#technical-architecture)
- [🔑 Three Key Techniques](#-three-key-techniques)
- [📃 Main Experimental Results](#-main-experimental-results)
- [✨ Quick Start](#-quick-start)
- [📊 Training Process Details](#-training-process-details)
- [🔍 Important Concept Explanations](#-important-concept-explanations)
- [⚠️ Notes](#-important-notes)
- [🌻 Acknowledgments](#-acknowledgments)
- [📨 Contact](#-contact)
- [📝 TODO](#-todo)
- [🎈 Citation](#-citation)

---

# 🎉 Latest News

- **[2025-10-01]** **SimpleVLA-RL** now supports the RoboTwin2.0 benchmark. Welcome to try it out!
- **[2025-09-12]** **SimpleVLA-RL** paper officially released! See details: [Paper Link](https://arxiv.org/abs/2509.09674)
- **[2025-05-27]** Released the complete **SimpleVLA-RL** code.

---

# 📖 Project Overview

## Research Background

Vision-Language-Action (VLA) models have emerged as a powerful paradigm in robotic manipulation, capable of unifying visual perception, language understanding, and action generation. However, the current development of VLA models faces two core challenges:

### Challenge 1: Data Scarcity and High Cost

Traditional VLA training heavily relies on large-scale human-operated robot trajectory data for supervised fine-tuning (SFT). The collection of this data suffers from the following issues:
- **High acquisition cost**: Requires carefully designed experimental scenarios, diverse manipulation objects, and skilled operators
- **Limited data scale**: The number of human demonstrations is far from sufficient for large-scale training needs
- **Insufficient diversity**: Human demonstrations tend to concentrate on specific manipulation patterns, lacking adequate exploration

### Challenge 2: Insufficient Generalization

VLA models trained on limited, scenario-specific data show significant performance degradation when facing:
- Unseen tasks and environments
- Long-horizon compositional tasks
- Real-world scenarios with distribution shifts

### Inspiration: Drawing from Large Language Model Reinforcement Learning

Recent breakthroughs in large reasoning models (e.g., DeepSeek-R1) demonstrate that reinforcement learning (RL), even when relying solely on outcome rewards, can significantly enhance a model's step-by-step reasoning ability. This naturally raises the question:

**Can RL similarly enhance the ability of VLA models to generate precise actions step by step?**

## Core Innovations

SimpleVLA-RL is an efficient reinforcement learning framework specifically designed for VLA models, featuring the following innovations:

### 1. **Using Only Outcome Rewards**
- No need to manually design process rewards for each sub-action
- Uses only binary task success/failure signals (0/1)
- Inspired by the successful experience of LLM reinforcement learning (DeepSeek-R1)
- Greatly enhances the scalability of the method

### 2. **Three Exploration Enhancement Strategies**
Based on the latest LLM RL research, three key technical enhancements are introduced:
- **Dynamic Sampling**: Filters out all-success/all-failure sample groups to ensure stable gradients
- **Clip Higher**: Asymmetric PPO clipping range to encourage bolder exploration
- **Higher Rollout Temperature**: Generates diverse trajectories to discover new strategies

The combination of these three can achieve approximately **30%** improvement over the baseline within 300 training steps!

### 3. **Discovery of Novel Action Patterns**
The "Pushcut" phenomenon emerges during training:
- The SFT model only learns the "grasp-lift-move" pattern
- After RL training, the model autonomously discovers the "push-slide" strategy
- **These action patterns never appeared in the training data!**
- Proves that RL can surpass human demonstrations to discover optimal strategies

## Technical Architecture

SimpleVLA-RL is built on the following technology stack:
- **Base Framework**: [veRL](https://github.com/volcengine/verl) - Volcengine LLM reinforcement learning framework
- **VLA Model**: [OpenVLA-OFT](https://github.com/moojink/openvla-oft) - 7B parameter open-source VLA model
- **Simulation Environments**:
  - [LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) - Long-horizon manipulation benchmark
  - [RoboTwin2.0](https://github.com/RoboTwin-Platform/RoboTwin) - Dual-arm manipulation benchmark
- **RL Algorithm**: Group Relative Policy Optimization (GRPO) + Proximal Policy Optimization (PPO)

---

# 🔑 Three Key Techniques

## Technique 1: Dynamic Sampling

### Problem
All-success or all-failure sample groups have zero advantage variance, leading to unstable gradients and inefficient training.

### Solution
Only retain sample groups with mixed results (partial success/partial failure) for training:

```python
# Mathematical expression (Paper Formula 10)
0 < |{trajectory_i | is_success(trajectory_i)}| < G

# Implementation code
data.accuracy_lower_bound=0.1  # Exclude all-failure groups (0%)
data.accuracy_upper_bound=0.9  # Exclude all-success groups (100%)
```

### Effect
- Ensures non-zero advantage, providing meaningful learning signals
- Naturally forms a curriculum learning process, focusing on tasks of appropriate difficulty
- Achieves approximately **~15%** improvement over baseline (Paper Figure 3a)

---

## Technique 2: Clip Higher

### Problem
Standard PPO's symmetric clipping `[0.8, 1.2]` limits the probability increase of low-probability actions, suppressing exploration.

### Solution
Adopt an asymmetric clipping range `[0.8, 1.28]`:

```bash
actor_rollout_ref.actor.clip_ratio_low=0.2   # Lower bound 1-0.2 = 0.8
actor_rollout_ref.actor.clip_ratio_high=0.28  # Upper bound 1+0.28 = 1.28
```

### Effect
- Allows low-probability actions greater room for probability increase
- Encourages exploration of new action patterns
- Achieves approximately **~10%** improvement over baseline (Paper Figure 3b)
- Inspired by DAPO (Yu et al., 2025)

---

## Technique 3: Higher Rollout Temperature

### Problem
Low temperature (1.0) leads to deterministic, repetitive trajectory generation, lacking exploration.

### Solution
Increase the sampling temperature during the rollout phase from 1.0 to 1.6:

```bash
actor_rollout_ref.rollout.temperature=1.6
```

**Note**: Used only when collecting data during rollout, not during training.

### Effect
- Generates diverse trajectories, enhancing exploration capability
- Crucial for discovering new successful strategies (e.g., the "pushcut" phenomenon)
- Achieves approximately **~15%** improvement over baseline (Paper Figure 3c)
- Widely used in the latest LLM RL research

---

# 📃 Main Experimental Results

## LIBERO Benchmark

We evaluated using OpenVLA-OFT on the LIBERO benchmark. SimpleVLA-RL boosts performance to **97.6 points** (out of 100), setting a new state-of-the-art.

### Key Results

| Setting | LIBERO-Long Success Rate | Improvement |
|---------|--------------------------|-------------|
| Baseline SFT | 60% | - |
| SFT + 300-step RL | 90% | +30% |
| **Final Performance** | **97.6%** | **+37.6%** |

### Cold Start Experiment (Extreme Data Scarcity Scenario)

**Experimental Setup**: Only **1 trajectory** per task used for SFT initialization

| Method | Success Rate | Improvement |
|--------|--------------|-------------|
| SFT only (1 trajectory) | 17.3% | - |
| SFT + SimpleVLA-RL | **91.7%** | **+74.4% (430.1%)** |

This demonstrates the powerful capability of RL in extreme data scarcity scenarios!

## RoboTwin 2.0 Benchmark

SimpleVLA-RL also achieves excellent results on the RoboTwin 2.0 dual-arm manipulation benchmark, surpassing the π₀ model on some tasks.

### RoboTwin 2.0 Introduction

RoboTwin 2.0 is a scalable dual-arm robot manipulation benchmark platform with the following features:
- **Strong Domain Randomization**: Multi-dimensional randomization of environments, objects, camera viewpoints, etc.
- **Dual-Arm Coordination**: Requires coordination between left and right arms to complete tasks
- **Realistic Physics**: Based on the SAPIEN physics engine, high-fidelity simulation
- **Diverse Tasks**: Covers various manipulation types including grasping, placing, tool use, etc.

---

# ✨ Quick Start

## Step 1: Environment Setup

### Installation Options

Choose the installation option based on the benchmark you want to use:

- **Option 1**: Run RL on the LIBERO benchmark
- **Option 2**: Run RL on the RoboTwin 2.0 benchmark

---

### Option 1: Run RL on the LIBERO Benchmark

#### Step 1.1: Install veRL

> **Note**: It is recommended to use veRL version 0.2 or 0.3. The latest version may have library conflicts.

Refer to the official [veRL Installation Guide](https://verl.readthedocs.io/en/v0.3.x/start/install.html):

```bash
# Create and activate conda environment
conda create -n simplevla python==3.10
conda activate simplevla

# Install PyTorch
pip3 install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124

# Clone veRL (recommended to place it in the same parent directory as simplevla-rl, not inside the simplevla-rl folder)
git clone -b v0.2.x https://github.com/volcengine/verl.git
cd verl
pip3 install -e .
cd ..
```

#### Step 1.2: Install EGL Libraries for Headless Rendering

**This step is required for both the LIBERO and RoboTwin 2.0 benchmarks.**

Install EGL libraries to enable headless rendering in Docker containers or remote servers without a display:

```bash
sudo apt-get update
sudo apt-get install -y libegl1 libegl-dev libegl-mesa0 libegl1-mesa-dev libgles2-mesa-dev
```

> **Note**: Without these libraries, you may encounter an `AttributeError: 'NoneType' object has no attribute 'eglQueryString'` error when initializing the SAPIEN/robot environment.

#### Step 1.3: Install LIBERO and OpenVLA-OFT

Refer to the official [OpenVLA-OFT Installation Guide](https://github.com/moojink/openvla-oft):

```bash
conda activate simplevla
pip3 install torch torchvision

# Clone OpenVLA-OFT (place it in the same parent directory as simplevla-rl, not inside the simplevla-rl folder)
git clone https://github.com/moojink/openvla-oft.git
cd openvla-oft
pip install -e .

# Install Flash Attention 2 for training
# If you encounter issues, first try `pip cache remove flash_attn`
pip install packaging ninja
ninja --version; echo $?  # Should return exit code "0"
pip3 install flash-attn --no-build-isolation

cd ..

# Install LIBERO
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git
pip install -e LIBERO
cd openvla-oft
pip install -r experiments/robot/libero/libero_requirements.txt
cd ..
```

---

### Option 2: Run RL on the RoboTwin 2.0 Benchmark

#### Step 2.1: Install veRL

Same as Step 1.1 in Option 1.

#### Step 2.2: Install EGL Libraries for Headless Rendering

Same as Step 1.2 in Option 1.

#### Step 2.3: Install RoboTwin 2.0

Refer to the official [RoboTwin 2.0 Installation Guide](https://robotwin-platform.github.io/doc/usage/robotwin-install.html#1-dependencies):

```bash
# Install system dependencies
sudo apt install libvulkan1 mesa-vulkan-drivers vulkan-tools

conda activate simplevla

# Clone and install RoboTwin
git clone https://github.com/RoboTwin-Platform/RoboTwin.git
cd RoboTwin
bash script/_install.sh

# Download RoboTwin assets
bash script/_download_assets.sh
cd ..
```

#### Step 2.4: Install OpenVLA-OFT

```bash
conda activate simplevla
pip3 install torch torchvision

# Clone OpenVLA-OFT (place it in the same directory as simplevla-rl, not inside the simplevla-rl folder)
git clone https://github.com/moojink/openvla-oft.git
cd openvla-oft
pip install -e .

# Install Flash Attention 2
pip install packaging ninja
ninja --version; echo $?  # Should return exit code "0"
pip3 install flash-attn --no-build-isolation
cd ..
```

#### Step 2.5: Configure RoboTwin for SimpleVLA-RL

Apply the necessary RoboTwin modifications:

```bash
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git
cd SimpleVLA-RL

# Apply RoboTwin modifications
bash copy_overwrite_robotwin2.sh <your_robotwin_path> <your_simplevlarl_path>
# Example: bash copy_overwrite_robotwin2.sh /mnt/petrelfs/RoboTwin /mnt/petrelfs/SimpleVLA-RL
```

---

### Troubleshooting

- If you encounter issues during the RoboTwin 2.0 installation, please refer to the [RoboTwin documentation](https://robotwin-platform.github.io/doc/) or check its GitHub Issues.
- If you encounter EGL-related errors, ensure all EGL libraries are correctly installed (see Steps 1.2/2.2).
- If you encounter Flash Attention installation issues, try clearing the pip cache: `pip cache remove flash_attn`
- It is recommended to clone all code repositories (veRL, OpenVLA-OFT, RoboTwin, LIBERO) into the same directory level as SimpleVLA-RL.

### Directory Structure

After installation, your directory structure should look like this:

```
your_workspace/
├── SimpleVLA-RL/
├── verl/
├── openvla-oft/
├── LIBERO/          (for Option 1)
└── RoboTwin/        (for Option 2)
```

### Verify Installation

After completing the installation, verify your setup:

```bash
# Activate environment
conda activate simplevla

# Verify PyTorch installation
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"

# Verify OpenVLA-OFT installation
python -c "import openvla; print('OpenVLA imported successfully')"

# For LIBERO (Option 1)
python -c "import libero; print('LIBERO imported successfully')"

# For RoboTwin (Option 2)
python -c "import robotwin; print('RoboTwin imported successfully')"
```

---

### (Optional) Support Additional Tasks in RoboTwin 2.0

#### Step A: Collect Feasible Seeds

RoboTwin 2.0 tasks may have infeasible seeds (e.g., objects out of the robot arm's reach). To optimize RL training, we pre-collect feasible seeds to avoid repeated validation during training epochs.

**Collection Process**:

1. Update `DATASET_NAME` in `pre_collect_robotwin2_seed.sh` to your target task name
2. Run the collection script:
   ```bash
   sh pre_collect_robotwin2_seed.sh
   ```
3. This will generate `robotwin2_train_seeds.json` in the SimpleVLA-RL directory
4. Add the JSON content to:
   ```
   SimpleVLA-RL/verl/utils/envs/robotwin2/seeds/robotwin2_train_seeds.json
   ```

#### Step B: Register New Tasks

1. Add the task name in `SimpleVLA-RL/verl/utils/dataset/rob_dataset.py`
2. Add the task name and corresponding maximum steps in `SimpleVLA-RL/verl/workers/rollout/rob_rollout.py`

#### Step C: Implement Task-Specific Functions

Add the `get_info()` function in the corresponding task file at `SimpleVLA-RL/verl/utils/envs/robotwin2/envs/task_name.py`.

Reference implementation example:
```
SimpleVLA-RL/modified_codes/robotwin2/envs/handover_block.py
```

## Step 2: Prepare the SFT Model

Reinforcement learning training requires an **SFT (Supervised Fine-Tuning)** VLA model as a starting point.

### Option 1: Download a Pre-trained SFT Model

Download from the [SimpleVLA-RL Collection](https://huggingface.co/collections/Haozhan72/simplevla-rl-6833311430cd9df52aeb1f86):

**LIBERO Benchmark Models**:
- `libero-10 traj1 SFT`: Trained with 1 trajectory per task (cold-start experiment)
- `libero-10 trajall SFT`: Trained with all trajectories per task
- `libero-goal traj1 SFT`: Goal generalization experiment
- `libero-object traj1 SFT`: Object generalization experiment
- `libero-spatial traj1 SFT`: Spatial generalization experiment

**RoboTwin 2.0 Benchmark Models**:
- `Robotwin2.0 tasks traj1000 SFT`: Trained with 1000 trajectories per task

### Option 2: Start from the Official OpenVLA Model

Download the pre-trained model from the [Official OpenVLA Repository](https://huggingface.co/openvla).

### Option 3: Fine-Tune Yourself

If you need to use other models or custom data, you will need to perform SFT fine-tuning yourself.

## Step 3: Configure Training Parameters

Before running the training script, you need to configure the following key parameters:

### 1. Configure WandB (Optional but Recommended)

Replace with your WandB API key in `SimpleVLA-RL/align.json`:

```json
{
  "WANDB_API_KEY": "your_wandb_api_key_here"
}
```

### 2. Modify the Training Script

Edit `examples/run_openvla_oft_rl_libero.sh` or `examples/run_openvla_oft_rl_twin2.sh`:

```bash
# Experiment configuration
export EXPERIMENT_NAME="libero_long_rl_exp1"     # Experiment name
export SFT_MODEL_PATH="/path/to/your/sft/model" # SFT model path
export CKPT_PATH="/path/to/save/checkpoints"    # Checkpoint save path

# Dataset configuration
export DATASET_NAME="libero-long"  # Options: libero-10, libero-long,
                                   #          robotwin2_beat_block_hammer, etc.

# Compute resource configuration
export NUM_GPUS=8      # Number of GPUs per node
export NUM_NODES=1     # Number of nodes

# WandB configuration
export ALIGN_PATH="SimpleVLA-RL/align.json"
```

### 3. Key Hyperparameter Explanation

```bash
# Data sampling configuration
data.train_batch_size=64                # Sample 64 task instances per training step
data.n_samples=8                        # Sample 8 trajectories per task (required by GRPO)

# Dynamic sampling (Key Technique 1)
data.filter_accuracy=True
data.accuracy_lower_bound=0.1          # Filter out task groups with success rate < 10%
data.accuracy_upper_bound=0.9          # Filter out task groups with success rate > 90%

# Inference configuration (Key Technique 3)
actor_rollout_ref.rollout.temperature=1.6  # Higher sampling temperature

# PPO configuration (Key Technique 2)
actor_rollout_ref.actor.clip_ratio_low=0.2    # Lower clipping bound
actor_rollout_ref.actor.clip_ratio_high=0.28  # Upper clipping bound (higher!)

# Optimizer configuration
actor_rollout_ref.actor.optim.lr=5e-6       # Learning rate
actor_rollout_ref.actor.ppo_mini_batch_size=128
actor_rollout_ref.actor.ppo_micro_batch_size=8

# Training progress configuration
trainer.total_epochs=20                 # Total epochs (paper uses 20 epochs = 300 steps)
trainer.save_freq=20                    # Save checkpoint every 20 steps
trainer.test_freq=4                     # Validate every 4 steps
```

## Step 4: Start RL Training

### LIBERO Benchmark

```bash
bash examples/run_openvla_oft_rl_libero.sh
```

### RoboTwin 2.0 Benchmark

```bash
bash examples/run_openvla_oft_rl_twin2.sh
```

### Expected Training Time

**Hardware Configuration**: 8×NVIDIA A800 GPU (80GB)

| Configuration | Training Steps | Estimated Time | Description |
|------|---------|---------|------|
| Paper Setting | 300 steps | ~4.3 days | 20 epochs, ~20 minutes per step |
| Configuration File | 1500 steps | ~21 days | 100 epochs (adjustable) |

**Time Breakdown (per training step)**:
- Data Collection (Rollout): ~18 minutes (87.8%)
- PPO Update: ~2.4 minutes (11.8%)
- Other Operations: ~0.2 minutes (0.4%)

## Step 5: Run Evaluation

To evaluate the trained model, enable validation mode in the script:

```bash
# Add to run_openvla_oft_rl_libero.sh
trainer.val_only=True
```

Then run the same script:

```bash
bash examples/run_openvla_oft_rl_libero.sh
```

---

# 📊 Detailed Training Process

## Training Loop Overview

Each training step consists of the following phases:

```
Training Step i
│
├─ 1. Data Sampling
│   └─ Sample 64 task instances from the dataset
│
├─ 2. Trajectory Inference (Rollout)
│   ├─ Generate 8 trajectories per task
│   ├─ VLA model inference
│   ├─ Environment interaction
│   └─ Collect trajectory data
│
├─ 3. Dynamic Sampling Filtering
│   └─ Filter out task groups that are all successful or all failed
│
├─ 4. Reward Calculation
│   └─ Apply outcome rewards (Success=1.0, Failure=0.0)
│
├─ 5. Advantage Estimation (GRPO)
│   ├─ Group by task
│   ├─ Calculate intra-group average return as baseline
│   └─ Advantage = Individual return - Group average
│
├─ 6. Policy Update (PPO)
│   ├─ Mini-batch loop
│   ├─ Calculate policy loss (with clipping)
│   ├─ Backpropagation
│   └─ Gradient Clipping and Optimizer Update
│
├─ 7. Validation (every 4 steps)
│   └─ Evaluate success rate on 256 tasks
│
└─ 8. Save Checkpoint (every 20 steps)
    └─ Save model weights and optimizer state
```

## Detailed Explanation of GRPO Advantage Estimation

**Group Relative Policy Optimization (GRPO)** is an advantage estimation method specifically designed for outcome-based rewards:

### Why GRPO?

Traditional Generalized Advantage Estimation (GAE) requires:
- Training an additional value network V(s)
- Dense intermediate reward signals
- A more complex training pipeline

Advantages of GRPO:
- ✅ No value network needed
- ✅ Only requires outcome rewards
- ✅ Learns through relative comparison within a group

### Algorithm Principle

For N trajectories of the same task:

```python
# 1. Compute the total return for each trajectory
R_i = Σ rewards  # i = 1, 2, ..., N (N=8)

# 2. Compute the group average as the baseline
baseline = (1/N) × Σ R_i

# 3. Compute the advantage
A_i = R_i - baseline
```

### Example

```
8 trajectories for Task 1:
Returns: [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0]
Baseline: 0.5
Advantages: [-0.5, 0.5, -0.5, 0.5, -0.5, 0.5, 0.5, -0.5]
             ↑    ↑    ↑    ↑     ↑    ↑    ↑    ↑
            Bad  Good  Bad  Good  Bad  Good  Good  Bad

Meaning: Successful trajectories receive positive advantages, failed ones receive negative advantages.
         The policy will learn to increase the probability of successful trajectories and decrease that of failed ones.
```

## Detailed Explanation of PPO Policy Update

### Standard PPO vs SimpleVLA-RL

```python
# Standard PPO objective function
ratio = π(a|s) / π_old(a|s)
clipped_ratio = clip(ratio, 0.8, 1.2)  # Symmetric clipping
loss = -min(ratio × A, clipped_ratio × A)

# SimpleVLA-RL: Clip Higher
clipped_ratio = clip(ratio, 0.8, 1.28)  # Asymmetric clipping!
loss = -min(ratio × A, clipped_ratio × A)
```

### Why is Clip Higher Effective?

**Scenario**: A low-probability action (p=0.1) succeeds during exploration

```
Standard PPO (clip_high=0.2):
- ratio = 0.15 / 0.1 = 1.5
- clipped_ratio = 1.2 (clipped!)
- Probability increases by at most 20%
- New probability ≤ 0.12

Clip Higher (clip_high=0.28):
- ratio = 1.5
- clipped_ratio = 1.5 (not clipped!)
- Probability can increase by 50%
- New probability ≤ 0.15

Result: Clip Higher allows larger policy updates, encouraging exploration.
```

---

# 🔍 Explanation of Important Concepts

## What is the "Pushcut" Phenomenon?

**Pushcut** is a novel manipulation pattern autonomously discovered by the policy during RL training, **never present in the training demonstrations**.

### Discovery Process

**SFT Model**: Learns only from human demonstrations
```
Standard Action Sequence:
1. Approach object
2. Grasp object
3. Lift object vertically (clear the table)
4. Move horizontally to target position
5. Place object down
6. Release gripper
```

**After RL Training**: A superior strategy is discovered
```
"Pushcut" Action Sequence:
1. Approach object
2. Grasp or contact object
3. Stay low (close to the table surface)
4. Push/drag object horizontally to target position
5. Task complete!
   ↑
   No lifting required, faster and more robust!
```

### Tasks Where Pushcut Was Observed

- ✅ **move_can_pot**: Push the can instead of lifting it
- ✅ **place_a2b_left/right**: Push object A instead of picking and placing
- ❌ **beat_block_hammer**: Not observed (requires tool grasping)

### Why is Pushcut Superior?

1. **Faster Execution**: Less vertical movement, more direct path
2. **More Robust**: Lower precision requirements
3. **Energy Efficient**: No need to fight gravity
4. **Collision Safety**: Staying close to the table reduces collision risk
5. **Maintains Contact**: Pushing naturally maintains object contact

### Significance

This discovery proves:
- ✅ RL can discover strategies not demonstrated by humans
- ✅ It surpasses the limitations of imitation learning
- ✅ It demonstrates a true understanding of the task objective (not just copying actions)
- ✅ Similar to AlphaGo discovering unconventional but optimal moves

## How Does Action Chunking Work?

### Comparison with ReAct Mode

**ReAct Mode** (Single Step):
```
Each Step:
  Observe → LLM Reason → Generate 1 Action → Execute → Next Step

Total (200 environment steps): 200 LLM calls
```

**VLA Action Chunking** (Multi-Step Planning):
```
Each Round:
  Observe → VLA Reason → Generate 25 Future Actions → Execute All → Next Round

Total (200 environment steps): 8 VLA calls (200÷25=8)
```

### Execution Timeline

```
Timeline:   0ms    300ms    1800ms   2100ms   3600ms
          |       |         |        |        |
GPU:      [VLA 1]  Idle     [VLA 2]  Idle     [VLA 3]
          ↓                         ↓
Actions:  Generate 25  Execute 25  Generate 25  Execute 25
          Actions      Actions     Actions      Actions

Env Steps:   0       0→24      25      25→49    50

Robot:    Stationary  Moving...  Moving...  Moving...  Moving...
```

### Why Use Action Chunking?

1. **Computational Efficiency**: 8 inferences vs 200 = **25x reduction**
2. **Natural Motion**: Produces smooth trajectories, avoids jitter
3. **Temporal Consistency**: Enforces coherence in action sequences
4. **Reduced Accumulated Error**: Fewer replanning steps reduce drift

### Does the Robot Pause in Real Deployment?

**Answer: No!** Real deployment uses **buffered execution**:

```
VLA Thread:    Continuously compute the next batch of 25 actions
               ↓
Action Buffer: [Actions 0-24] → [Actions 25-49] → [Actions 50-74]
               ↓                ↓                 ↓
Control Thread: Execute Actions  Execute Actions   Execute Actions
               (50Hz)           (50Hz)            (50Hz)

Result: The robot maintains continuous, smooth motion, no pauses!
```

**Key Condition**:
```
VLA Inference Time < Action Chunk Execution Time
300ms < (25 actions × 50ms/action) = 1250ms ✓

Safety Margin: 1250ms / 300ms = 4x ✓
```

---

# ⚠️ Important Notes

## Training Configuration

### Key Hyperparameters

The hyperparameters for the three key techniques **must be retained**:

```bash
# 1. Dynamic Sampling
data.accuracy_lower_bound=0.1
data.accuracy_upper_bound=0.9

# 2. Higher Clip Bound
actor_rollout_ref.actor.clip_ratio_high=0.28

# 3. Higher Inference Temperature
actor_rollout_ref.rollout.temperature=1.6
```

These three parameters together contribute approximately **30%** performance improvement!

---

# Experimental Results

[SimpleVLA RL rollout results (videos of the robot operating in a virtual environment)](https://01.me/files/ai-agent-book/SimpleVLA-RL-rollouts.zip)

[wandb experimental results](https://wandb.ai/bojieli-pine-ai/SimpleVLA-RL)

## Experiment Overview

According to the documentation, this experiment ran two key tasks on the RoboTwin 2.0 benchmark:
- **beat_block_hammer**: Tool use task (grasp hammer to hit block)
- **move_can_pot**: Spatial reasoning task (move can next to pot)

## Detailed Analysis

### 1. Actor Training Metrics Analysis

**PPO KL Divergence (ppo_kl)**:
- KL divergence for both tasks remained at low levels (~0.002-0.008)
- Indicates moderate policy update magnitude, not deviating excessively from the reference policy
- Meets the stability requirements of the PPO algorithm

**Policy Gradient Loss (pg_loss)**:
- `beat_block_hammer` shows higher loss values and larger fluctuations
- `move_can_pot` loss is relatively stable and lower
- Reflects the higher complexity of the tool use task

**Policy Gradient Clip Fraction (pg_clipfrac)**:
- Both tasks remain within the 0.01-0.03 range
- Moderate clipping indicates the **higher clip bound (1.28)** technique is effective
- Allows for bolder policy exploration while maintaining training stability

**Learning Rate and Gradient Norm**:
- Learning rate stable at 5e-6, consistent with configuration
- Gradient norm within a reasonable range, training process stable

### 2. Training Reward Analysis

**Verifier Reward (train_reward/verifier)**:
- `beat_block_hammer` (orange): Increased from ~0.3 to ~0.75, **150% growth**
- `move_can_pot` (blue): Increased from ~0.15 to ~0.6, **300% growth**
- Indicates both tasks benefit significantly from reinforcement learning

**Total Reward (train_reward/reward_all)**:
- Trend similar to verifier reward but with higher values
- This aligns with the GRPO algorithm design, where the group average serves as the baseline

### 3. Validation Score Analysis

**Training Validation Score (train_verify_score/all)**:
- `beat_block_hammer` ultimately reaches ~0.8 (80% success rate)
- `move_can_pot` ultimately reaches ~0.67 (67% success rate)
- Consistent with the 60-80% success rate expected by the paper

**Test Validation Score (val/test_score)**:
- **IID Test** (within training distribution):
  - `beat_block_hammer`: ~0.85 success rate
  - `move_can_pot`: ~0.63 success rate
- **OOD Test** (out of distribution):
  - `beat_block_hammer`: ~0.78 success rate
  - `move_can_pot`: ~0.58 success rate
- Small gap between IID/OOD performance indicates good generalization ability

### 4. Critic Network Analysis

**Reward Score Statistics**:
- **Minimum**: Both tasks start from 0, consistent with the binary reward setting
- **Mean**: Steadily increasing, reflecting improved average success rate
- **Maximum**: Both tasks reach the highest reward value

**Score Distribution**:
- Shows a healthy exploration-exploitation balance
- Consistent with the expected effect of the **dynamic sampling** technique

### 5. Exploration Strategy Analysis

**Entropy Loss (actor_after/entropy_loss_eval)**:
- `beat_block_hammer` shows higher entropy values (more exploration)
- `move_can_pot` entropy gradually decreases but remains at a reasonable level
- Indicates the **higher inference temperature (1.6)** successfully promotes exploration

## Performance Comparison

### Comparison with Paper Baseline

Results of this experiment on RoboTwin 2.0:
- `beat_block_hammer`: 80% success rate
- `move_can_pot`: 67% success rate
- Consistent with the performance range expected by the paper

### Cold Start Capability
The experiment demonstrates RL's powerful capability under data-scarce conditions:
- Starts from a limited SFT initialization
- Achieves significant performance improvement through outcome rewards
- Proves that RL can **surpass the limitations of human demonstrations**

---

# 🌻 Acknowledgements

This project is developed based on the following excellent open-source projects:

- **[veRL](https://github.com/volcengine/verl)**: Volcengine LLM Reinforcement Learning Framework
- **[OpenVLA-OFT](https://github.com/moojink/openvla-oft)**: Open-source Vision-Language-Action Model
- **[RoboTwin2.0](https://github.com/RoboTwin-Platform/RoboTwin)**: Dual-arm Robot Manipulation Benchmark
- **[LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO)**: Lifelong Robot Learning Benchmark
- **[PRIME](https://github.com/PRIME-RL/PRIME)**: Reinforcement Learning Research Framework

Thank you for the significant contributions of these projects! For more details and updates, please refer to the official documentation and code repositories of each project.

---

# 📨 Contact Information

For questions or suggestions, please feel free to contact:

- **Li Haozhan**: zhan72426@gmail.com
- **Ding Ning**: dingning@mail.tsinghua.edu.cn

Or submit an issue on [GitHub Issues](https://github.com/PRIME-RL/SimpleVLA-RL/issues).

---

# 📝 TODO

## Model Support

- ✅ Support for OpenVLA and OpenVLA-OFT
- ⏳ Support for Pi0 fast tokenizer
- ⏳ Support for more VLA architectures (RT-1, RT-2)

## Benchmarks

- ✅ Support for LIBERO benchmark
- ✅ Support for RoboTwin benchmark
- ⏳ Support for CALVIN benchmark
- ⏳ Support for real robot hardware

## Algorithm Improvements

- ⏳ Support for GPU-accelerated simulator (Isaac Gym)
- ⏳ Support for distributed training (multi-node)
- ⏳ Support for online curriculum learning

---

# 🎈 Citation

If you find SimpleVLA-RL helpful for your research, please cite our paper:

```bibtex
@article{li2025simplevla,
  title={SimpleVLA-RL: Scaling VLA Training via Reinforcement Learning},
  author={Li, Haozhan and Zuo, Yuxin and Yu, Jiale and Zhang, Yuhao and Yang, Zhaohui and Zhang, Kaiyan and Zhu, Xuekai and Zhang, Yuchen and Chen, Tianxing and Cui, Ganqu and others},
  journal={arXiv preprint arXiv:2509.09674},
  year={2025}
}
```

Also, please cite the RoboTwin 2.0 benchmark:

```bibtex
@article{robotwin2025,
  title={RoboTwin 2.0: A Scalable Data Generator and Benchmark with Strong Domain Randomization for Robust Bimanual Robotic Manipulation},
  author={Chen, Tianxing and Chen, Zanxin and Chen, Baijun and Cai, Zijian and Liu, Yibin and Li, Zixuan and Liang, Qiwei and Lin, Xianliang and Ge, Yiheng and Gu, Zhenyu and Deng, Weiliang and Guo, Yubin and Nian, Tian and Xie, Xuanbing and Chen, Qiangyu and Su, Kailun and Xu, Tianling and Liu, Guodong and Hu, Mengkang and Gao, Huan-ang and Wang, Kaixuan and Liang, Zhixuan and Qin, Yusen and Yang, Xiaokang and Luo, Ping and Mu, Yao},
  journal={arXiv preprint arXiv:2506.18088},
  year={2025}
}
```

---

## 中文

## 通过强化学习扩展视觉-语言-动作模型训练

**项目地址**: [https://github.com/PRIME-RL/SimpleVLA-RL/](https://github.com/PRIME-RL/SimpleVLA-RL/)

**SimpleVLA-RL** 概览。SimpleVLA-RL 是一个高效的 VLA 强化学习框架,能够在数据稀缺条件下改进长时序规划,在模拟和真实任务中的表现超越监督微调(SFT),揭示了"推切"新动作现象,并增强了空间、物体和目标的泛化能力。

---

# 📑 目录

- [🎉 最新动态](#-最新动态)
- [📖 项目概述](#-项目概述)
  - [研究背景](#研究背景)
  - [核心创新](#核心创新)
  - [技术架构](#技术架构)
- [🔑 三大关键技术](#-三大关键技术)
- [📃 主要实验结果](#-主要实验结果)
- [✨ 快速开始](#-快速开始)
- [📊 训练过程详解](#-训练过程详解)
- [🔍 重要概念解释](#-重要概念解释)
- [⚠️ 注意事项](#️-注意事项)
- [🌻 致谢](#-致谢)
- [📨 联系方式](#-联系方式)
- [📝 TODO](#-todo)
- [🎈 引用](#-引用)

---

# 🎉 最新动态

- **[2025-10-01]** **SimpleVLA-RL** 现已支持 RoboTwin2.0 基准测试。欢迎试用!
- **[2025-09-12]** **SimpleVLA-RL** 论文正式发布!查看详情:[论文链接](https://arxiv.org/abs/2509.09674)
- **[2025-05-27]** 发布 **SimpleVLA-RL** 完整代码。

---

# 📖 项目概述

## 研究背景

视觉-语言-动作(Vision-Language-Action, VLA)模型已成为机器人操作领域的有力范式,能够统一视觉感知、语言理解和动作生成。然而,当前 VLA 模型的发展面临两大核心挑战:

### 挑战一:数据稀缺与高成本

传统 VLA 训练严重依赖大规模人工操作的机器人轨迹数据进行监督微调(SFT)。这些数据的收集存在以下问题:
- **获取成本高昂**:需要精心设计的实验场景、多样化的操作物体和熟练的操作人员
- **数据规模受限**:人工演示的数量远不能满足大规模训练需求
- **多样性不足**:人类演示往往集中在特定的操作模式,缺乏充分的探索

### 挑战二:泛化能力不足

基于有限、特定场景数据训练的 VLA 模型在面对以下情况时性能显著下降:
- 未见过的任务和环境
- 长时序的组合任务
- 存在分布偏移的真实世界场景

### 启发:从大语言模型强化学习获得灵感

近期大型推理模型(如 DeepSeek-R1)的突破表明,强化学习(RL)即使仅依赖结果奖励,也能显著提升模型的逐步推理能力。这自然引出一个问题:

**RL 能否同样增强 VLA 模型逐步生成精确动作的能力?**

## 核心创新

SimpleVLA-RL 是一个专为 VLA 模型设计的高效强化学习框架,具有以下创新特点:

### 1. **仅使用结果奖励**
- 不需要为每个子行为手工设计过程奖励
- 仅使用任务成功/失败的二元信号(0/1)
- 受 LLM 强化学习(DeepSeek-R1)成功经验启发
- 极大提升了方法的可扩展性

### 2. **三大探索增强策略**
基于最新 LLM RL 研究,引入三个关键技术增强:
- **动态采样(Dynamic Sampling)**:过滤全成功/全失败样本组,确保稳定梯度
- **更高裁剪界(Clip Higher)**:不对称 PPO 裁剪范围,鼓励更大胆的探索
- **更高推理温度(Higher Rollout Temperature)**:生成多样化轨迹,发现新策略

三者结合可在 300 训练步内相比基线提升约 **30%**!

### 3. **发现新颖动作模式**
训练过程中出现"推切(Pushcut)"现象:
- SFT 模型仅学习"抓取-抬起-移动"模式
- RL 训练后自主发现"推动-滑动"策略
- **这些动作模式从未在训练数据中出现!**
- 证明 RL 能超越人类演示,发现最优策略

## 技术架构

SimpleVLA-RL 构建于以下技术栈:
- **基础框架**:[veRL](https://github.com/volcengine/verl) - 火山引擎 LLM 强化学习框架
- **VLA 模型**:[OpenVLA-OFT](https://github.com/moojink/openvla-oft) - 7B 参数的开源 VLA 模型
- **模拟环境**:
  - [LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) - 长时序操作基准测试
  - [RoboTwin2.0](https://github.com/RoboTwin-Platform/RoboTwin) - 双臂操作基准测试
- **RL 算法**:Group Relative Policy Optimization (GRPO) + Proximal Policy Optimization (PPO)

---

# 🔑 三大关键技术

## 技术一:动态采样(Dynamic Sampling)

### 问题
全成功或全失败的样本组优势方差为零,导致梯度不稳定,训练效率低下。

### 解决方案
仅保留混合结果(部分成功/部分失败)的样本组进行训练:

```python
# 数学表达式(论文公式 10)
0 < |{轨迹_i | 是否成功(轨迹_i)}| < G

# 实现代码
data.accuracy_lower_bound=0.1  # 排除全失败组(0%)
data.accuracy_upper_bound=0.9  # 排除全成功组(100%)
```

### 效果
- 确保非零优势,提供有意义的学习信号
- 自然形成课程学习,聚焦于适当难度的任务
- 相比基线提升 **~15%**(论文图 3a)

---

## 技术二:更高裁剪界(Clip Higher)

### 问题
标准 PPO 的对称裁剪 `[0.8, 1.2]` 限制了低概率动作的概率增长,抑制探索。

### 解决方案
采用不对称裁剪范围 `[0.8, 1.28]`:

```bash
actor_rollout_ref.actor.clip_ratio_low=0.2   # 下界 1-0.2 = 0.8
actor_rollout_ref.actor.clip_ratio_high=0.28  # 上界 1+0.28 = 1.28
```

### 效果
- 允许低概率动作有更大的概率提升空间
- 鼓励探索新的动作模式
- 相比基线提升 **~10%**(论文图 3b)
- 灵感来自 DAPO(Yu et al., 2025)

---

## 技术三:更高推理温度(Higher Rollout Temperature)

### 问题
低温度(1.0)会导致确定性、重复的轨迹生成,缺乏探索。

### 解决方案
将推理阶段的采样温度从 1.0 提升至 1.6:

```bash
actor_rollout_ref.rollout.temperature=1.6
```

**注意**:仅在推理收集数据时使用,训练时不使用。

### 效果
- 生成多样化轨迹,增强探索能力
- 对发现新的成功策略至关重要(如"推切"现象)
- 相比基线提升 **~15%**(论文图 3c)
- 广泛应用于最新 LLM RL 研究

---

# 📃 主要实验结果

## LIBERO 基准测试

我们在 LIBERO 基准测试上使用 OpenVLA-OFT 进行评估。SimpleVLA-RL 将性能提升至 **97.6 分**(满分 100),创下新的最先进水平。

### 关键结果

| 设置 | LIBERO-Long 成功率 | 提升幅度 |
|------|-------------------|---------|
| 基线 SFT | 60% | - |
| SFT + 300步RL | 90% | +30% |
| **最终性能** | **97.6%** | **+37.6%** |

### 冷启动实验(极端数据稀缺场景)

**实验设置**:每个任务仅使用 **1 条轨迹**进行 SFT 初始化

| 方法 | 成功率 | 提升 |
|------|--------|------|
| 仅 SFT(1条轨迹) | 17.3% | - |
| SFT + SimpleVLA-RL | **91.7%** | **+74.4% (430.1%)** |

这证明了 RL 在极端数据稀缺场景下的强大能力!

## RoboTwin 2.0 基准测试

SimpleVLA-RL 在 RoboTwin 2.0 双臂操作基准测试上也取得优异成绩,在部分任务上超越了 π₀ 模型。

### RoboTwin 2.0 简介

RoboTwin 2.0 是一个可扩展的双臂机器人操作基准测试平台,具有以下特点:
- **强域随机化**:环境、物体、相机视角等多维度随机化
- **双臂协同**:需要左右手臂协调配合完成任务
- **真实物理**:基于 SAPIEN 物理引擎,高保真度模拟
- **多样任务**:涵盖抓取、放置、工具使用等多种操作类型

---

# ✨ 快速开始

## 第一步:环境配置

### 安装选项

根据您要使用的基准测试,选择对应的安装选项:

- **选项 1**: 在 LIBERO 基准测试上运行 RL
- **选项 2**: 在 RoboTwin 2.0 基准测试上运行 RL

---

### 选项 1: 在 LIBERO 基准测试上运行 RL

#### 步骤 1.1: 安装 veRL

> **注意**: 建议使用 veRL 0.2 或 0.3 版本。最新版本可能存在库冲突。

参考官方 [veRL 安装指南](https://verl.readthedocs.io/en/v0.3.x/start/install.html):

```bash
# 创建并激活 conda 环境
conda create -n simplevla python==3.10
conda activate simplevla

# 安装 PyTorch
pip3 install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124

# 克隆 veRL (建议放在与 simplevla-rl 同级目录,而非 simplevla-rl 文件夹内)
git clone -b v0.2.x https://github.com/volcengine/verl.git
cd verl
pip3 install -e .
cd ..
```

#### 步骤 1.2: 安装 EGL 库以支持无头渲染

**LIBERO 和 RoboTwin 2.0 基准测试都需要此步骤。**

安装 EGL 库以在 Docker 容器或无显示器的远程服务器上启用无头渲染:

```bash
sudo apt-get update
sudo apt-get install -y libegl1 libegl-dev libegl-mesa0 libegl1-mesa-dev libgles2-mesa-dev
```

> **注意**: 如果没有这些库,在初始化 SAPIEN/机器人环境时可能会遇到 `AttributeError: 'NoneType' object has no attribute 'eglQueryString'` 错误。

#### 步骤 1.3: 安装 LIBERO 和 OpenVLA-OFT

参考官方 [OpenVLA-OFT 安装指南](https://github.com/moojink/openvla-oft):

```bash
conda activate simplevla
pip3 install torch torchvision

# 克隆 OpenVLA-OFT (放在与 simplevla-rl 同级目录,而非 simplevla-rl 文件夹内)
git clone https://github.com/moojink/openvla-oft.git
cd openvla-oft
pip install -e .

# 安装 Flash Attention 2 用于训练
# 如果遇到问题,可以先尝试 `pip cache remove flash_attn`
pip install packaging ninja
ninja --version; echo $?  # 应返回退出码 "0"
pip3 install flash-attn --no-build-isolation

cd ..

# 安装 LIBERO
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git
pip install -e LIBERO
cd openvla-oft
pip install -r experiments/robot/libero/libero_requirements.txt
cd ..
```

---

### 选项 2: 在 RoboTwin 2.0 基准测试上运行 RL

#### 步骤 2.1: 安装 veRL

与选项 1 的步骤 1.1 相同。

#### 步骤 2.2: 安装 EGL 库以支持无头渲染

与选项 1 的步骤 1.2 相同。

#### 步骤 2.3: 安装 RoboTwin 2.0

参考官方 [RoboTwin 2.0 安装指南](https://robotwin-platform.github.io/doc/usage/robotwin-install.html#1-dependencies):

```bash
# 安装系统依赖
sudo apt install libvulkan1 mesa-vulkan-drivers vulkan-tools

conda activate simplevla

# 克隆并安装 RoboTwin
git clone https://github.com/RoboTwin-Platform/RoboTwin.git
cd RoboTwin
bash script/_install.sh

# 下载 RoboTwin 资源
bash script/_download_assets.sh
cd ..
```

#### 步骤 2.4: 安装 OpenVLA-OFT

```bash
conda activate simplevla
pip3 install torch torchvision

# 克隆 OpenVLA-OFT (放在与 simplevla-rl 同级目录,而非 simplevla-rl 文件夹内)
git clone https://github.com/moojink/openvla-oft.git
cd openvla-oft
pip install -e .

# 安装 Flash Attention 2
pip install packaging ninja
ninja --version; echo $?  # 应返回退出码 "0"
pip3 install flash-attn --no-build-isolation
cd ..
```

#### 步骤 2.5: 为 SimpleVLA-RL 配置 RoboTwin

应用必要的 RoboTwin 修改:

```bash
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git
cd SimpleVLA-RL

# 应用 RoboTwin 修改
bash copy_overwrite_robotwin2.sh <your_robotwin_path> <your_simplevlarl_path>
# 示例: bash copy_overwrite_robotwin2.sh /mnt/petrelfs/SimpleVLA-RL /mnt/petrelfs/RoboTwin
```

---

### 故障排除

- 如果在 RoboTwin 2.0 安装过程中遇到问题,请参考 [RoboTwin 文档](https://robotwin-platform.github.io/doc/) 或查看其 GitHub Issues
- 如果遇到 EGL 相关错误,请确保正确安装了所有 EGL 库(参见步骤 1.2/2.2)
- 如果遇到 Flash Attention 安装问题,请尝试清除 pip 缓存: `pip cache remove flash_attn`
- 所有代码仓库(veRL、OpenVLA-OFT、RoboTwin、LIBERO)建议克隆到与 SimpleVLA-RL 相同的目录层级

### 目录结构

安装完成后,您的目录结构应该如下所示:

```
your_workspace/
├── SimpleVLA-RL/
├── verl/
├── openvla-oft/
├── LIBERO/          (用于选项 1)
└── RoboTwin/        (用于选项 2)
```

### 验证安装

完成安装后,验证您的设置:

```bash
# 激活环境
conda activate simplevla

# 验证 PyTorch 安装
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"

# 验证 OpenVLA-OFT 安装
python -c "import openvla; print('OpenVLA imported successfully')"

# 针对 LIBERO (选项 1)
python -c "import libero; print('LIBERO imported successfully')"

# 针对 RoboTwin (选项 2)
python -c "import robotwin; print('RoboTwin imported successfully')"
```

---

### (可选) 在 RoboTwin 2.0 中支持额外任务

#### 步骤 A: 收集可行的种子

RoboTwin 2.0 任务可能有不可行的种子(例如,物体超出机械臂可达范围)。为了优化 RL 训练,我们预先收集可行的种子,以避免在训练轮次中重复验证。

**收集过程**:

1. 在 `pre_collect_robotwin2_seed.sh` 中更新 `DATASET_NAME` 为您的目标任务名称
2. 运行收集脚本:
   ```bash
   sh pre_collect_robotwin2_seed.sh
   ```
3. 这将在 SimpleVLA-RL 目录中生成 `robotwin2_train_seeds.json`
4. 将 JSON 内容添加到:
   ```
   SimpleVLA-RL/verl/utils/envs/robotwin2/seeds/robotwin2_train_seeds.json
   ```

#### 步骤 B: 注册新任务

1. 在 `SimpleVLA-RL/verl/utils/dataset/rob_dataset.py` 中添加任务名称
2. 在 `SimpleVLA-RL/verl/workers/rollout/rob_rollout.py` 中添加任务名称和对应的最大步数

#### 步骤 C: 实现任务特定函数

在 `SimpleVLA-RL/verl/utils/envs/robotwin2/envs/task_name.py` 对应的任务文件中添加 `get_info()` 函数。

实现参考示例:
```
SimpleVLA-RL/modified_codes/robotwin2/envs/handover_block.py
```

## 第二步:准备 SFT 模型

强化学习训练需要一个 **SFT(监督微调)** 的 VLA 模型作为起点。

### 选项 1: 下载预训练 SFT 模型

从 [SimpleVLA-RL Collection](https://huggingface.co/collections/Haozhan72/simplevla-rl-6833311430cd9df52aeb1f86) 下载:

**LIBERO 基准测试模型**:
- `libero-10 traj1 SFT`: 每任务 1 条轨迹训练(冷启动实验)
- `libero-10 trajall SFT`: 每任务所有轨迹训练
- `libero-goal traj1 SFT`: 目标泛化实验
- `libero-object traj1 SFT`: 物体泛化实验
- `libero-spatial traj1 SFT`: 空间泛化实验

**RoboTwin 2.0 基准测试模型**:
- `Robotwin2.0 tasks traj1000 SFT`: 每任务 1000 条轨迹训练

### 选项 2: 从 OpenVLA 官方模型开始

从 [OpenVLA 官方仓库](https://huggingface.co/openvla) 下载预训练模型。

### 选项 3: 自行微调

如需使用其他模型或自定义数据,需要自行进行 SFT 微调。

## 第三步:配置训练参数

在运行训练脚本前,需要配置以下关键参数:

### 1. 配置 WandB(可选但推荐)

在 `SimpleVLA-RL/align.json` 中替换为您的 WandB API 密钥:

```json
{
  "WANDB_API_KEY": "your_wandb_api_key_here"
}
```

### 2. 修改训练脚本

编辑 `examples/run_openvla_oft_rl_libero.sh` 或 `examples/run_openvla_oft_rl_twin2.sh`:

```bash
# 实验配置
export EXPERIMENT_NAME="libero_long_rl_exp1"     # 实验名称
export SFT_MODEL_PATH="/path/to/your/sft/model" # SFT模型路径
export CKPT_PATH="/path/to/save/checkpoints"    # 检查点保存路径

# 数据集配置
export DATASET_NAME="libero-long"  # 选项: libero-10, libero-long, 
                                   #       robotwin2_beat_block_hammer, 等

# 计算资源配置
export NUM_GPUS=8      # 每节点GPU数量
export NUM_NODES=1     # 节点数量

# WandB配置
export ALIGN_PATH="SimpleVLA-RL/align.json"
```

### 3. 关键超参数说明

```bash
# 数据采样配置
data.train_batch_size=64                # 每步训练采样64个任务实例
data.n_samples=8                        # 每任务采样8个轨迹(GRPO需要)

# 动态采样(关键技术1)
data.filter_accuracy=True
data.accuracy_lower_bound=0.1          # 过滤成功率<10%的任务组
data.accuracy_upper_bound=0.9          # 过滤成功率>90%的任务组

# 推理配置(关键技术3)
actor_rollout_ref.rollout.temperature=1.6  # 更高的采样温度

# PPO配置(关键技术2)
actor_rollout_ref.actor.clip_ratio_low=0.2    # 裁剪下界
actor_rollout_ref.actor.clip_ratio_high=0.28  # 裁剪上界(更高!)

# 优化器配置
actor_rollout_ref.actor.optim.lr=5e-6       # 学习率
actor_rollout_ref.actor.ppo_mini_batch_size=128
actor_rollout_ref.actor.ppo_micro_batch_size=8

# 训练进度配置
trainer.total_epochs=20                 # 总轮数(论文用20轮=300步)
trainer.save_freq=20                    # 每20步保存检查点
trainer.test_freq=4                     # 每4步验证一次
```

## 第四步:启动 RL 训练

### LIBERO 基准测试

```bash
bash examples/run_openvla_oft_rl_libero.sh
```

### RoboTwin 2.0 基准测试

```bash
bash examples/run_openvla_oft_rl_twin2.sh
```

### 预期训练时间

**硬件配置**: 8×NVIDIA A800 GPU(80GB)

| 配置 | 训练步数 | 预计时间 | 说明 |
|------|---------|---------|------|
| 论文设置 | 300步 | ~4.3天 | 20轮,每步约20分钟 |
| 配置文件 | 1500步 | ~21天 | 100轮(可调整) |

**时间分解(每训练步)**:
- 数据收集(Rollout): ~18分钟(87.8%)
- PPO更新: ~2.4分钟(11.8%)
- 其他操作: ~0.2分钟(0.4%)

## 第五步:运行评估

要评估训练好的模型,在脚本中启用验证模式:

```bash
# 在 run_openvla_oft_rl_libero.sh 中添加
trainer.val_only=True
```

然后运行相同的脚本:

```bash
bash examples/run_openvla_oft_rl_libero.sh
```

---

# 📊 训练过程详解

## 训练循环概览

每个训练步包含以下阶段:

```
训练步 i
│
├─ 1. 数据采样
│   └─ 从数据集采样 64 个任务实例
│
├─ 2. 轨迹推理(Rollout)
│   ├─ 每任务生成 8 条轨迹
│   ├─ VLA 模型推理
│   ├─ 环境交互
│   └─ 收集轨迹数据
│
├─ 3. 动态采样过滤
│   └─ 过滤全成功/全失败的任务组
│
├─ 4. 奖励计算
│   └─ 应用结果奖励(成功=1.0,失败=0.0)
│
├─ 5. 优势估计(GRPO)
│   ├─ 按任务分组
│   ├─ 计算组内平均回报作为基线
│   └─ 优势 = 个体回报 - 组平均
│
├─ 6. 策略更新(PPO)
│   ├─ Mini-batch循环
│   ├─ 计算策略损失(带裁剪)
│   ├─ 反向传播
│   └─ 梯度裁剪和优化器更新
│
├─ 7. 验证(每4步)
│   └─ 在256个任务上评估成功率
│
└─ 8. 保存检查点(每20步)
    └─ 保存模型权重和优化器状态
```

## GRPO 优势估计详解

**Group Relative Policy Optimization (GRPO)** 是专为结果奖励设计的优势估计方法:

### 为什么需要 GRPO?

传统的 Generalized Advantage Estimation (GAE) 需要:
- 训练额外的价值网络 V(s)
- 密集的中间奖励信号
- 更复杂的训练流程

GRPO 的优势:
- ✅ 无需价值网络
- ✅ 仅需结果奖励
- ✅ 通过组内相对比较进行学习

### 算法原理

对于同一任务的 N 个轨迹:

```python
# 1. 计算每条轨迹的总回报
R_i = Σ 奖励  # i = 1, 2, ..., N (N=8)

# 2. 计算组内平均作为基线
baseline = (1/N) × Σ R_i

# 3. 计算优势
A_i = R_i - baseline
```

### 示例

```
任务1的8条轨迹:
回报: [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0]
基线: 0.5
优势: [-0.5, 0.5, -0.5, 0.5, -0.5, 0.5, 0.5, -0.5]
     ↑    ↑    ↑    ↑     ↑    ↑    ↑    ↑
     差   好   差   好    差   好   好   差

含义: 成功的轨迹获得正优势,失败的轨迹获得负优势
     策略将学习增加成功轨迹的概率,减少失败轨迹的概率
```

## PPO 策略更新详解

### 标准 PPO vs SimpleVLA-RL

```python
# 标准 PPO 目标函数
ratio = π(a|s) / π_old(a|s)
clipped_ratio = clip(ratio, 0.8, 1.2)  # 对称裁剪
loss = -min(ratio × A, clipped_ratio × A)

# SimpleVLA-RL: Clip Higher
clipped_ratio = clip(ratio, 0.8, 1.28)  # 不对称裁剪!
loss = -min(ratio × A, clipped_ratio × A)
```

### 为什么 Clip Higher 有效?

**场景**: 某个低概率动作(p=0.1)在一次探索中获得成功

```
标准 PPO (clip_high=0.2):
- ratio = 0.15 / 0.1 = 1.5
- clipped_ratio = 1.2 (被限制!)
- 概率最多增长 20%
- 新概率 ≤ 0.12

Clip Higher (clip_high=0.28):
- ratio = 1.5
- clipped_ratio = 1.5 (未被限制!)
- 概率可增长 50%
- 新概率 ≤ 0.15

结果: Clip Higher 允许更大的策略更新,鼓励探索
```

---

# 🔍 重要概念解释

## 什么是"推切(Pushcut)"现象?

**推切**是 RL 训练过程中策略自主发现的新颖操作模式,**从未在训练演示中出现**。

### 发现过程

**SFT 模型**:仅从人类演示学习
```
标准操作序列:
1. 接近物体
2. 抓取物体
3. 垂直抬起物体(避开桌面)
4. 水平移动到目标位置
5. 放下物体
6. 松开抓手
```

**RL 训练后**:发现更优策略
```
"推切"操作序列:
1. 接近物体
2. 抓取或接触物体
3. 保持低位(贴近桌面)
4. 水平推动/拖拽物体到目标位置
5. 任务完成!
   ↑
   无需抬起动作,更快速且鲁棒!
```

### 观察到推切现象的任务

- ✅ **move_can_pot**: 推动罐子而非抬起
- ✅ **place_a2b_left/right**: 推动物体A而非抓放
- ❌ **beat_block_hammer**: 未观察到(需要抓取工具)

### 为什么推切更优?

1. **更快执行**: 更少的垂直运动,更直接的路径
2. **更鲁棒**: 对精确定位要求更低
3. **能量高效**: 无需对抗重力
4. **碰撞安全**: 贴近桌面减少碰撞风险
5. **保持接触**: 推动自然维持物体接触

### 意义

这一发现证明:
- ✅ RL 能发现人类未演示的策略
- ✅ 超越模仿学习的限制
- ✅ 展示对任务目标的真实理解(而非仅复制动作)
- ✅ 类似 AlphaGo 发现非常规但最优的着法

## 动作分块(Action Chunking)如何工作?

### 与 ReAct 模式的对比

**ReAct 模式**(单步):
```
每步:
  观察 → LLM推理 → 生成1个动作 → 执行 → 下一步

总计(200环境步): 200次LLM调用
```

**VLA 动作分块**(多步规划):
```
每轮:
  观察 → VLA推理 → 生成25个未来动作 → 全部执行 → 下一轮

总计(200环境步): 8次VLA调用(200÷25=8)
```

### 执行时间线

```
时间轴:    0ms    300ms    1800ms   2100ms   3600ms
          |       |         |        |        |
GPU:      [VLA 1] 空闲      [VLA 2]  空闲     [VLA 3]
          ↓                         ↓
动作:     生成25   执行25    生成25   执行25
          个动作   个动作    个动作   个动作
          
环境步:   0       0→24      25      25→49    50
          
机器人:   静止    运动...   运动... 运动...  运动...
```

### 为什么使用动作分块?

1. **计算效率**: 8次推理 vs 200次 = **25倍减少**
2. **自然运动**: 产生流畅的轨迹,避免抖动
3. **时序一致性**: 强制动作序列的连贯性
4. **减少累积误差**: 更少的重新规划减少漂移

### 真实部署中机器人会暂停吗?

**答案:不会!** 真实部署使用**缓冲执行**:

```
VLA线程:    持续计算下一批25个动作
            ↓
动作缓冲区:  [动作0-24] → [动作25-49] → [动作50-74]
            ↓           ↓            ↓
控制线程:   执行动作    执行动作      执行动作
            (50Hz)     (50Hz)       (50Hz)

结果: 机器人保持连续、流畅的运动,无暂停!
```

**关键条件**:
```
VLA推理时间 < 动作分块执行时间
300ms < (25动作 × 50ms/动作) = 1250ms ✓

安全边际: 1250ms / 300ms = 4倍 ✓
```

---

# ⚠️ 注意事项

## 训练配置

### 关键超参数

三大关键技术的超参数**务必保留**:

```bash
# 1. 动态采样
data.accuracy_lower_bound=0.1
data.accuracy_upper_bound=0.9

# 2. 更高裁剪界
actor_rollout_ref.actor.clip_ratio_high=0.28

# 3. 更高推理温度
actor_rollout_ref.rollout.temperature=1.6
```

这三个参数共同贡献了约 **30%** 的性能提升!

---

# 实验结果

[SimpleVLA RL rollout 结果（即机器人在虚拟环境中操作的视频）](https://01.me/files/ai-agent-book/SimpleVLA-RL-rollouts.zip)

[wandb 实验结果](https://wandb.ai/bojieli-pine-ai/SimpleVLA-RL)

## 实验概述

根据文档，本实验在 RoboTwin 2.0 基准测试上运行了两个关键任务：
- **beat_block_hammer**: 工具使用任务（抓取锤子击打方块）
- **move_can_pot**: 空间推理任务（将罐子移动到锅旁）

## 详细分析

### 1. Actor 训练指标分析

**PPO KL 散度 (ppo_kl)**:
- 两个任务的 KL 散度都维持在较低水平 (~0.002-0.008)
- 说明策略更新幅度适中，没有过度偏离参考策略
- 符合 PPO 算法的稳定性要求

**策略梯度损失 (pg_loss)**:
- `beat_block_hammer` 显示更高的损失值和更大的波动
- `move_can_pot` 的损失相对稳定且较低
- 反映了工具使用任务的复杂性更高

**策略梯度裁剪比例 (pg_clipfrac)**:
- 两个任务都保持在 0.01-0.03 范围内
- 适度的裁剪表明**更高裁剪界 (1.28)** 技术发挥作用
- 允许了更大胆的策略探索，同时保持训练稳定

**学习率和梯度范数**:
- 学习率稳定在 5e-6，符合配置
- 梯度范数在合理范围内，训练过程稳定

### 2. 训练奖励分析

**验证器奖励 (train_reward/verifier)**:
- `beat_block_hammer`（橙色）: 从 ~0.3 提升到 ~0.75，**增长 150%**
- `move_can_pot`（蓝色）: 从 ~0.15 提升到 ~0.6，**增长 300%**
- 说明两个任务都从强化学习中获得显著收益

**总体奖励 (train_reward/reward_all)**:
- 趋势与验证器奖励类似但数值更高
- 这符合 GRPO 算法的设计，其中组内平均作为基线

### 3. 验证分数分析

**训练验证分数 (train_verify_score/all)**:
- `beat_block_hammer` 最终达到 ~0.8 (80% 成功率)
- `move_can_pot` 最终达到 ~0.67 (67% 成功率)
- 与论文预期的 60-80% 成功率一致

**测试验证分数 (val/test_score)**:
- **IID 测试** (训练分布内):
  - `beat_block_hammer`: ~0.85 成功率
  - `move_can_pot`: ~0.63 成功率
- **OOD 测试** (分布外):
  - `beat_block_hammer`: ~0.78 成功率  
  - `move_can_pot`: ~0.58 成功率
- IID/OOD 性能差距小，表明良好的泛化能力

### 4. Critic 网络分析

**奖励分数统计**:
- **最小值**: 两个任务都从 0 开始，符合二元奖励设置
- **均值**: 稳定上升，反映平均成功率提升
- **最大值**: 两个任务都达到最高奖励值

**分数分布**:
- 显示了健康的探索-利用平衡
- 符合**动态采样**技术的预期效果

### 5. 探索策略分析

**熵损失 (actor_after/entropy_loss_eval)**:
- `beat_block_hammer` 显示更高的熵值（更多探索）
- `move_can_pot` 熵值逐渐降低但保持合理水平
- 说明**更高推理温度 (1.6)** 成功促进了探索

## 性能对比

### 与论文基线比较

本实验在 RoboTwin 2.0 上的结果：
- `beat_block_hammer`: 80% 成功率
- `move_can_pot`: 67% 成功率
- 符合论文预期的性能范围

### 冷启动能力
实验展现了 RL 在数据稀缺条件下的强大能力：
- 从有限的 SFT 初始化开始
- 通过结果奖励实现显著性能提升
- 证明了 RL 能够**超越人类演示的限制**

---

# 🌻 致谢

本项目基于以下优秀开源项目开发:

- **[veRL](https://github.com/volcengine/verl)**: 火山引擎 LLM 强化学习框架
- **[OpenVLA-OFT](https://github.com/moojink/openvla-oft)**: 开源视觉-语言-动作模型
- **[RoboTwin2.0](https://github.com/RoboTwin-Platform/RoboTwin)**: 双臂机器人操作基准测试
- **[LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO)**: 终身机器人学习基准测试
- **[PRIME](https://github.com/PRIME-RL/PRIME)**: 强化学习研究框架

感谢以上项目的重要贡献!更多详情和更新,请参阅各项目的官方文档和代码仓库。

---

# 📨 联系方式

如有问题或建议,欢迎联系:

- **李浩展**: zhan72426@gmail.com
- **丁宁**: dingning@mail.tsinghua.edu.cn

或在 [GitHub Issues](https://github.com/PRIME-RL/SimpleVLA-RL/issues) 提出问题。

---

# 📝 TODO

## 模型支持

- ✅ 支持 OpenVLA 和 OpenVLA-OFT
- ⏳ 支持 Pi0 快速分词器
- ⏳ 支持更多 VLA 架构(RT-1, RT-2)

## 基准测试

- ✅ 支持 LIBERO 基准测试
- ✅ 支持 RoboTwin 基准测试
- ⏳ 支持 CALVIN 基准测试
- ⏳ 支持真实机器人硬件

## 算法改进

- ⏳ 支持 GPU 加速模拟器(Isaac Gym)
- ⏳ 支持分布式训练(多节点)
- ⏳ 支持在线课程学习

---

# 🎈 引用

如果您觉得 SimpleVLA-RL 对您的研究有帮助,请引用我们的论文:

```bibtex
@article{li2025simplevla,
  title={SimpleVLA-RL: Scaling VLA Training via Reinforcement Learning},
  author={Li, Haozhan and Zuo, Yuxin and Yu, Jiale and Zhang, Yuhao and Yang, Zhaohui and Zhang, Kaiyan and Zhu, Xuekai and Zhang, Yuchen and Chen, Tianxing and Cui, Ganqu and others},
  journal={arXiv preprint arXiv:2509.09674},
  year={2025}
}
```

同时也请引用 RoboTwin 2.0 基准测试:

```bibtex
@article{robotwin2025,
  title={RoboTwin 2.0: A Scalable Data Generator and Benchmark with Strong Domain Randomization for Robust Bimanual Robotic Manipulation},
  author={...},
  journal={arXiv preprint arXiv:2506.18088},
  year={2025}
}
```
