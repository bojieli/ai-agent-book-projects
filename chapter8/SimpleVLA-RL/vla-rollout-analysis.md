# VLA Rollout Process Analysis - GPU Utilization Patterns

**Based on**: [SimpleVLA-RL: Scaling VLA Training via Reinforcement Learning](https://arxiv.org/pdf/2509.09674) (2025)

## Architecture Overview

### Distributed System Components
- **Ray Framework**: Orchestrates distributed training across 8 GPUs
- **Actor-Critic PPO**: Separate workers for ActorRollout, Critic, and RefPolicy
- **Resource Pool**: All roles share the same GPU pool (global_pool_id)
- **Configuration**: 8 GPUs on 1 node, micro_batch_size=1, action_chunks_len=25

## Rollout Pipeline Phases

The rollout process alternates between **GPU-intensive** and **CPU-intensive** phases, causing the observed utilization patterns.

### Phase 1: Environment Initialization (CPU-Bound) 🔴 **GPUs ~0%**
**Location**: `rob_rollout.py:623-646`

```python
# Create environment wrappers for each task
env_wrappers = []
for idx in range(batch_size):
    wrapper = RobotwinEnvWrapper(task_name, tr_id, tr_seed, ...)
    env_wrappers.append(wrapper)

# Initialize environments in parallel using ThreadPoolExecutor
init_futures = []
for wrapper in env_wrappers:
    future = self.env_thread_pool.submit(wrapper.initialize)  # CPU-bound
    init_futures.append(future)
```

**What happens**:
- Creates SAPIEN physics environments for RoboTwin 2.0 tasks
- Loads robot models, scene assets, camera configurations
- Sets up task-specific initial states and randomizations
- Uses `threading.Lock` to serialize Robotwin initialization
- **Duration**: 5-15 seconds per batch

**Why GPUs are idle**:
- Environment setup is pure CPU work (YAML parsing, scene construction)
- SAPIEN physics engine runs on CPU (MuJoCo/EGL rendering)
- No neural network operations occur during this phase

---

### Phase 2: Observation Processing (Mixed CPU/GPU) 🟡 **GPUs ~30-50%**
**Location**: `rob_rollout.py:649-678`

```python
# Collect initial observations from all environments
for idx, wrapper in enumerate(env_wrappers):
    obs = wrapper.get_obs()  # CPU: Get image + proprio from environment
    obs = encode_obs(obs)    # CPU: Minimal processing
    inputs.append(self._obs_to_input(obs, ...))  # CPU: Format conversion
```

**What happens**:
- Retrieves RGB images (224x224x3) from head_camera, left_wrist, right_wrist
- Extracts proprioceptive state (14-dim joint positions)
- Converts NumPy arrays to PIL Images
- **Duration**: 100-300ms per batch

**Why GPU usage is low**:
- Data is still on CPU (NumPy/PIL)
- GPU only used if batching operations trigger early transfers
- Main bottleneck: retrieving rendered images from SAPIEN

---

### Phase 3: VLA Inference (GPU-Bound) 🟢 **GPUs ~100%**
**Location**: `rob_rollout.py:690-708`

```python
# Prepare inputs for VLA model
vla_input = self.process_input(current_inputs, current_task_descriptions)
# Process images, tokenize text, prepare proprio
# → Transfers data to GPU, pads sequences, applies center crop

# Generate actions from VLA model  
vla_output = self._generate_one_step(vla_input)
# → Runs full VLA forward pass:
#    1. Vision encoder (DINOv2/SigLIP): extract image features
#    2. Projector: map vision to language space  
#    3. LLM (Llama-7B): generate action tokens
#    4. Action decoder: convert tokens to continuous actions
```

#### Detailed VLA Model Forward Pass

**3.1 Input Processing** (`rob_rollout.py:509-600`):
```python
def process_input(inputs, task_descriptions):
    for i in range(len(inputs)):
        # Image preprocessing
        image = Image.fromarray(input_data["full_image"]).convert("RGB")
        if self.config.center_crop:
            image = center_crop_image(image)  # TensorFlow ops on CPU
        
        # Tokenization
        prompt = f"In: What action should the robot take to {task_description}?\nOut:"
        batch_feature = self.processor(prompt, image)  # HuggingFace processor
        
        # Multi-view images
        pixel_values_list = [batch_feature["pixel_values"]]
        # Add wrist camera images if using multiple views
        
        # Proprioception normalization
        proprio = normalize_proprio(proprio, norm_stats)  # CPU
        
    # Transfer to GPU and pad
    batchdata["input_ids"] = pad_sequence(...).to(device)
    batchdata["pixel_values"] = torch.cat(...).to(device)
    batchdata["proprio"] = torch.stack(...).to(device)
```

**3.2 VLA Generation** (`rob_rollout.py:930-983`):
```python
def _generate_one_step_oft(prompts):
    with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
        actions, response = self.module.generate_action_verl(
            input_ids=idx,              # (batch, seq_len) e.g., (8, 64)
            pixel_values=pixel_values,  # (batch, num_images*patches, dim)
            proprio=proprio,            # (batch, 14) for RoboTwin
            attention_mask=attention_mask,
            temperature=1.6,  # Higher Rollout Temperature (Paper Section 3.3)
                             # Increased from 1.0 to 1.6 for exploration
                             # One of three key enhancements in SimpleVLA-RL
            unnorm_key=self.config.unnorm_key  # For action denormalization
        )
```

**VLA Model Architecture** (from `modeling_prismatic.py`):
```
OpenVLA-OFT Model:
├── Vision Backbone (PrismaticVisionBackbone)
│   ├── Primary Featurizer (SigLIP-400M): 224x224 → 256 patches × 1152 dim
│   └── [Optional] Fused Featurizer (DINOv2): 224x224 → 256 patches × 768 dim
│   → Output: (batch, num_images*256, 1920) for fused backbone
│
├── Projector (nn.Linear + LayerNorm)
│   └── Maps vision features: 1920 → 4096 (Llama hidden dim)
│
├── [Optional] Proprio Projector (ProprioProjector)
│   └── Maps proprio: 14 → 4096 via MLP (fc1 → GELU → fc2)
│
├── Language Model (Llama-7B)
│   ├── Input: concatenate [vision_embeddings, proprio_embedding, text_embeddings]
│   ├── Autoregressive generation with temperature sampling
│   └── Output: action tokens (14 tokens per action chunk)
│
└── Action Decoder
    ├── Token IDs → Discretized bins (256 bins per dimension)
    ├── Bin centers → Normalized actions [-1, 1]
    └── Denormalization using task statistics → Raw actions
```

**Computation Breakdown**:
1. **Vision Encoding**: ~40% of GPU time
   - SigLIP: 400M params, attention over 256 patches
   - DINOv2: Additional 300M params if using fused backbone
   - Forward pass: 6 transformer blocks + pooling

2. **LLM Generation**: ~50% of GPU time
   - Llama-7B: 7B parameters
   - Generates 14×25=350 tokens for 25-chunk actions
   - Each token requires full attention over previous tokens
   - With `do_sample=True` and `temperature=1.6`

3. **Projection Layers**: ~10% of GPU time
   - Linear projections: relatively fast

**Key Configuration**:
- `action_token_len=14`: Each action is 14 tokens (7 DOF × 2 arms)
- `action_chunks_len=25`: Generates 25 future actions per step
- `temperature=1.6`: **Higher Rollout Temperature** (Paper Section 3.3)
  - Increased from standard 1.0 to 1.6 for diverse trajectory generation
  - One of three key exploration enhancements in SimpleVLA-RL
  - Achieves ~15% improvement over baseline (Figure 3c)
  - Widely used in recent LLM RL work (Liu et al., 2025c; An et al., 2025)
- `gpu_memory_utilization=0.9`: Uses 90% of GPU memory

**Why all GPUs are busy**:
- Batch size = 8 (one per GPU with FSDP)
- Full model forward + autoregressive sampling
- bfloat16 mixed precision
- **Duration**: 200-500ms per step (depends on model size and action length)

---

### Phase 4: Action Execution (CPU-Bound) 🔴 **GPUs ~0-10%**
**Location**: `rob_rollout.py:711-741`

```python
# Execute actions in parallel across all active environments
step_futures = []
for idx in active_indices:
    future = self.env_thread_pool.submit(
        env_wrappers[idx].step,  # CPU-bound physics simulation
        actions[idx]              # 25 action chunks
    )
    step_futures.append((idx, future))

# Wait for all environments to finish stepping
for idx, future in step_futures:
    obs, done = future.result(timeout=120)
    # Each env executes 25 steps of physics simulation
```

**What happens in `env_wrapper.step()`** (`rob_rollout.py:299-326`):
```python
def step(self, action):  # action shape: (25, 14)
    with self.lock:  # Thread-safe execution
        for i in range(action.shape[0]):  # 25 iterations
            self.env.take_action(action[i])  # SAPIEN physics step
            # - Update robot joint positions
            # - Simulate physics contacts and dynamics
            # - Render cameras (RGB images)
            # - Check collision and success conditions
        
        done = self.env.eval_success
        obs = self.env.get_obs()  # Get new observation
        self.finish_step += action.shape[0]
```

**SAPIEN Physics Execution**:
- **Per-step operations** (×25 for action chunks):
  - Joint PD controller: computes torques
  - Forward dynamics: updates positions/velocities
  - Collision detection: broadphase + narrowphase
  - Contact solver: computes contact forces
  - Rendering: generates RGB images from cameras
  
- **Parallelism**: 
  - `ThreadPoolExecutor(max_workers=16)` handles up to 16 envs concurrently
  - But each env runs serially (SAPIEN is not GPU-accelerated)
  - Thread lock ensures thread safety for RoboTwin

**Why GPUs are mostly idle**:
- SAPIEN/MuJoCo physics runs entirely on CPU
- EGL rendering uses CPU (OpenGL software rasterization)
- Only occasional GPU usage if rendering uses GPU (minimal)
- **Duration**: 500-2000ms per batch (dominates rollout time!)

---

### Phase 5: Cleanup & Video Saving (CPU-Bound) 🔴 **GPUs ~0%**
**Location**: `rob_rollout.py:746-770`

```python
# Close all environments
cleanup_futures = []
for wrapper in env_wrappers:
    future = self.env_thread_pool.submit(wrapper.close)
    cleanup_futures.append(future)

torch.cuda.empty_cache()  # Clear GPU memory
gc.collect()              # Python garbage collection

# Save validation videos
if is_valid:
    for task_file, images in valid_video.items():
        save_rollout_video(images, ...)  # CPU: encode video
```

**What happens**:
- Close SAPIEN scenes and release resources
- Write video files (H.264 encoding on CPU)
- Synchronize threads
- **Duration**: 1-3 seconds per batch

---

## Why GPU Utilization is Unbalanced

### Root Causes:

#### 1. **Sequential Phases Within Each Rollout**
The rollout loop alternates between GPU and CPU work:
```
Initialize Envs (CPU) → Get Obs (CPU) → VLA Inference (GPU) 
→ Execute Actions (CPU) → Get Obs (CPU) → VLA Inference (GPU) → ...
→ Cleanup (CPU)
```
- During CPU phases, GPUs are idle
- During GPU phases, CPUs are idle
- **Imbalance ratio**: ~70% CPU time, ~30% GPU time per rollout

#### 2. **Ray Distributed Execution**
From `main_ppo.py:159-173`:
```python
role_worker_mapping = {
    Role.ActorRollout: ray.remote(RobActorRolloutRefWorker),
    Role.Critic: ray.remote(CriticWorker),
    Role.RefPolicy: ray.remote(RobActorRolloutRefWorker)
}

resource_pool_spec = {
    global_pool_id: [8] * 1,  # 8 GPUs on 1 node
}
mapping = {
    Role.ActorRollout: global_pool_id,
    Role.Critic: global_pool_id,
    Role.RefPolicy: global_pool_id,
}
```

- **All roles share the same GPU pool**
- Ray schedules tasks dynamically:
  - Some GPUs may be running rollout (Phase 3: 100% GPU)
  - Other GPUs may be idle waiting for envs to finish (Phase 4: 0% GPU)
  - Critic training may be running on some GPUs (intermittent 100%)
  
- **Synchronization barriers**:
  - PPO requires collecting full batches before training
  - Some workers finish rollout early and wait for others
  - This causes the "some GPUs at 0%, others at 100%" pattern

#### 3. **Micro-Batch Size = 1**
From `run_openvla_oft_rl_twin2.sh:65`:
```bash
actor_rollout_ref.rollout.micro_batch_size=1
```

- Each GPU processes **only 1 environment at a time**
- No pipelining between CPU and GPU work
- If using `micro_batch_size=4`, could overlap:
  - GPU: Process batch 1 inference
  - CPU: Execute batch 2 actions
  - But current config doesn't allow this

#### 4. **Action Chunking Amplifies CPU Bottleneck**
From config:
```bash
actor_rollout_ref.model.action_chunks_len=25
```

- VLA generates 25 actions in one inference (GPU: ~300ms)
- Then environment executes all 25 steps serially (CPU: ~1500ms)
- **5× longer CPU execution than GPU inference!**
- During those 1500ms, GPU is completely idle

#### 5. **Environment Initialization Serialization**
From `rob_rollout.py:75`:
```python
_ENV_INIT_LOCK = threading.Lock()

def initialize(self):
    with _ENV_INIT_LOCK:  # Serialize initialization!
        with self.lock:
            self.env, self.args = get_robotwin2_task(...)
            self.env.setup_demo(...)
```

- **All environments initialize serially** (not parallel!)
- Even though ThreadPoolExecutor has 16 workers
- This is to prevent SAPIEN resource conflicts
- Causes initial ~0% GPU phase to be very long

---

## Expected GPU Usage Patterns

### Pattern 1: All GPUs at 0%
**When**: 
- Batch initialization (beginning of epoch)
- Action execution phase (most of the time)
- Environment cleanup

**Duration**: 60-70% of rollout time

### Pattern 2: All GPUs at 100%
**When**: 
- VLA inference phase
- All workers are synchronized at inference

**Duration**: 20-30% of rollout time

### Pattern 3: Unbalanced (some 30%, others 0%)
**When**:
- Workers finish inference at different times
- Some workers finish rollout early, waiting for stragglers
- Critic training starts while some rollouts still running
- Ray resource contention between ActorRollout/Critic/RefPolicy

**Duration**: 10-20% of time (transition periods)

---

## Performance Bottleneck Analysis

### Timing Breakdown (per rollout step):
```
1. Get observation:        ~50ms   (CPU)
2. Process input:          ~100ms  (CPU → GPU transfer)
3. VLA inference:          ~300ms  (GPU) ← Only GPU-intensive part!
4. Execute 25 actions:     ~1500ms (CPU) ← BOTTLENECK!
5. Get new observation:    ~50ms   (CPU)
-------------------------------------------
Total per step:            ~2000ms
GPU utilization:           15% (300ms / 2000ms)
```

### Over full rollout (200 steps for beat_block_hammer):
```
Total steps: 200 / 25 = 8 VLA inferences
Total time: ~16 seconds
GPU active time: ~2.4 seconds (15%)
CPU active time: ~13.6 seconds (85%)
```

### Why Action Execution is the Bottleneck:
1. **SAPIEN physics is single-threaded** per environment
2. **No GPU acceleration** for physics simulation
3. **25 serial steps** per VLA inference
4. **Rendering overhead**: 3 cameras (head + 2 wrists) × 25 steps

---

## Optimization Recommendations

### ⚠️ Important Note from Paper

The SimpleVLA-RL paper already implements **three critical optimizations** that significantly improve performance:

1. **Higher Rollout Temperature (1.6)**: Already in your config! `temperature=1.6`
2. **Dynamic Sampling**: Already in your config! `accuracy_lower_bound=0.1, accuracy_upper_bound=0.9`
3. **Clip Higher**: Already in your config! `clip_ratio_high=0.28`

These three enhancements achieve **~30% improvement** over baseline. Before adding more optimizations, ensure these are working correctly by monitoring:
- Dynamic sampling retention rate (~70-80% is good)
- Policy exploration metrics (`actor/entropy`)
- Success rate improvements over training

### 🚀 Additional High-Impact Optimizations

Beyond what the paper already implements:

#### 1. Reduce Action Chunking (Experimental)
```bash
# Current (Paper setting)
action_chunks_len=25  # GPU idle for 1500ms

# Proposed (Trade-off)
action_chunks_len=10  # GPU idle for 600ms
```
**Trade-off**: More frequent VLA calls improves GPU utilization but:
- May reduce planning horizon for the policy
- Paper uses 25 chunks - changing this may affect performance
- **Recommendation**: Only try if rollout speed is critical bottleneck

#### 2. Increase Micro-Batch Size
```bash
# Current
micro_batch_size=1  # No pipelining

# Proposed  
micro_batch_size=4  # Process 4 envs per GPU
```
**Benefit**: Can overlap CPU/GPU work across different batches

#### 3. Async Rollout with Pipeline
Modify `_generate_minibatch_robotwin` to:
```python
# Pseudocode
queue = deque(maxlen=2)
queue.append(get_observations())  # Batch 0

while not done:
    # GPU: Inference on batch i
    vla_output = vla_inference(queue.popleft())
    
    # CPU (parallel): Execute batch i-1 actions + collect batch i+1 obs
    with ThreadPoolExecutor():
        execute_actions(vla_output)
        queue.append(get_observations())
```
**Benefit**: Hide CPU latency behind GPU work

#### 4. Use GPU-Accelerated Simulator
Consider replacing SAPIEN with:
- **Isaac Gym/Isaac Sim**: GPU-accelerated physics
- **MuJoCo XLA**: TPU/GPU support
**Benefit**: 10-100× faster physics simulation

#### 5. Distributed Rollout Workers
```python
# Current: All roles share 8 GPUs
mapping = {
    Role.ActorRollout: global_pool_id,
    Role.Critic: global_pool_id,
    Role.RefPolicy: global_pool_id,
}

# Proposed: Dedicated resources
resource_pool_spec = {
    'rollout_pool': [4] * 1,  # 4 GPUs for rollout
    'train_pool': [4] * 1,    # 4 GPUs for critic/ref
}
mapping = {
    Role.ActorRollout: 'rollout_pool',
    Role.Critic: 'train_pool',
    Role.RefPolicy: 'train_pool',
}
```
**Benefit**: Eliminate resource contention

---

## Monitoring and Debugging

### Recommended Tools:
```bash
# Real-time GPU monitoring
nvidia-smi dmon -s u -d 1  # Update every 1 second

# Detailed profiling
pip install py-spy
py-spy record -o profile.svg -- python -m verl.trainer.main_ppo ...

# Ray dashboard
# Access at http://localhost:8265 to see task scheduling
```

### Key Metrics to Track:
1. **GPU Utilization %** per device
2. **GPU Memory Usage** (should be ~90% during inference)
3. **Ray Task Queue Length** (indicates scheduling bottlenecks)
4. **Env Step Time** vs **VLA Inference Time** ratio
5. **Samples per Second** (throughput metric)

---

## Understanding VLA Concepts

### What is "Pushcut"?

**Pushcut** is a novel manipulation strategy discovered by the RL-trained VLA policy that was **never demonstrated in the training data**. This phenomenon is described in the SimpleVLA-RL paper (Section 6.1) and represents a key finding about RL's ability to discover optimal behaviors beyond imitation.

**Where pushcut was observed**:
- ✅ **move_can_pot task**: Pushing can instead of grasping and lifting
- ✅ **place_a2b_left/right task**: Pushing Object A instead of pick-and-place

#### The Discovery

**Before RL (SFT Model)**:
- Trained only on human demonstrations
- Learned strategy: **Grasp → Lift → Move → Place**
- Standard pick-and-place approach mimicking human behavior
- Always lifts objects vertically before horizontal motion

**After RL Training (in applicable tasks)**:
- Discovered strategy: **Grasp → Push/Slide horizontally**
- Instead of lifting objects, the robot keeps the gripper low
- Pushes or drags objects across the table surface toward the target
- More like sliding a chess piece than picking it up

#### Example: move_can_pot Task

**SFT Strategy** (from demonstrations):
```
1. Approach can
2. Grasp can with gripper
3. Lift can upward (clear the table)
4. Move can horizontally toward target position beside pot
5. Lower can carefully to table surface
6. Release gripper and complete placement
```

**RL "Pushcut" Strategy** (discovered):
```
1. Approach can
2. Grasp can (or just make contact)
3. Push/slide can horizontally toward target (staying low)
4. Drag can across table surface beside pot
5. Success achieved through pushing motion
6. No vertical lift required! (faster and more robust)
```

**Note on beat_block_hammer Task**: The pushcut phenomenon was **NOT** observed in the hammer task. The hammer task still requires grasping and striking motions due to the nature of tool use.

#### Why "Pushcut" Works Better

**Advantages**:
1. **Faster Execution**: Fewer vertical motions, more direct path
2. **More Robust**: Less precise positioning required
3. **Energy Efficient**: No need to lift against gravity
4. **Collision Safe**: Staying close to table reduces risk of hitting obstacles
5. **Natural Contact**: Pushing naturally maintains contact with objects

**Physics Insight**:
- Friction with table provides stability during push
- Continuous contact reduces uncertainty
- Less reliance on precise gripper control
- More forgiving of position errors

#### Why This Matters

**1. Emergence of Novel Behaviors**:
- RL discovers strategies humans didn't demonstrate
- Goes beyond imitation learning limitations
- Shows true understanding of task goals (contact block), not just copying actions

**2. Optimality Discovery**:
- RL explores action space to find more efficient solutions
- Not constrained by human demonstration biases
- Similar to AlphaGo discovering unconventional but optimal moves

**3. Task Understanding**:
- Policy learned the task is "make hammer contact block"
- Not "copy human lifting motion exactly"
- Demonstrates goal-directed reasoning vs behavior cloning

**4. Exploration Success**:
- Higher Rollout Temperature (1.6) enabled diverse strategy exploration
- Dynamic Sampling focused learning on improvable scenarios
- PPO with Clip Higher allowed bolder policy updates
- These three enhancements (paper Section 3.3) enabled discovery

#### Broader Implications

**For VLA Research**:
- RL enables creativity beyond supervised learning
- Outcome-based rewards (success/failure) sufficient for discovery
- No need to hand-craft dense rewards for every sub-behavior
- Demonstrates transfer from reasoning models (DeepSeek-R1) to action models (VLA)

**For Robotics**:
- Policies can discover human-unintuitive but efficient strategies
- Simulation enables safe exploration of novel behaviors
- Real-world transfer may discover additional optimizations
- Suggests RL as path to superhuman manipulation skills

---

### How VLA Inference Steps Work with Environment Steps

**TL;DR**: VLA is **NOT** like ReAct. Instead of generating one action per observation (single-step), VLA uses **action chunking** to generate 25 future actions at once (multi-step planning).

#### ReAct Pattern (Single-Step)

The ReAct pattern you're thinking of works like this:
```
Loop until task done:
  1. Observe environment state
  2. LLM thinks and generates ONE action
  3. Execute that ONE action
  4. Get new observation
  5. Repeat
```

**Characteristics**:
- High-frequency LLM calls (one per step)
- Reactive: responds to immediate observations
- Myopic: only considers current state
- Fine-grained control but high computational cost

**Example** (200 environment steps):
```
Step 0:   obs₀ → LLM → action₀ → execute → obs₁
Step 1:   obs₁ → LLM → action₁ → execute → obs₂
Step 2:   obs₂ → LLM → action₂ → execute → obs₃
...
Step 199: obs₁₉₉ → LLM → action₁₉₉ → done

Total: 200 LLM calls, 200 environment steps
```

#### VLA Pattern (Action Chunking)

VLA uses a fundamentally different approach:
```
Loop until task done:
  1. Observe environment state
  2. VLA generates 25 FUTURE actions (action chunk)
  3. Execute all 25 actions sequentially
  4. Get new observation (after all 25 executed)
  5. Repeat
```

**Characteristics**:
- Low-frequency VLA calls (one per 25 steps)
- Predictive: plans ahead for multiple steps
- Temporal reasoning: considers action sequences
- Smooth trajectories but delayed reactivity

**Example** (200 environment steps):
```
Step 0:   obs₀ → VLA → [action₀, action₁, ..., action₂₄] 
          ↓
          Execute action₀ in env
          Execute action₁ in env
          ...
          Execute action₂₄ in env
          ↓
Step 25:  obs₂₅ → VLA → [action₂₅, action₂₆, ..., action₄₉]
          ↓
          Execute action₂₅ in env
          Execute action₂₆ in env
          ...
          Execute action₄₉ in env
          ↓
Step 50:  obs₅₀ → VLA → [action₅₀, action₅₁, ..., action₇₄]
...

Total: 8 VLA calls, 200 environment steps (25 steps × 8 calls)
```

#### Detailed Execution Flow

Let's trace through a concrete example for beat_block_hammer:

**VLA Call 1** (Step 0):
```
Input:
- RGB images: head camera (224×224×3)
              left wrist camera (224×224×3)  
              right wrist camera (224×224×3)
- Proprioception: 14-dim joint positions [θ₁, θ₂, ..., θ₁₄]
- Instruction: "Grab the hammer and beat the block"

VLA Processing:
1. Vision Encoder: Extract visual features from 3 camera views
2. Text Encoder: Process instruction into embeddings
3. Proprio Encoder: Normalize joint positions
4. Fusion: Concatenate all modalities
5. LLM (Llama-7B): Autoregressively generate 350 tokens
   - 25 action chunks × 14 dimensions = 350 tokens
6. Action Decoder: Convert tokens to continuous actions

Output:
actions₀₋₂₄ = [
  [left_arm₀, right_arm₀],    # Step 0
  [left_arm₁, right_arm₁],    # Step 1
  ...
  [left_arm₂₄, right_arm₂₄]  # Step 24
]
Shape: (25, 14) = 25 timesteps × 14 dimensions

Time: ~300ms for entire VLA forward pass
```

**Environment Execution 1** (Steps 0-24):
```
for t in range(25):
    # Execute one action chunk
    env.step(actions₀₋₂₄[t])
    
    # What happens internally:
    1. Update robot joint targets with action[t]
    2. PD controller computes joint torques
    3. Physics simulation advances 1 timestep (~50ms real-time)
    4. Update object positions, check collisions
    5. Render 3 camera views (RGB images)
    6. Check success condition
    
    # Time per step: ~60ms
    
# Total execution time: 25 × 60ms = 1500ms
# GPU is IDLE during this entire period!
```

**VLA Call 2** (Step 25):
```
Input:
- NEW RGB images: Updated after 25 steps of motion
- NEW Proprioception: Current joint positions after movement
- SAME Instruction: Task hasn't changed

Output:
actions₂₅₋₄₉ = [next 25 action chunks]

Time: ~300ms
```

**Environment Execution 2** (Steps 25-49):
```
Execute all 25 actions sequentially
Time: ~1500ms
```

This continues for ~8 VLA calls until either:
- Success condition met (hammer contacts block)
- Maximum steps reached (200 steps)
- Failure detected (robot stuck, collision, timeout)

#### Visual Timeline

```
Time:      0ms         300ms      1800ms     2100ms     3600ms
           |            |           |          |           |
GPU:       [VLA Call 1] idle        [VLA Call 2] idle      [VLA Call 3]
           ↓                                    ↓
Actions:   Generate     Execute     Generate   Execute
           25 actions   25 actions  25 actions 25 actions
           
Steps:     0            0→24        25         25→49      50
           
Robot:     Stationary   Moving...   Moving...  Moving...  Moving...
```

#### Key Differences: ReAct vs VLA

| Aspect | ReAct (Single-Step) | VLA (Action Chunking) |
|--------|--------------------|-----------------------|
| **Observation Frequency** | Every step | Every 25 steps |
| **Model Calls** | 200 (for 200 steps) | 8 (for 200 steps) |
| **Planning Horizon** | 1 step (reactive) | 25 steps (predictive) |
| **Output per Call** | 1 action (14-dim) | 25 actions (25×14 matrix) |
| **Computational Cost** | 200 × 300ms = 60s | 8 × 300ms = 2.4s |
| **GPU Utilization** | ~50% (frequent calls) | ~15% (infrequent calls) |
| **Adaptability** | High (responds each step) | Lower (commits to 25 steps) |
| **Trajectory Smoothness** | Can be jerky | Naturally smooth |
| **Real-time Capability** | Challenging (200Hz calls) | Feasible (8Hz calls) |

#### Why VLA Uses Action Chunking

**1. Computational Efficiency**:
- VLA models are huge (7B parameters)
- 8 forward passes vs 200 = **25× fewer inferences**
- Critical for real-time robot control
- Enables deployment on resource-constrained robots

**2. Natural Motion**:
- Humans plan in chunks (reach → grasp → lift)
- Robot trajectories should be smooth, not jerky
- Single-step control often causes oscillations
- Action chunking produces fluid motion

**3. Training Data Structure**:
- Human demonstrations naturally contain temporal structure
- People execute sub-goals (approach, grasp, move) not individual joint movements
- VLA learns this hierarchical structure
- Action chunks capture motion primitives

**4. Temporal Consistency**:
- Generating 25 actions together enforces coherence
- Actions form smooth trajectory in joint space
- Prevents contradictory actions (e.g., open then close gripper)
- LLM's sequential generation creates temporal dependencies

**5. Reduced Accumulation Error**:
- Frequent re-planning can cause drift
- Each observation has noise
- Committing to 25 steps reduces noise amplification
- Balance between reactivity and stability

#### Limitations of Action Chunking

**Cannot React Quickly**:
- Must execute all 25 actions before sensing again
- 25 × 50ms = 1.25 seconds of "blindness"
- Cannot respond to unexpected events during chunk execution
- Example: If object moves during execution, robot won't notice until step 25

**Trade-off Decision**:
- Shorter chunks (e.g., 10): More reactive but more VLA calls
- Longer chunks (e.g., 50): Fewer VLA calls but less adaptive
- Paper uses 25 as optimal balance

**Why 25 Works**:
- Environment is relatively static (objects don't move spontaneously)
- Robot motion is fast enough to complete chunks quickly (~1.25s)
- Success rate shows this horizon is sufficient for tasks
- GPU idle time (1500ms) >> VLA inference (300ms), so bottleneck is physics anyway

#### Comparison to Other Approaches

**vs Hierarchical RL**:
- Hierarchical RL: High-level policy → sub-goal → Low-level policy → actions
- VLA action chunking: Single model generates action sequence directly
- VLA is simpler but less flexible

**vs Model Predictive Control (MPC)**:
- MPC: Optimize trajectory over horizon, execute first action, re-optimize
- VLA: Generate trajectory once, execute all actions
- MPC is more adaptive but computationally expensive

**vs Options Framework**:
- Options: Learn reusable skills (primitives) that execute for variable duration
- VLA: Fixed-length action sequences, no explicit skill decomposition
- Options are more structured but harder to learn

#### Implications for Your Training

**What to Monitor**:
- Action chunk utilization: Are all 25 steps being used?
- Early termination rate: How often do episodes end before 25 steps?
- Trajectory smoothness: Are actions forming coherent sequences?
- Success timing: At which chunk number does success typically occur?

**Expected Behavior**:
- Most episodes use 6-8 VLA calls (150-200 steps)
- Some succeed early (3-4 calls, 75-100 steps)
- Rarely use all 8 calls unless struggling
- Action sequences should show smooth progressions in joint space

**Performance Characteristics**:
- GPU busy: 300ms × 8 = 2.4s per episode
- GPU idle: 1500ms × 8 = 12s per episode  
- GPU utilization: 2.4s / 14.4s = **16.7%**
- This is expected and acceptable!

---

### Real-World Deployment: What Happens During VLA Inference?

**Key Question**: When the GPU is computing the next 25 actions (~300ms), what does the physical robot do in real-world deployment?

#### Answer: The Robot Continues Moving!

In real-world deployment, the system uses **buffered execution** to ensure continuous, smooth motion:

```
Action Buffer System:

Time:     0ms          300ms        1800ms       2100ms
          |             |             |            |
VLA:      [Inference 1] [Inference 2] [Inference 3]
          └─> Chunk 1   └─> Chunk 2   └─> Chunk 3
               (25 acts)     (25 acts)     (25 acts)

Buffer:   [a₀...a₂₄]   [a₂₅...a₄₉]  [a₅₀...a₇₄]
          ↓ executing   ↓ ready       ↓ ready

Robot:    [Executing a₀→a₂₄ continuously, no pause!]
                        [Executing a₂₅→a₄₉ continuously]
```

**How It Works**:

1. **Parallel Processing**:
   - **VLA Thread**: Continuously computes next action chunk
   - **Robot Control Thread**: Continuously executes actions from buffer
   - Both run simultaneously on different compute resources

2. **Action Buffer (Queue)**:
   - Initially empty
   - VLA generates first 25 actions → buffer fills
   - Robot starts executing from buffer at control frequency
   - While robot executes actions 0-24, VLA computes actions 25-49
   - By the time robot finishes action 24, actions 25-49 are ready
   - Seamless transition, no pause!

3. **Timing Requirements**:
   - VLA inference time: ~300ms
   - Action chunk execution time: ~1250ms (25 actions × 50ms)
   - **Critical condition**: VLA inference must complete before buffer empties
   - **Buffer safety margin**: 1250ms - 300ms = 950ms extra time
   - This ensures smooth operation with 3× safety margin

#### Control Frequencies Explained

There are **three different frequencies** in the system:

**1. Simulation Physics Frequency (250 Hz)**
- **What**: SAPIEN physics engine update rate
- **Value**: 250 Hz (timestep = 1/250 = 4ms)
- **Found in**: `_base_task.py:223` → `scene.set_timestep(1/250)`
- **Purpose**: High-fidelity physics simulation
- **Scope**: Internal to simulator
- **Note**: This is NOT the robot control frequency!

**2. Robot Control Frequency (Variable, typically 10-50 Hz)**
- **What**: Rate at which robot receives and executes new action commands
- **Typical values**:
  - ALOHA robot: ~50 Hz (20ms per action)
  - Position control: 10-20 Hz (50-100ms per action)
  - Torque control: 100-500 Hz (2-10ms per action)
- **In VLA system**: Each of the 25 action chunks is executed at this rate
- **Example**: If control freq = 50 Hz:
  - Each action chunk takes 20ms to execute
  - 25 chunks × 20ms = 500ms total execution time
  - But simulation shows ~60ms per chunk → likely using lower control rate (~16 Hz)

**3. VLA Inference Frequency (~8 Hz for 200 steps)**
- **What**: Rate at which VLA model generates new action chunks
- **Value**: ~8 Hz (125ms per inference call)
  - 200 environment steps / 25 chunks = 8 calls
  - 8 calls / (8 × 1.25s) = ~0.8 Hz actual rate
  - But ideally: 1 call per 1.25s = 0.8 Hz
- **Calculation**: 1000ms / 125ms ≈ 8 inferences per second (if continuous)
- **Purpose**: High-level action planning
- **Scope**: End-to-end system throughput

#### Real-World Execution Timeline

Let's trace what happens in real-world deployment:

**Initial Phase** (t = 0ms):
```
1. VLA thread starts computing first chunk (0-300ms)
2. Robot waits at home position (buffer empty)
3. At t=300ms: First 25 actions loaded into buffer
4. Robot immediately starts executing action₀
```

**Steady State** (t = 300ms onward):
```
Robot Control Loop (50 Hz = 20ms per cycle):
  t=300ms:  Execute action₀  | VLA computing chunk 2 in background
  t=320ms:  Execute action₁  | VLA still computing...
  t=340ms:  Execute action₂  | VLA still computing...
  ...
  t=780ms:  Execute action₂₄ | VLA finished chunk 2 at t=600ms
  t=800ms:  Execute action₂₅ | Chunk 2 ready, seamless transition!
  
  No pause! Robot maintains continuous motion.
```

**Key Insight**: 
- Action execution (500-1250ms) is **slower** than VLA inference (300ms)
- This creates natural buffering
- VLA always finishes before buffer empties
- Robot experiences **continuous, smooth motion**

#### Simulation vs Real-World Differences

**In Simulation** (SimpleVLA-RL code):
```python
# Sequential execution (rob_rollout.py)
vla_output = _generate_one_step(vla_input)  # 300ms, GPU busy
actions = vla_output["action"]  # (25, 14)

# Then execute all actions
for i in range(25):
    env.step(actions[i])  # 60ms each, GPU idle
```

**Why sequential in simulation?**
- Easier to implement and debug
- No real-time constraints in simulation
- Can run faster or slower than real-time
- GPU idle time doesn't matter (no physical robot waiting)

**In Real-World Deployment** (typical VLA systems):
```python
import threading
import queue

action_buffer = queue.Queue(maxsize=50)  # Buffer for 2 chunks

def vla_inference_thread():
    while True:
        obs = get_latest_observation()
        actions = vla_model.generate(obs)  # 300ms
        for action in actions:
            action_buffer.put(action)  # Add to buffer

def robot_control_thread():
    while True:
        action = action_buffer.get()  # Blocks if empty
        robot.execute_action(action)  # 20ms at 50 Hz
        time.sleep(0.02)  # Maintain 50 Hz control rate

# Start both threads
threading.Thread(target=vla_inference_thread).start()
threading.Thread(target=robot_control_thread).start()
```

**Benefits of Real-World Approach**:
1. **Continuous Motion**: No pauses, robot never stops
2. **Smooth Trajectories**: Maintains constant velocity
3. **Better User Experience**: Looks natural, not jerky
4. **Optimal Resource Use**: GPU and robot work in parallel
5. **Robustness**: Buffer handles inference time variations

#### Control Frequency Trade-offs

**Higher Control Frequency (50-100 Hz)**:
- ✅ Smoother motion trajectories
- ✅ Better tracking of complex paths
- ✅ Faster reaction to disturbances
- ❌ More computational overhead
- ❌ Requires faster VLA inference or larger buffer

**Lower Control Frequency (10-20 Hz)**:
- ✅ Less computational demand
- ✅ Easier to keep buffer full
- ✅ More time for VLA inference
- ❌ Choppier motion
- ❌ Reduced responsiveness

**Optimal for VLA** (20-50 Hz):
- Balances smoothness and efficiency
- Action chunk of 25 at 50 Hz = 500ms execution
- VLA has 500ms to compute next chunk (vs 300ms needed)
- 200ms safety margin handles variations

#### Practical Deployment Example

**ALOHA Robot** (typical VLA deployment platform):
```
Hardware Specs:
- Control frequency: 50 Hz (20ms per action command)
- Servo update rate: 100 Hz (10ms internal)
- Camera frame rate: 30 Hz (33ms per frame)
- Network latency: 5-20ms (WiFi/Ethernet)

VLA System:
- Inference time: 200-500ms (depends on hardware)
- Action chunk size: 25 actions
- Chunk execution time: 25 × 20ms = 500ms
- VLA frequency: ~2 Hz (500ms per chunk)

Buffer Management:
- Minimum buffer: 25 actions (500ms)
- Typical buffer: 50 actions (1000ms = 2 chunks)
- Buffer refill: When < 15 actions remain
- This ensures buffer never empties
```

**Execution Flow**:
```
t=0ms:     Camera captures frame
t=10ms:    Frame sent to VLA computer
t=15ms:    VLA starts inference
t=315ms:   VLA outputs 25 actions
t=320ms:   Actions sent to robot controller
t=325ms:   Robot starts executing action₀

t=325ms:   Robot executes action₀ (servo moves)
t=345ms:   Robot executes action₁
t=365ms:   Robot executes action₂
...
t=325ms + 500ms = 825ms: Robot finishes action₂₄

Meanwhile:
t=350ms:   Camera captures next frame (during execution)
t=365ms:   VLA starts computing next chunk
t=665ms:   VLA outputs next 25 actions
t=670ms:   Actions loaded into buffer (before robot finishes current chunk!)

t=825ms:   Robot seamlessly transitions to action₂₅
           No pause! Continuous motion!
```

#### What if VLA is Too Slow?

**Problem Scenario**: VLA inference takes 800ms, but chunk execution only 500ms
- Buffer empties before next chunk ready
- Robot must pause and wait
- Results in jerky, unnatural motion

**Solutions**:

1. **Increase Chunk Size**:
   - Use 50 actions instead of 25
   - Execution time: 1000ms
   - Allows 800ms VLA inference + 200ms margin

2. **Faster Hardware**:
   - Use better GPU (A100 → H100)
   - Reduce inference from 800ms → 300ms
   - Larger safety margin

3. **Model Optimization**:
   - Quantization (bfloat16 → int8)
   - Faster inference frameworks (TensorRT)
   - Smaller models (7B → 3B)

4. **Predictive Buffering**:
   - Start computing chunk N+2 while executing chunk N
   - Keep 2-3 chunks in buffer at all times
   - Provides larger time cushion

#### Summary: Real-World Behavior

**Question**: "Will the robot stop at a static position during VLA inference?"

**Answer**: **No!** In properly designed real-world systems:

1. Robot **continues executing** previously generated actions
2. VLA computes **in parallel** while robot moves
3. Action buffer ensures **seamless transitions**
4. Robot experiences **continuous, smooth motion**
5. No pause or static positions during normal operation

**Control Frequency**:
- **Physics simulation**: 250 Hz (4ms timestep) - only in simulation
- **Robot control**: 20-50 Hz (20-50ms per action) - real-world execution rate
- **VLA inference**: ~0.8-2 Hz (500-1250ms per chunk) - planning rate

**Critical Success Factor**:
```
VLA_inference_time < action_chunk_execution_time

300ms < (25 actions × 50ms/action) = 1250ms ✓

This ensures buffer never empties and robot maintains continuous motion.
```

The system is designed with a **4× safety margin** (1250ms / 300ms), making it robust to inference time variations, network delays, and other real-world uncertainties!

---

## Conclusion

The GPU utilization patterns you're observing are **normal and expected** for this architecture:
- ✅ **0% GPU**: Environment simulation (CPU-bound)
- ✅ **100% GPU**: VLA model inference (GPU-bound)  
- ✅ **Unbalanced**: Ray scheduling transitions

The main bottleneck is **not GPU utilization**, but rather **CPU physics simulation and environment management**.

### Key Insight from Paper

The SimpleVLA-RL paper (Section 3.3) introduces **three exploration enhancements** that are already implemented in your config:

1. **Higher Rollout Temperature (1.6)**: Directly affects the rollout process
   - Generates more diverse trajectories during rollout
   - Critical for discovering new successful strategies
   - Achieves ~15% improvement (Figure 3c)
   - **This is why you see `temperature=1.6` in the code!**

2. **Dynamic Sampling**: Filters rollout data during collection
   - Keeps only groups with mixed success/failure outcomes
   - Ensures stable gradients and meaningful learning
   - Achieves ~15% improvement (Figure 3a)

3. **Clip Higher (1.28)**: Affects PPO policy updates (not rollout)
   - Allows larger policy updates for exploration
   - Achieves ~10% improvement (Figure 3b)

**Combined effect**: These three enhancements achieve **~30% improvement** over baseline SFT in just 300 training steps (~4.3 days)!

### Terminology Clarification

There are **three different types of "steps"** in this system:

1. **Training Steps (global_steps)**: 
   - **Paper shows: 300 steps** (Figure 3 in [SimpleVLA-RL paper](https://arxiv.org/pdf/2509.09674))
   - **Config file has: 1500 steps** (`trainer.total_epochs=100`)
   - Main training loop iterations
   - One training step = collect rollouts + update policy
   - Takes ~20 minutes per training step

2. **Environment Steps**: Max 200 per rollout
   - Physical robot control actions in simulation
   - These are the actual joint movements

3. **VLA Inference Steps**: ~8 per rollout
   - Number of VLA model forward passes
   - 200 env steps ÷ 25 action_chunks = 8 VLA calls

### Actual Performance

Based on real timing data:
- **Per Training Step**: ~1220 seconds (~20 minutes)
  - Rollout: ~1070s (87.8%)
  - PPO Update: ~145s (11.8%)
  - Other: ~5s (0.4%)

- **Total Training Time**: 
  - Paper (300 steps): ~4.3 days with 8 GPUs
  - Full config (1500 steps): ~21 days with 8 GPUs

### Recommendations Priority Order

**High Priority** (proven by paper):
1. **Verify the three key enhancements are working**:
   - Monitor dynamic sampling retention (~70-80% is healthy)
   - Check entropy metrics for exploration
   - Validate temperature=1.6 is being used during rollout

2. **Monitor learning progress** (paper shows convergence at 300 steps):
   - Success rate should improve steadily
   - Policy should discover new strategies (like "pushcut" phenomenon)
   - Advantages should center around 0 (GRPO working correctly)

**Medium Priority** (system optimization):
3. Use GPU-accelerated simulators (Isaac Gym) - **10-100× speedup**
4. Optimize environment initialization
5. Improve threading/parallelism in rollout

**Low Priority** (experimental):
6. Reduce action chunk length (25 → 10-15) - may hurt performance
7. Pipeline CPU/GPU work - complex engineering effort
8. Separate resource pools - may not help much with current bottleneck

**Key Takeaway**: The paper's three enhancements already address the main algorithmic challenges. The remaining bottleneck is **CPU physics simulation speed**, which is best solved by switching to GPU-accelerated simulators, not by tuning the RL algorithm further.

