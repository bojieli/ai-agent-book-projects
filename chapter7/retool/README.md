## English

# ReTool: Enhancing LLM Mathematical Reasoning with Multi-Turn Dialogue and Code Sandbox

## Overview

ReTool is an innovative reinforcement learning method designed to significantly improve large language model performance on mathematical reasoning tasks through multi-turn dialogue and code sandbox execution. The core idea is to teach the model to use tools (particularly code execution environments) to assist in solving mathematical problems, rather than relying solely on the language model's own reasoning capabilities. Through two training stages—supervised fine-tuning (SFT) and reinforcement learning (RL)—ReTool teaches the model when and how to invoke the code sandbox to verify calculation results, test hypotheses, or explore the problem space.

This document provides a detailed record of the complete replication steps for the ReTool method, including environment configuration, model training, and evaluation. The replication is based on the verl framework, uses Qwen2.5-32B-Instruct as the base model, and is trained on the AIME 2024 mathematics competition dataset. The entire training process consists of two main phases: first, supervised fine-tuning to teach the model basic tool usage patterns, followed by reinforcement learning to further optimize the model's performance on actual problem solving.

## Hardware and Software Requirements

### Hardware Configuration

Replicating ReTool requires powerful GPU computing resources. The recommended hardware configurations include the following two options:

The first option is to use a server equipped with 8 H200 GPUs. H200 GPUs offer large memory capacity and strong computational power, enabling efficient large-scale model training. A single-server configuration simplifies the complexity of distributed training and is particularly suitable for researchers attempting replication for the first time.

The second option is to use 2 servers each with 8 A100 or H100 GPUs. This configuration provides greater total computational power but requires configuring multi-node distributed training. If choosing this option, it is recommended to use the original verl framework rather than a modified version.

### Software Environment

The following software environment combination is recommended for optimal compatibility and performance:

- **CUDA Version**: 12.6.2
- **Operating System**: Ubuntu 24.04 LTS
- **Python Version**: 3.13

These version choices are based on support for the latest deep learning frameworks and stability considerations. CUDA 12.6.2 provides optimized support for the latest GPU architectures, Ubuntu 24.04 is a long-term support release ensuring system stability, and Python 3.13 offers the latest language features and performance improvements.

## Environment Setup

### Downloading the verl Framework

verl is an efficient reinforcement learning framework specifically designed for RLHF (Reinforcement Learning from Human Feedback) training of large language models. For a single-server 8x H200 GPU configuration, a modified version is recommended:

```bash
git clone https://github.com/bojieli/verl
```

This modified version is optimized for a single 8x H200 configuration. For multi-node configurations, the original verl framework should be used:

```bash
git clone https://github.com/volcengine/verl/
```

### Installing Miniconda

Miniconda is a lightweight Python environment management tool that makes it easy to create and manage isolated Python environments, avoiding dependency conflicts. The installation steps are as follows:

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

Follow the prompts to complete the configuration during installation. After installation, it is recommended to restart the terminal to apply the environment variables.

### Creating a Conda Environment

To avoid dependency conflicts with other projects on the system, create a dedicated Conda environment for ReTool training:

```bash
conda create -n verl python==3.13
conda activate verl
```

After activating the environment, all subsequent package installations and command executions will take place within this isolated environment.

### Installing Dependencies

Navigate to the verl directory and install the required dependencies. This process includes installing base dependencies, CUDA-related dependencies, and verl itself:

```bash
cd verl
pip install -r requirements.txt
pip install -r requirements-cuda.txt
pip install -e .
```

Here, `requirements.txt` contains the base Python package dependencies, `requirements-cuda.txt` contains CUDA-related deep learning frameworks and libraries, and `pip install -e .` installs the verl framework itself in editable mode, facilitating subsequent development and debugging.

### Downloading the Base Model

ReTool uses Qwen2.5-32B-Instruct as the base model. This is an instruction-tuned large language model with strong instruction-following and reasoning capabilities. First, create the model storage directory, then download the model using the Hugging Face CLI:

```bash
mkdir -p /root/verl/recipe/retool/model/
huggingface-cli download Qwen/Qwen2.5-32B-Instruct \
    --local-dir /root/verl/recipe/retool/model/Qwen2.5-32B-Instruct \
    --local-dir-use-symlinks False
```

The `--local-dir-use-symlinks False` parameter ensures files are fully copied rather than using symbolic links, which is more stable and reliable in certain training scenarios.

### Downloading Training Data

The supervised fine-tuning phase of ReTool uses the AIME 2024 dataset. First, run the preprocessing script, then download the dataset:

```bash
python3 recipe/retool/retool_sft_preprocess.py
huggingface-cli download --repo-type dataset --resume-download \
    BytedTsinghua-SIA/AIME-2024 \
    --local-dir /dataset/BytedTsinghua-SIA/AIME_2024
```

The preprocessing script prepares the dataset format to meet the input requirements of the training framework. The `--resume-download` parameter allows resuming downloads if the network is interrupted, improving download robustness.

## Supervised Fine-Tuning (SFT)

### Starting Training

Supervised fine-tuning is the first phase of ReTool training, aimed at teaching the model basic tool usage patterns and multi-turn dialogue formats. Navigate to the recipe directory and execute the training script:

```bash
cd recipe/retool
bash run_qwen2-32b_sft.sh
```

### Configuring Wandb

At the start of training, the system will prompt you to configure Weights & Biases (wandb), a popular machine learning experiment tracking tool. First, register an account at wandb.ai, then follow the prompts:

1. Select "Use an existing W&B account" (option 2)
2. Visit https://wandb.ai/authorize to obtain an API key
3. Paste the API key into the terminal prompt

Once configured, all training metrics will be automatically uploaded to the wandb platform, allowing real-time monitoring of training progress and model performance through the web interface.

### Training Process Analysis

After training begins, the system displays detailed configuration information and training parameters. Based on the dataset size and batch settings, the training process includes 6 epochs, each with 62 steps, for a total of 372 training steps.

Key training configuration parameters include:

- **Batch Size**: Training batch size is 16, with a micro-batch size of 4 per GPU
- **Sequence Length**: Maximum sequence length is 16384, supporting long multi-turn dialogues
- **Optimizer Configuration**: Learning rate is 1e-5, using the Adam optimizer with weight decay of 0.01
- **Parallelism Strategy**: Uses Ulysses sequence parallelism with a parallelism size of 4, effectively handling long sequences
- **Model Strategy**: Uses FSDP (Fully Sharded Data Parallel) for distributed training, with gradient checkpointing enabled to save memory

During training, the loss value, learning rate, and execution time for each step are output. A typical training log looks like this:

```text
step:1 - train/loss:0.8078852891921997 - train/lr(1e-3):0.0002702702702702703 - train/time(s):14.796027898788452
step:2 - train/loss:0.7787683010101318 - train/lr(1e-3):0.0005405405405405405 - train/time(s):7.293778896331787
step:3 - train/loss:0.7899439334869385 - train/lr(1e-3):0.0008108108108108109 - train/time(s):6.083798885345459
```

It can be observed that the initial step takes longer due to various initialization operations (about 15 seconds), but subsequent steps stabilize at around 6-7 seconds per step. As training progresses, the loss value gradually decreases, indicating that the model is learning the task.

By the 3rd epoch, the loss has significantly decreased:

```text
step:127 - train/loss:0.1943996697664261 - train/lr(1e-3):0.00832235736719411 - train/time(s):6.062393665313721
step:128 - train/loss:0.1821298599243164 - train/lr(1e-3):0.008287170670328432 - train/time(s):6.20814323425293
```

The learning rate uses a cosine scheduling strategy, gradually decaying during training, which helps the model converge more stably in the later stages of training.

### Training Time Estimation

Based on actual testing, with an 8x H200 GPU configuration, each step takes approximately 7 seconds on average. Completing all 372 steps takes about 45 minutes. Actual time may vary depending on the GPU configuration.

After training completes, the terminal outputs a summary. You can click the wandb link to view detailed training information.

```text
Total time for train steps: 2627.97s
Final validation metrics: {'val/loss': 0.019425522536039352}
Epoch 6/6:  98%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████▎  | 61/62 [09:53<00:09,  9.73s/it]
wandb:
wandb: Run history:
wandb:     train/loss █▇▇▇▅▅▅▅▅▄▄▄▄▄▂▂▂▂▃▂▂▂▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁
wandb: train/lr(1e-3) ▄▅▆▆██████▇▇▇▇▆▆▆▆▆▆▄▄▄▄▃▃▃▃▃▂▂▂▂▁▁▁▁▁▁▁
wandb:  train/time(s) ▅▃▆▆▃▃▂█▁▃▆▆▁▆▄▅▂▃▄▂▅▁▄▅▄▇▄▁▂▂▂▂▄▂▃▄▄█▁▅
wandb:       val/loss ▁
wandb:
wandb: Run summary:
wandb:     train/loss 0.01913
wandb: train/lr(1e-3) 0
wandb:  train/time(s) 6.46921
wandb:       val/loss 0.01943
wandb:
wandb: 🚀 View run multiturn-sft-qwen-2.5-32b-instruct at: https://wandb.ai/bojieli-pine-ai/boj-multiturn-sft/runs/7zndjepf
wandb: ⭐️ View project at: https://wandb.ai/bojieli-pine-ai/boj-multiturn-sft
wandb: Synced 5 W&B file(s), 0 media file(s), 0 artifact file(s) and 0 other file(s)
```

After training, model checkpoints are saved in the specified directory (default: `/root/verl/recipe/retool/checkpoint/multiturn-sft-qwen-2.5-32b-instruct`) for use in the subsequent reinforcement learning phase.

### Detailed Explanation of SFT Training Recipe Parameters

Understanding the parameter configuration of the training script is crucial for adjusting the training process and optimizing performance. The SFT training script uses torchrun to launch distributed training, where the nnodes and nproc_per_node parameters specify the number of nodes and the number of processes per node, respectively. For a single 8x H200 server, these parameters are set to 1 and 8, meaning all 8 GPUs on a single node are used for training. The standalone option indicates that no master node address configuration is needed, simplifying the startup process for single-machine training.Data-related parameters determine how the model processes input. The `train_files` and `val_files` parameters specify the paths to the training and validation data, which in this case are Parquet files from the ReTool-SFT dataset. The `max_length` parameter is set to 16384, a relatively long sequence length that allows the model to handle complex interaction sequences involving multi-turn dialogues and code execution results. `train_batch_size` is set to 32, meaning 32 samples are processed per training step, while `micro_batch_size_per_gpu` is set to 4, meaning each GPU actually processes 4 samples at a time, with gradient accumulation used to achieve a larger effective batch size. This design balances training stability and efficiency under limited GPU memory.

The multi-turn dialogue configuration is a key feature of ReTool training. The `data.multiturn.enable` parameter enables multi-turn dialogue mode, while the `messages_key` and `tools_key` parameters specify the field names for dialogue messages and tool definitions in the dataset. This allows the model to learn the ability to invoke tools appropriately during a conversation. By observing the message sequences and tool call patterns in the example data, the model gradually understands when to use tools, how to construct tool call requests, and how to interpret the results returned by tools.

Model and training strategy parameters control how the model is loaded and optimized. The `partial_pretrain` parameter points to the path of the Qwen2.5-32B-Instruct base model, from which fine-tuning will start. The `strategy` parameter is set to `fsdp` (Fully Sharded Data Parallel), an advanced distributed training strategy that shards model parameters, gradients, and optimizer states across multiple GPUs, significantly reducing per-GPU memory requirements.

Sequence parallelism and optimization parameters further improve training efficiency. `ulysses_sequence_parallel_size` is set to 4, meaning the Ulysses sequence parallelism algorithm is used to split long sequences across 4 GPUs for parallel processing. This is crucial for handling sequences of length 16384, avoiding memory bottlenecks on a single GPU. The `use_remove_padding` parameter enables dynamic padding removal optimization, computing only on actual valid tokens and skipping padding tokens, which significantly improves training efficiency, especially when dealing with variable-length sequences.

Experiment management parameters help organize and track the training process. `project_name` and `experiment_name` are used to identify training tasks on the wandb platform, making it easy to review and compare results from different experiments later. `default_local_dir` specifies the local path for saving checkpoints, with model states saved periodically during training. The `logger` parameter is set to use both console and wandb logging, ensuring real-time observation of training progress while also enabling in-depth analysis through the wandb web interface. `total_epochs` is set to 6, meaning the training dataset will be traversed completely 6 times.

## Reinforcement Learning Environment: SandboxFusion

### Environment Overview

SandboxFusion is the code execution sandbox environment used in the reinforcement learning phase of ReTool. It provides a secure, isolated Python code execution environment, allowing the model to actually execute code during training and receive feedback on execution results. This interactive learning approach is key to how ReTool effectively improves the model's tool-use capabilities.

### Installation Steps

Download the modified version of SandboxFusion, which supports running 128 parallel workers locally to meet the demands of large-scale training:

```bash
git clone https://github.com/bojieli/SandboxFusion
cd SandboxFusion/
```

Create a dedicated Conda environment for SandboxFusion. Note that Python 3.12 is used here instead of 3.13 to ensure optimal compatibility with SandboxFusion's dependencies:

```bash
conda create -n sandbox python==3.12
conda activate sandbox
```

Install dependencies using Poetry. Poetry is a modern Python dependency management tool that handles complex dependency relationships more effectively:

```bash
pip install poetry
poetry install
```

Create a new conda environment for the code execution sandbox and install common scientific computing and math-related libraries.

```bash
conda create -n sandbox-runtime -y python=3.11
conda activate sandbox-runtime
pip install -r ./requirements.txt --ignore-requires-python

# for NaturalCodeBench python problem 29
python -c "import nltk; nltk.download('punkt')"

# for CIBench nltk problems
python -c "import nltk; nltk.download('stopwords')"
```

Start the SandboxFusion service (defaults to 128 parallel processes; modify the Makefile if the machine has lower specifications). This service listens for code execution requests from the training process:

```bash
make run-online
```

To ensure the service can properly execute scientific computing code, it is recommended to test it with the following command:

```bash
curl 'http://localhost:8080/run_code' \
  -H 'Content-Type: application/json' \
  --data-raw '{"code": "import sympy\n\n# Define symbolic variables\nx, y = sympy.symbols(\"x y\")\n\n# Basic algebra\nexpr = x**2 + 2*x + 1\nfactored = sympy.factor(expr)\nprint(f\"Expression: {expr}\")\nprint(f\"Factored: {factored}\")\n\n# Solve equation\nsolution = sympy.solve(x**2 - 4, x)\nprint(f\"Solution to x^2 - 4 = 0: {solution}\")\n\n# Calculus\nderivative = sympy.diff(x**3 + 2*x**2 + x, x)\nprint(f\"Derivative of x^3 + 2x^2 + x: {derivative}\")\n\n# Integration\nintegral = sympy.integrate(x**2, x)\nprint(f\"Integral of x^2: {integral}\")\n\nprint(\"\\nSympy test completed successfully!\")", "language": "python"}'
```

If the service is running correctly, it will output the following result.

```json
{"status":"Success","message":"","compile_result":null,"run_result":{"status":"Finished","execution_time":0.2835578918457031,"return_code":0,"stdout":"Expression: x**2 + 2*x + 1\nFactored: (x + 1)**2\nSolution to x^2 - 4 = 0: [-2, 2]\nDerivative of x^3 + 2x^2 + x: 3*x**2 + 4*x + 1\nIntegral of x^2: x**3/3\n\nSympy test completed successfully!\n","stderr":""},"executor_pod_name":null,"files":{}}
```

Once the service is running, the reinforcement learning training process can call SandboxFusion via its API to execute code generated by the model and feed the execution results back as reward signals to the training process.

## Reinforcement Learning Training (RL)

### Preparing the SFT Model Checkpoint

After completing supervised fine-tuning, the FSDP-format checkpoint needs to be converted to the standard Hugging Face format for use in the reinforcement learning phase. The verl framework provides a model merging tool for this conversion. The SFT training consisted of 372 steps; the last checkpoint is used for conversion:

```bash
python3 -m verl.model_merger merge \
    --backend fsdp \
    --local_dir /root/verl/recipe/retool/checkpoint/multiturn-sft-qwen-2.5-32b-instruct/global_step_372 \
    --target_dir /root/verl/recipe/retool/checkpoint/multiturn-sft-qwen-2.5-32b-instruct/global_step_372/huggingface
```

This conversion process merges the sharded model weights from distributed training into a single model file and converts them to the standard format of the Hugging Face Transformers library. The converted model will be saved in the specified `huggingface` subdirectory and can be used directly for subsequent reinforcement learning training or inference evaluation. Note that this process requires sufficient disk space to store the converted model files.

### ReTool Training Principles

Before delving into the RL training steps, it is necessary to understand the core principles of the ReTool method. According to the [ReTool paper](https://arxiv.org/pdf/2504.11536), ReTool's innovation lies in integrating tool-use capabilities into the reasoning process of large language models, enabling the model to leverage computational tools to aid problem-solving, much like a human mathematician. While traditional reasoning models (such as DeepSeek R1 and OpenAI o1) perform well on pure text reasoning tasks, they still have significant limitations in scenarios requiring precise numerical computation or symbolic manipulation. Text-based reasoning processes are prone to cumulative errors and calculation mistakes. Code interpreters, by providing a formal and executable interface, enable precise numerical verification, significantly reducing such issues.

The ReTool training pipeline consists of two key stages. In the supervised fine-tuning (SFT) stage, the model learns basic tool call patterns by studying high-quality code-augmented reasoning trajectories. The data construction process first collects mathematical reasoning data from open-source datasets (e.g., OpenThoughts). After dual verification by human experts and DeepSeek-R1, a structured prompt template is used to convert text-based reasoning processes into code-integrated reasoning data. This conversion replaces manual calculation steps in the original thought process that could benefit from code execution with corresponding code snippets and their execution results. The converted data undergoes two stages of validation—format validation and answer validation—to ensure syntactic consistency and result correctness. The SFT stage uses the `swordfaith/ReTool-SFT-multi-turn` dataset, which contains 2000 mathematical problems with detailed multi-turn dialogue solutions, each sample annotated with a `tool_call` attribute. Through this supervised learning, the model establishes a foundational cognitive framework for tool use.

The reinforcement learning stage employs the DAPO (Decoupled Clip and Dynamic Sampling Policy Optimization) algorithm, an optimization method specifically designed for large-scale, long-chain-of-thought RL scenarios. According to the [DAPO paper](https://arxiv.org/pdf/2503.14476), this algorithm achieved a score of 50 on AIME 2024 with the Qwen2.5-32B model, surpassing DeepSeek-R1-Zero-Qwen-32B's score of 47, while using only 50% of the training steps. DAPO introduces four key technical innovations on top of GRPO (Group Relative Policy Optimization), specifically addressing issues like entropy collapse, reward noise, and training instability in long-chain-of-thought RL training.

The first technique is the Clip-Higher strategy, designed to promote system diversity and prevent entropy collapse. Traditional PPO uses a symmetric clipping range (e.g., 1-ε to 1+ε), but in long-chain-of-thought scenarios, this symmetric clipping can cause the model to prematurely converge to a deterministic policy, losing exploration capability. Clip-Higher uses an asymmetric clipping interval (`clip_ratio_low=0.2`, `clip_ratio_high=0.28`), providing more room for upward policy updates, encouraging the model to explore high-reward response patterns, while strictly limiting downward updates to prevent performance degradation. This design maintains training stability while effectively preserving policy exploration, preventing entropy from collapsing prematurely to near zero.

The second technique is Dynamic Sampling, used to improve training efficiency and stability. In standard GRPO, a fixed number G of responses are generated per question for relative advantage estimation. Dynamic Sampling adjusts the number of samples per question based on the training progress and reward distribution, using more samples early in training for stable advantage estimation and reducing samples later when the policy stabilizes to improve efficiency. The third technique is the Token-Level Policy Gradient Loss, which is crucial in long-chain-of-thought scenarios. Traditional methods use a single reward signal for the entire sequence, while DAPO normalizes the loss function at the token level, ensuring fair gradient weights for both long and short sequences and preventing overly long sequences from dominating the training process. The fourth technique is Overlong Reward Shaping, which reduces reward noise by applying a mild length penalty to overly long responses. This mechanism does not impose a hard length limit but introduces a gentle negative feedback in the reward function, guiding the model to generate more concise and efficient responses while maintaining reasoning quality.The core innovation of ReTool lies in its rollout mechanism that supports interleaved real-time code execution. During generation, the policy model collaborates with a code sandbox to dynamically produce mixed content—including textual reasoning, code snippets, and real-time interpreter feedback. Specifically, the model uses special tags (`<code></code>`) to mark the boundaries of generated code. When a code termination trigger (`</code>`) is detected, generation pauses, and the parsed code is sent to the sandbox for execution. The sandbox's output (successful results or error messages) is wrapped in `<interpreter></interpreter>` tags and fed back to the model, which then continues generating its reasoning trajectory, ultimately producing a mixed reasoning sequence of the form `[text₁ ⊕ code₁ ⊕ feedback₁ ⊕ ... ⊕ answer]`.

The reward design adopts a minimalist, rule-driven approach. ReTool uses a rule-based accuracy reward: +1 when the predicted answer is equivalent to the ground truth, and -1 otherwise. This simplified reward design aims to mitigate reward hacking and encourage more diverse problem-solving behaviors based solely on outcome feedback. The paper explicitly states that code executability rewards are not considered; instead, the model autonomously learns when and how to invoke tools through outcome feedback. The key design philosophy is the belief that, given sufficient exploration, the model can independently discover optimal tool-use patterns without requiring manually predefined rules for tool usage.

Experimental results thoroughly validate the effectiveness of the ReTool method. On the AIME 2024 dataset, the ReTool model based on Qwen2.5-32B-Instruct achieved 67.0% accuracy in just 400 training steps, while the text RL baseline only reached 40.0% accuracy even after 1080 training steps. This significant gap demonstrates that explicitly modeling tool use as part of the decision-making process not only pushes the boundaries of model reasoning capabilities but also greatly improves training efficiency. In the scaled setting, ReTool-32B achieved 72.5% accuracy, surpassing OpenAI's o1-preview model by 27.9 percentage points.

Another important feature of the ReTool method is its multi-turn interaction mechanism and emergent behaviors. Unlike traditional single-shot generation, ReTool allows the model to engage in multiple rounds of thinking and tool invocation. The model can first propose a hypothesis, then verify its correctness through code, adjust its reasoning direction based on the verification results, and proceed to the next round of exploration. Notably, the model exhibits an emergent ability for code self-correction during RL training. When generated code fails due to errors such as undefined functions, the model can identify the error and autonomously generate corrected, executable code. The emergence of this meta-cognitive ability marks an "aha moment," indicating that the model has mastered adaptive tool use.

Behavioral evolution analysis during training reveals several key trends. First, response length decreased by approximately 40% after RL training (from 10k tokens to 6k tokens), indicating that code-driven reasoning significantly improves the efficiency of reasoning token utilization by replacing complex computational processes with concise code. Second, the code ratio, number of code lines, and number of correct code snippets all increased steadily during training, and the timing of code invocation gradually shifted earlier. These trends collectively suggest continuous development in the model's code usage ability and strategic tool invocation. Furthermore, code purpose analysis shows that after RL training, the model's code purposes became more diverse, expanding from primarily computation and verification to a wider range of problem types, demonstrating meta-cognitive development in adaptive tool selection.

### Preparing RL Training Data

The core training dataset for the reinforcement learning phase is the BytedTsinghua-SIA/DAPO-Math-17k dataset. This is a large-scale collection of mathematical problems, containing 1.79 million math problems and their answers, covering a wide range of topics from basic arithmetic to advanced mathematics. The scale of the dataset ensures that the model can learn and generalize tool-use strategies across diverse problem scenarios. Download this dataset:

```bash
huggingface-cli download --repo-type dataset --resume-download \
    BytedTsinghua-SIA/DAPO-Math-17k \
    --local-dir /dataset/BytedTsinghua-SIA/DAPO-Math-17k
```

The evaluation dataset uses BytedTsinghua-SIA/AIME-2024, which is the 2024 problem set from the American Invitational Mathematics Examination (AIME), containing 30 high-difficulty math competition problems. AIME is one of the most challenging high school math competitions in the United States, requiring deep reasoning and creative problem-solving skills. This dataset should have already been downloaded during the SFT phase and is located in the `/dataset/BytedTsinghua-SIA/AIME_2024` directory. If a re-download is needed:

```bash
huggingface-cli download --repo-type dataset --resume-download \
    BytedTsinghua-SIA/AIME-2024 \
    --local-dir /dataset/BytedTsinghua-SIA/AIME_2024
```

It is worth noting that the RL training dataset is significantly larger than that of the SFT phase. This design is intentional: the SFT phase establishes foundational capabilities using a small number of high-quality examples, while the RL phase enhances the model's generalization ability and policy optimization through large-scale exploratory learning. The 1.79 million problems in DAPO-Math-17k provide ample exploration space for the model, enabling it to discover effective tool-use patterns across various mathematical problem scenarios.

### Starting Reinforcement Learning Training

With the SandboxFusion service running, you can start reinforcement learning training. First, ensure you have switched back to the `verl` conda environment, then enter the recipe directory and execute the RL training script:

```bash
conda activate verl
bash recipe/retool/run_qwen2-32b_dapo.sh
```

Reinforcement learning training uses the DAPO (Direct Alignment from Preferences Optimization) method, an efficient preference optimization algorithm. During training, the model generates multiple candidate answers and verifies their correctness through interaction with the code sandbox. Correct answers receive positive rewards, while incorrect answers receive negative rewards. Through this reward mechanism, the model gradually learns to generate more accurate reasoning processes and more effective tool-use strategies.

The training time for the reinforcement learning phase is typically longer than that of the SFT phase, as each training step involves multiple stages: model inference, code execution, and reward calculation. The training process is also logged to the wandb platform, allowing real-time monitoring of key metrics such as reward values and success rates. As training progresses, you should observe a gradual increase in the model's accuracy on math problem solving, along with continuous optimization of tool-use efficiency.

### Training Monitoring and Evaluation

During reinforcement learning training, several key metrics require close attention to evaluate training effectiveness. The first is the average reward value, which reflects the overall quality of the model's generated answers. As training proceeds, the average reward should show an upward trend. The second is the problem-solving success rate, i.e., the proportion of problems the model answers correctly. This metric directly reflects the model's actual capability improvement. Additionally, tool invocation frequency and tool-use success rate should be monitored, as these metrics reveal whether the model has learned to effectively use the code sandbox to assist reasoning.

Through the wandb interface, you can visualize the change curves of these metrics and compare them with the SFT phase baseline. If training stagnation or performance degradation is observed, adjustments to the learning rate, reward function weights, or other hyperparameters may be necessary. Regularly evaluating model performance on a validation set helps to promptly detect issues like overfitting and take appropriate corrective measures.

### RL Training Process Example

During RL training, you can observe the real-time interaction between the model and the SandboxFusion code sandbox. The training logs clearly show the complete cycle of the model generating code, the sandbox executing it, and returning results. Below is a typical log output from the SandboxFusion service during training:

````text
2025-10-01 08:10:56 [debug] start processing python request with code ```
import math

x_approx = (4 * math.sqrt(3) - 2) / 5
print(f"Approximate x: {x_approx}")
``` and files []...(memory_limit: 1024MB) [sandbox.server.sandbox_api]
2025-10-01 08:10:56 [debug] running command python /tmp/tmppzrv67yh/tmp1y8y74j1.py [sandbox.runners.base]
2025-10-01 08:10:56 [debug] stop running command python /tmp/tmppzrv67yh/tmp1y8y74j1.py [sandbox.runners.base]

2025-10-01 08:10:57 [debug] start processing python request with code ```
from itertools import product

# Define all edges with indices (0-11)
edges = {
    'T1': 0, 'T2': 1
``` and files []...(memory_limit: 1024MB) [sandbox.server.sandbox_api]
2025-10-01 08:10:57 [debug] running command python /tmp/tmpy_ac6y5a/tmpxn02qp2v.py [sandbox.runners.base]
2025-10-01 08:10:57 [debug] stop running command python /tmp/tmpy_ac6y5a/tmpxn02qp2v.py [sandbox.runners.base]

2025-10-01 08:11:04 [debug] start processing python request with code ```
def is_greedy_successful(N):
    # Calculate the greedy result
    q = N // 25
    r = N % 25
    gr
``` and files []...(memory_limit: 1024MB) [sandbox.server.sandbox_api]
2025-10-01 08:11:04 [debug] running command python /tmp/tmpyqtl99_8/tmph_t_tj6u.py [sandbox.runners.base]
2025-10-01 08:11:04 [debug] stop running command python /tmp/tmpyqtl99_8/tmph_t_tj6u.py [sandbox.runners.base]

2025-10-01 08:11:07 [debug] start processing python request with code ```
import math

z_numerator = 9 * math.sqrt(5) - 1
z = z_numerator / 4
print(f"z = {z}")
``` and files []...(memory_limit: 1024MB) [sandbox.server.sandbox_api]
2025-10-01 08:11:07 [debug] running command python /tmp/tmpbk3a7frj/tmp12g7qyuf.py [sandbox.runners.base]
2025-10-01 08:11:07 [debug] stop running command python /tmp/tmpbk3a7frj/tmp12g7qyuf.py [sandbox.runners.base]
````

These logs illustrate several important characteristics of RL training. First, the model generates diverse code snippets when handling different types of math problems, ranging from simple numerical calculations (using the `math` module) to complex algorithm implementations (using standard libraries like `itertools`). Second, each code request is executed in an isolated temporary directory, ensuring the security and independence of the execution environment. The sandbox creates unique temporary files for each execution (e.g., `tmp1y8y74j1.py`) and cleans them up immediately after execution, preventing state contamination.

From the timestamps in the logs, it is evident that code execution is very fast, with most simple calculations completing in milliseconds. This efficient execution mechanism allows the model to make numerous tool invocation attempts during training, rapidly accumulating experience. The logs also show that the model generates multiple candidate solutions for the same problem (evidenced by multiple code requests with close timestamps), which is characteristic of the DAPO algorithm's GRPO framework—estimating relative advantages by generating and comparing multiple responses.

Notably, each code request has a memory limit set (memory_limit: 1024MB), which is one of the sandbox environment's security mechanisms to prevent malicious or inefficient code from consuming excessive system resources. This resource constraint ensures the stability of the training process; even if the model generates problematic code, it will not affect the operation of the entire training system.

### Training Start and Initial Verification

When RL training starts, the system outputs detailed initialization and verification information. First, the AgentLoopWorker initialization log shows the configuration of the code interpreter tool:

````text
(AgentLoopWorker pid=235550) Performing class-level ToolAgentLoop initialization [repeated 7x across cluster]
(AgentLoopWorker pid=235550) {
(AgentLoopWorker pid=235550)   "type": "function",
(AgentLoopWorker pid=235550)   "function": {
(AgentLoopWorker pid=235550)     "name": "code_interpreter",
(AgentLoopWorker pid=235550)     "description": "A tool for executing code.",
(AgentLoopWorker pid=235550)     "parameters": {```
(AgentLoopWorker pid=235550)       "type": "object",
(AgentLoopWorker pid=235550)       "properties": {
(AgentLoopWorker pid=235550)         "code": {
(AgentLoopWorker pid=235550)           "type": "string",
(AgentLoopWorker pid=235550)           "description": "The code to execute."
(AgentLoopWorker pid=235550)         }
(AgentLoopWorker pid=235550)       },
(AgentLoopWorker pid=235550)       "required": ["code"]
(AgentLoopWorker pid=235550)     }
(AgentLoopWorker pid=235550)   }
(AgentLoopWorker pid=235550) }
(AgentLoopWorker pid=235550) Initialized tools: {'code_interpreter': <recipe.retool.retool.CustomSandboxFusionTool object at 0x7b4207c44c20>}
````

These logs indicate that the system is initializing 8 AgentLoopWorkers (corresponding to 8 GPUs), each configured with the same code interpreter tool. The tool definition uses a standard function-calling format, including the tool name, description, and parameter specification. "repeated 7x across cluster" indicates that this initialization process is repeated across the 7 worker processes other than the main process, ensuring configuration consistency across all processes in distributed training.

Next is the initial validation phase (val_before_train), which is a baseline performance evaluation before RL training. The system generates multiple responses (30) on the AIME 2025 validation set and calculates various statistical metrics:

```text
(TaskRunner pid=221183) Initial validation metrics:
  'val-core/aime_2025/acc/mean@30': 0.1856 (average accuracy 18.56%)
  'val-core/aime_2025/acc/best@30/mean': 0.6362 (best answer accuracy 63.62%)
  'val-core/aime_2025/acc/maj@30/mean': 0.2778 (majority voting accuracy 27.78%)
  'val-aux/num_turns/min': 2 (minimum interaction turns)
  'val-aux/num_turns/max': 16 (maximum interaction turns)
  'val-aux/num_turns/mean': 6.59 (average interaction turns)
```

These metrics reveal several important characteristics of the model before training. mean@30 represents the average accuracy after generating 30 responses for each question, with a baseline of 18.56%. best@30 indicates the accuracy of selecting the best answer among these 30 responses, reaching 63.62%, suggesting the model is capable of generating correct answers but lacks consistency. maj@30 shows the accuracy of selecting an answer through majority voting is 27.78%, higher than the average but lower than the best value, indicating that diverse sampling can improve results to some extent.

Reward statistics are equally important. The average reward on the validation set is -0.464. This is because the reward design assigns +1 for correct answers and -1 for incorrect answers; the negative value indicates a high initial error rate for the model. Metrics like best@2, best@4, and best@8 represent the average reward for selecting the best answer among 2, 4, and 8 responses, respectively. These values increase as the number of candidates grows (from -0.263 to 0.290), validating the positive impact of sampling diversity on performance. The worst metric shows the performance of the worst answer, consistently negative and decreasing as the number of candidates increases, which is expected behavior.

The num_turns statistics reveal the model's interaction patterns. The average number of interaction turns is 6.59, ranging from 2 to 16, indicating that the model adopts different strategies for different problems. Simple problems may require only a few interactions, while complex problems need multiple rounds of iteration. This baseline data provides a reference point for observing the evolution of tool usage patterns during subsequent training.

The training progress bar shows that a complete traversal of the dataset requires 3499 training steps (based on the DAPO-Math-17k dataset size of 1.79 million problems / batch size 512 × 1 epoch). However, according to the experimental results in the paper, a significant advantage of the ReTool method is its high training efficiency; in practice, only about 400 training steps are needed to achieve excellent performance. This means the model can fully learn tool usage strategies using only about 11% of the dataset, significantly shortening the training cycle. As training progresses, the trends of these metrics can be monitored in real-time through the wandb interface, observing the trajectory of model performance improvement.

### RL Training Loop Mechanism

After the initial validation, the system enters the formal RL training loop. ReTool adopts a PPO-based training process, where each training step includes three core phases: Sampling (Rollout), Reward Computation, and Policy Update. This loop repeats throughout the entire training process.

**Rollout Phase (Sampling and Inference)** is the most time-consuming part of the training loop. The current policy model draws a batch of math problems from the training set (32 problems per iteration) and generates multiple candidate solutions for each problem. According to the configuration parameter n_resp_per_prompt=16, the system generates 16 different responses for each problem, totaling 512 responses. These responses are generated using a sampling strategy (temperature=1.0), ensuring sufficient diversity to support the relative advantage estimation of the DAPO algorithm.

During generation, the system uses the vllm inference engine, configured with infer_tp=4 for tensor parallelism, splitting the model across 4 GPUs for efficient inference. Crucially, the model interacts in real-time with the SandboxFusion code sandbox. When the model generates a code snippet and marks it with `<code></code>` tags, vllm pauses generation, sends the code to the sandbox for execution. The sandbox uses an asynchronous architecture, maintaining a pool of 128 workers that independently handle code execution tasks. After execution, the result (or error message) is wrapped in `<interpreter></interpreter>` tags and returned to the model. The model continues generation after receiving feedback, adjusting its reasoning direction or attempting to correct the code based on the execution result. This interaction can repeat multiple times until the model provides a final answer. Each response is a complete reasoning trajectory, containing interwoven text reasoning, code snippets, and interpreter outputs. Due to the waiting for code execution and multiple rounds of interaction, the Rollout phase typically dominates the time of each iteration.

Tool call decoding errors may occur during training, which is normal:

```text
(AgentLoopWorker pid=235547) ERROR:2025-10-01 08:14:21,179:Failed to decode tool call: Invalid \escape: line 2 column 135 (char 135)
(AgentLoopWorker pid=235547) ERROR:2025-10-01 08:14:28,934:Failed to decode tool call: Extra data: line 2 column 228 (char 228)
(AgentLoopWorker pid=235548) ERROR:2025-10-01 08:15:37,582:Failed to decode tool call: Invalid \escape: line 2 column 480 (char 480)
```

These errors indicate that during the exploration phase, the model generated tool call code that was not entirely correct in format, such as containing unescaped backslashes, extra data, or missing delimiters. This is a manifestation of the reinforcement learning exploration process—the model needs to try various possible ways of generating code, including some attempts that will fail, and then learn which are effective through reward signals. As training progresses, the frequency of such errors will gradually decrease as the model learns to generate correctly formatted tool calls.

**Reward Computation Phase** is a relatively fast CPU-intensive process. The system collects all 512 responses generated in the Rollout phase and extracts the final answer from each response (usually contained within `<answer></answer>` or `\boxed{}` tags). The answer extractor handles various format variants to ensure reliable identification of the numerical, expression, or symbolic answer given by the model. The extracted answer is then compared to the ground truth answer using equivalence checking rather than simple string matching; for example, the mathematical expressions "1/2" and "0.5" would be judged as equivalent. Correct answers receive a reward of +1, and incorrect answers receive a reward of -1.

This simple binary reward design is an important feature of the ReTool method. Unlike some methods that attempt to give additional rewards for code executability, intermediate step correctness, etc., ReTool focuses only on the final result, allowing the model to learn entirely based on outcome feedback. This design avoids potential biases introduced by complex heuristic rules, giving the model greater freedom for exploration. For the 16 responses to each problem, the system calculates 16 corresponding reward values. These reward values are used in the DAPO algorithm to estimate relative advantage—how the quality of each response compares to other responses for the same problem. The reward differences among multiple responses to the same problem directly reflect the relative merits of different strategies, providing clear learning signals for policy gradients. DAPO's Token-Level Policy Gradient Loss ensures that these reward signals are fairly distributed across responses of different lengths, preventing overly long responses from dominating the training process.

**Policy Update Phase** is the core of the PPO algorithm and the only phase requiring backpropagation. The system treats a train_batch_size of 512 samples (from 32 problems × 16 responses) as one complete training batch. To accommodate GPU memory constraints and improve training stability, this large batch is further divided into several ppo_mini_batch_size=64 mini-batches, which undergo gradient descent sequentially. Specifically, the 512 samples are divided into 8 mini-batches, each containing 64 samples.

For each mini-batch, the training process proceeds as follows: First, the policy model performs a forward pass on these 64 responses, calculating the log probabilities of generating these responses under the current policy. Then, the policy ratio is calculated, which is the probability ratio of generating the response under the current policy compared to the old policy (the policy when these responses were generated). Next, the loss is calculated using the advantage function estimated by the DAPO algorithm and the modified clipping objective function. The clipping mechanism implements asymmetric clipping with clip_ratio_low=0.2 and clip_ratio_high=0.28, which is the core of DAPO's Clip-Higher strategy—providing 28% space for upward updates and only 20% space for downward updates, ensuring the new policy explores high-reward patterns without performance degradation. The Token-Level Policy Gradient Loss comes into play at this stage, normalizing the loss function by response length to ensure fair gradient weighting for both long and short sequences. Finally, backpropagation and parameter updates are performed.

Due to the use of FSDP and CPU offload, this phase involves complex memory management. Model parameters and optimizer states are frequently transferred between CPU and GPU. At the start of training for each mini-batch, relevant parameters are loaded from CPU to GPU; after computation, the updated parameters and gradient information are transferred back to CPU. After all 8 mini-batches are processed, one complete policy update is completed. DAPO inherits GRPO's advantage of not requiring a separate value network to be trained, estimating the advantage function through the relative quality of responses within the same batch, which greatly simplifies the training process and reduces memory requirements. Building on this, DAPO's four technical innovations further enhance training efficiency and stability, enabling it to surpass the performance of traditional methods within 50% of the training steps.

This sampling-reward-update loop continues throughout the training process. After each training step, the policy model's parameters are updated once, resulting in a slight improvement in generation capability. Then, the next loop begins, using the updated policy to resample, obtain new responses and rewards, and update the policy again. It is through this iterative optimization that the model gradually learns complex skills such as when to call tools, how to write effective code, and how to use execution results to aid reasoning.

According to the configuration, a validation is performed every 5 training steps (test_freq=5) to evaluate the current policy's performance on the validation set. Model checkpoints are saved every 30 steps (save_freq=30) for subsequent recovery or analysis. According to the experimental results in the paper, training for about 400 such loops achieves a 67% accuracy on AIME 2024, significantly surpassing the baseline model using only text reasoning (40%). This high training efficiency makes the ReTool method highly feasible in practical applications.

As training progresses, several important evolutionary trends can be observed. The frequency of code usage gradually increases, with the model learning to proactively call tools on more problems. The complexity of the code increases, expanding from simple calculations to complex algorithm implementations. The timing of tool calls advances, with the model learning to introduce code earlier to avoid cumulative errors. Most notably, emergent behaviors appear—the model begins to exhibit code self-correction capabilities, learning from execution errors and generating corrected versions. This meta-cognitive ability signifies that the model has mastered a truly adaptive tool usage strategy.

### Rollout Time Estimation Method

Understanding the time composition of the Rollout phase is crucial for reasonably planning the training cycle. Although the SandboxFusion code sandbox can process code execution requests at high speed (processing several requests per second), the total time for the entire Rollout phase is far more than just code execution itself.**Actual Workload Calculation** involves the product of multiple dimensions. According to the configuration parameters, each training step requires generating `train_batch_size=512` complete responses. This actually involves generating 16 different candidate answers from 32 math problems (512 / n_resp_per_prompt = 512 / 16 = 32). Each response is not generated in one shot but is a reasoning trajectory built step-by-step through multiple rounds of interaction. From the actual training data, it can be seen that each response contains an average of approximately 7.82 rounds of interaction (num_turns/mean). Each round of interaction typically includes one text reasoning generation, the generation and execution of a code snippet, and processing of the interpreter's feedback. Therefore, the number of code executions required to complete a full Rollout is: 512 responses × 7.82 rounds/response ≈ 4000 code executions. This number far exceeds the surface-level 512 responses, explaining why even though SandboxFusion can process multiple requests per second, the entire Rollout phase still takes a long time.

**Token Generation Volume and Actual Performance** can be accurately obtained from the training logs. Based on the statistics from the first training step, the average length of the 512 responses is 2707 tokens, ranging from a minimum of 288 tokens to a maximum of 16384 tokens. Approximately 0.85% of responses (4-5 responses) reached the maximum length limit and were truncated. The total number of tokens processed in the entire training step is 24,892,834 tokens, which includes Rollout generation, Reference Model log probability calculation, and forward and backward propagation during the Actor update. The overall system throughput is 641 tokens/second, significantly lower than in pure text generation scenarios. This is the combined result of factors such as multi-round interaction, code execution waiting, and CPU offload.

**Actual Time Consumption of Each Training Phase** reveals the allocation pattern of computational resources. From the statistics of the first training step, the Rollout generation phase takes 2529 seconds (42 minutes). This is the most time-consuming phase in the training loop, during which the vllm engine needs to generate 512 responses and interact with SandboxFusion for approximately 4000 code executions. The Reference Model's log probability calculation takes 525 seconds (8.7 minutes). This phase performs forward propagation on the 512 generated responses to obtain probability values under the old policy, which is much faster than the Rollout phase. The policy update phase takes 1795 seconds (30 minutes). In this phase, the 512 samples are divided into 8 mini-batches for sequential gradient descent. Due to the enabling of FSDP and CPU offload, a significant amount of time is spent on CPU-GPU parameter transfers, making it the second largest time overhead after Rollout. The total time for the entire training step is 4853 seconds (approximately 81 minutes). This time **does not include** the initial validation phase, which is completed independently before the formal training begins.

**Batch Processing Efficiency Degradation** is an inherent challenge in multi-round interaction scenarios. Although vllm is configured with asynchronous mode (mode=async), in actual operation, the progress of the 512 requests is not synchronized. Initially, vllm may process requests in a near-full batch state. However, as some requests encounter code execution triggers and pause to wait, the actual concurrent batch size gradually decreases. While some requests are waiting for sandbox results, other requests continue generating; when paused requests receive feedback and rejoin the batch, new requests encounter code triggers and pause. This dynamic batch size fluctuation causes the actual average batch size to be much smaller than the theoretical 512, thereby reducing overall throughput.

**Estimating Progress via SandboxFusion Logs** is a practical monitoring method. By counting the number of log entries, the number of completed responses can be roughly estimated. Based on actual statistics, each response has approximately 8 code calls (num_turns/mean: 7.82), so the number of completed responses ≈ number of code execution requests / 8. Progress percentage = number of completed responses / 512 × 100%.

**Actual Performance of the First Training Step** provides a valuable performance baseline. According to actual runtime data, the complete first training step took 4853 seconds (approximately 81 minutes), processing a total of 24,892,834 tokens, with an overall throughput of 641 tokens/second. The average reward during training increased from -0.464 in the initial validation to 0.058, indicating that the model began to show learning effects after a single training step. Response length statistics show an average response of 2707 tokens, a minimum of 288 tokens, and a maximum reaching the upper limit of 16384 tokens. Approximately 0.85% of responses (4-5) reached the maximum length limit and were truncated. The average length of input prompts is 332 tokens, with a maximum of 787 tokens, indicating that the description of math problems is relatively concise, while the model's reasoning process is quite detailed.

**Resource Utilization and Performance Metrics** reflect the efficiency level of the training system. In terms of GPU memory, the peak memory allocation for a single training step reached 214.8 GB, with memory reserved at 226.8 GB, approaching the total memory capacity of 8 H200 GPUs. CPU memory usage reached 213.0 GB, a result of offloading a large number of model parameters and optimizer states to CPU memory after enabling CPU offload. The Model FLOPs Utilization (MFU) is 39.7%. Although this value is lower than the theoretical peak for pure computation scenarios, it is a reasonable utilization level considering the waiting time for multi-round interaction, CPU-GPU data transfer, and scheduling overhead of asynchronous rollout. The slowest single response generation took 2492 seconds (41.5 minutes). This response reached the maximum length of 16384 tokens, and its generation time almost determines the total duration of the entire Rollout phase, exemplifying the classic "bucket effect".

**Stability and Learning Curve of Subsequent Training Steps** can be verified from the data of step 2. The total time for the second training step is 4859 seconds (81 minutes), almost identical to the first step, indicating that the training process has entered a stable state and initialization overhead is not the main bottleneck. The time distribution for each phase remains highly consistent: Rollout generation 2543 seconds (42.4 minutes), log probability calculation 510 seconds (8.5 minutes), policy update 1801 seconds (30 minutes). However, in terms of training effectiveness, the model shows rapid learning progress. The average reward jumped significantly from 0.058 in step 1 to 0.164 in step 2, an increase of 182%, with the corresponding accuracy improving from approximately 53% to 58%. This significant performance improvement validates the effectiveness of the ReTool method—the model is quickly learning when and how to use code tools to enhance mathematical reasoning capabilities.

Notably, response patterns have diverged. The shortest response decreased from 288 tokens to 60 tokens, indicating that the model has learned to adopt more direct solutions for simple problems; while the longest response still reaches the 16384 token limit, and the proportion of truncated responses increased from 0.85% to 0.94%, suggesting deeper exploration of complex problems. The average number of interaction rounds decreased slightly (from 7.82 to 7.79), but combined with the reward improvement, this reflects an improvement in tool usage efficiency rather than a reduction in exploration depth. The overall system throughput increased from 641 tokens/s to 650 tokens/s. Although the improvement is modest, it indicates continuous optimization of the training process. CPU memory usage increased from 213 GB to 227 GB. This growth trend needs continuous monitoring to prevent memory overflow after prolonged training.

**Actual Observations from the First Ten Training Steps** reveal the dynamic characteristics and performance evolution trends of the training process. The time consumption for steps one and two is highly consistent, at 4853 seconds and 4859 seconds (both 81 minutes), respectively, indicating that the training process has entered a stable state from the initial phase. However, starting from step three, a significant increase in time consumption is observed. This trend continues until step nine, with total time increasing from 81 minutes to 136 minutes, an increase of 68%. The total time for step ten is 128 minutes (including 19.4 minutes for validation), with pure training time being 109 minutes. Although slightly lower than step nine, it is still significantly higher than the initial level.

The main driver of this time increase is the continuous growth in response length. The average response length increased from 2707 tokens in step one to 4330 tokens in step nine, a cumulative increase of 60%. Step ten saw the first decrease in response length, dropping to 4116 tokens, a decrease of 5%, which may signal that the growth trend in response length is beginning to stabilize. The proportion of truncated responses also experienced a significant increase, from 0.85% (4-5 responses) in step one to 3.70% (19 responses) in step nine, before slightly decreasing to 2.93% (15 responses) in step ten. The generation time for these ultra-long responses reaching the 16384 token limit increased from 41.5 minutes in step one to 76.2 minutes in step nine, before falling back to 70.8 minutes in step ten, consistently dominating the total time of the entire Rollout phase.

Step five is the first step to include validation, with a total time of 6069 seconds (101.2 minutes), of which the validation phase alone took 913 seconds (15.2 minutes). The validation phase requires generating 30 responses for each of 30 problems (n_resp_per_prompt_val=30), totaling 900 responses. Interestingly, the average number of interaction rounds in the validation phase is 6.98, significantly lower than the 7.84 in the training phase. This may be related to the different sampling parameters used during validation (top_p=0.6, temperature=1.0). Excluding the validation time, the pure training time for step five is 5156 seconds (86 minutes), still higher than the 81 minutes of the first two steps, but lower than the 94 minutes of step four, showing some volatility.

**Model Learning Progress** shows a fluctuating upward trajectory over the first ten steps. The average reward on the training set increased from 0.058 in step one to 0.251 in step ten, with corresponding accuracy improving from approximately 53% to 63%, a cumulative increase of 10 percentage points. The learning curve exhibits non-monotonic characteristics: a significant increase from step one to two (+5 percentage points), slower growth from step two to five, a local peak in step six (0.251, 63%), a decline in step seven (0.206, 60%), followed by another climb in step eight (0.264, 63%), and then stabilization around 0.25 in steps nine and ten. This fluctuation is a normal phenomenon in reinforcement learning training, reflecting the dynamic balance between exploration and optimization of the policy.

The evolution of validation set performance provides key insights into the model's generalization ability. Validation results from step five show an average accuracy (mean@30) of 27.9%, a Best-of-30 metric of 62.9%, and a majority voting accuracy (maj@30) of 36.9%. By step ten, the average accuracy slightly increased to 28.3%, but the Best-of-30 metric significantly improved to 67.4%, an increase of 4.5 percentage points, indicating that the model's peak capability is continuously strengthening. However, the majority voting accuracy decreased to 33.8%, a drop of 3.1 percentage points. This divergence suggests that while the model can generate higher quality answers, its consistency has decreased. The average number of interaction rounds in the validation phase decreased from 6.98 in step five to 5.85 in step ten, a reduction of 16%, showing a similar trend to the evolution of interaction patterns in the training phase (fewer rounds but more complex per round). There is a significant performance gap between the training set and the validation set. The training set accuracy reaches 63%, while the validation set average accuracy is only 28%, but the Best-of-30 reaches 67.4%, indicating that the model has the ability to generate correct answers, with the main challenge being to improve the consistency and reliability of generation.

**Evolution of Response Generation Patterns** shows a trend of initial growth followed by stabilization over the first ten steps. The average response length increased continuously from 2707 tokens in step one to 4330 tokens in step nine, a cumulative increase of 60%, before falling back to 4116 tokens in step ten for the first time. The average number of interaction rounds shows an opposite trend, gradually decreasing from 7.82 rounds in step one to 7.10 rounds in step ten, a decrease of 9%. However, the content generated per round of interaction increased significantly, from an average of 346 tokens per round to 580 tokens in step ten, an increase of 68%. This pattern shift indicates that the model is learning to generate more complex and detailed single-round reasoning, rather than simply increasing the number of interaction rounds. The generation time for the slowest single response increased from 41.5 minutes in step one to 76.2 minutes in step nine, before falling back to 70.8 minutes in step ten. The generation time of these ultra-long responses almost completely determines the total time of the entire Rollout phase, with the bucket effect persisting throughout the training process. The total number of tokens processed in the entire training step increased from 24.9M in step one to 36.5M in step ten, an increase of 47%. This growth stems from both the increase in response length and the cumulative effect of multiple forward propagations in the training process.

**System Resource Utilization** shows good stability over the first ten steps. GPU memory usage gradually increased from 214.8 GB in step one to 216.1 GB in step ten, an increase of less than 1 GB, always remaining within the safe range of the total capacity of 8 H200 GPUs. CPU memory usage fluctuated within the range of 220-228 GB after reaching 227 GB in step two, and was 221.8 GB in step ten, with no risk of memory overflow due to continuous growth. The Model FLOPs Utilization (MFU) fluctuated slightly between 39.7% and 40.3%, maintaining a stable level. Although this utilization is lower than the theoretical peak for pure computation scenarios, considering overheads such as multi-round interaction waiting, CPU-GPU data transfer, and asynchronous scheduling, it reflects the actual performance under the current configuration. Overall throughput continuously decreased from the peak of 650 tokens/s in step two to 595 tokens/s in step ten, a decrease of 8.5%. This decline is directly related to the increase in response length and the additional overhead of processing longer sequences.

**Internal Training Technical Metrics** demonstrate the stable operation and design advantages of the DAPO algorithm. The policy gradient loss (actor/pg_loss) fluctuates within a small range between -0.0022 and +0.0011 over the first ten steps, with very small absolute values and stability, indicating that the policy update is in a stable state. The policy gradient clipping fraction (actor/pg_clipfrac) gradually decreased from 0.197% in step one to 0.157% in step ten, always remaining at a very low level, indicating that almost all policy updates are within the allowed range and the protection mechanism against excessive updates has not been triggered. This consistently low clipping fraction validates the effectiveness of the Clip-Higher strategy—by using asymmetric clipping (clip_ratio_low=0.2, clip_ratio_high=0.28), sufficient space is reserved for upward updates, avoiding training stagnation caused by excessive clipping. The lower bound clipping fraction (actor/pg_clipfrac_lower) is close to zero in all steps (maximum is only 1.2e-7), indicating no policy degradation, proving the success of the strategy to strictly limit downward updates.

The KL divergence (actor/ppo_kl) remains between 1.3e-5 and 2.4e-5 over the first ten steps (except for the abnormally low value of 1.51e-6 in step five), with extremely small values and a narrow fluctuation range. The KL divergence in step ten is 1.46e-5, within the normal range. This extremely small KL divergence, combined with the low clipping fraction, jointly ensures the stability of training, avoiding the risk of policy collapse or sudden performance degradation. Since `kl_coef=0.0` is set in the configuration, the KL divergence term is not directly added to the loss function. These observed small KL values are entirely a natural result of the clipping mechanism and the small learning rate (1e-6), reflecting the inherent stability of the DAPO algorithm.The gradient norm (actor/grad_norm) shows a continuous downward trend over the first ten steps, decreasing from 0.132 at step one to 0.104 at step ten, a cumulative drop of 21%. The magnitude of the gradient norm directly reflects the intensity of parameter updates; its downward trend indicates that the model parameters are gradually approaching a local optimum, requiring progressively smaller adjustments. The gradient norm remains within the healthy range of 0.096-0.133 across all steps, with neither vanishing nor exploding gradients, indicating that the backpropagation process is functioning well.

Of particular interest is the evolution of policy entropy (actor/entropy), which gradually rises from 0.158 at step one to 0.180 at step ten, an increase of 14%. This sustained increase in entropy is strong evidence of the success of the DAPO algorithm's Clip-Higher strategy—in traditional GRPO baselines using symmetric clipping, entropy often drops rapidly to near zero early in training, causing the model to lose exploration capability and output diversity. DAPO successfully maintains and enhances policy exploration through asymmetric clipping, avoiding the entropy collapse problem.

The statistical distribution of the advantage function (critic/advantages) remains relatively consistent across steps. The mean advantage fluctuates between 0.013 and 0.054, close to zero, which aligns with DAPO's design inherited from GRPO—the advantage function measures the quality of a response relative to the batch average, so its mean should theoretically be near zero. The extreme values of the advantage function remain stable between -3.75 and +3.75. This symmetric range indicates that the batch contains both responses significantly better than average and those notably worse, providing clear learning signals for policy gradients. The application of the Token-Level Policy Gradient Loss ensures that these advantage values are fairly distributed across sequences of different lengths, preventing long sequences from receiving disproportionately large gradients due to containing more tokens. The stability of the advantage function distribution suggests that the algorithm's relative quality estimation mechanism is functioning properly, effectively identifying the quality of different responses.

## In-Depth Analysis of Full Training Experiment Results on Wandb

### Overview of Training Dynamics

Through a systematic analysis of the complete training process logs on Wandb, we can gain a deep understanding of the full-cycle learning dynamics of the ReTool method under DAPO algorithm optimization. The experiment compares the performance of models under two training configurations, both using qwen2.5-32b as the base model with tool-use training, but differing in exploration strategies and optimization parameters. Looking at the overall trend, the training process spans approximately 110 training steps, exhibiting stable learning curves and significant performance improvements, ultimately achieving an average accuracy of 52% and a Best-of-30 accuracy of 85% on the AIME 2025 validation set.

### In-Depth Analysis of Core Performance Metrics

**Evolution of Validation Set Accuracy** reveals the phased improvement characteristics of the model's capabilities. In the val-core metric group, the mean@30 accuracy (average accuracy after generating 30 responses per question) rises from approximately 0.25 (25%) at the start of training through three distinct upward phases to a final 0.52 (52%), a cumulative increase of 27 percentage points. The first rapid improvement phase occurs in the first 20 steps, with accuracy climbing from 25% to 35%, an average increase of 0.5 percentage points per step. This is a critical period for the model to quickly learn basic tool-use patterns. The second plateau phase occurs between steps 20-60, with accuracy fluctuating between 35-40% and growth slowing, reflecting a transitional period where the model consolidates learned skills and explores more complex strategies. The third accelerated improvement phase occurs between steps 60-100, with accuracy rapidly rising from 40% to 52%, demonstrating a breakthrough in strategy optimization built upon earlier exploration.

More noteworthy is the best@30 metric (the ability to generate at least one correct answer in 30 attempts), which continuously improves from an initial ~0.60 (60%) to a final 0.85 (85%), a cumulative increase of 25 percentage points. The sustained rise of this metric indicates that the model's peak capability is steadily strengthening; even when the average fluctuates, the model's ability to find correct solutions within the exploration space is steadily improving. The orange and green curves show a highly consistent overall trend throughout training but exhibit periodic leadership transitions. The orange line performs better in the first 40 steps (best@30 approximately 2-3 percentage points higher), likely due to the initial stability advantage from its more conservative policy updates. The green line overtakes after step 60 and ultimately achieves a higher accuracy level (85% vs 82%), suggesting that its more aggressive exploration strategy demonstrates stronger long-term potential after sufficient training.

The standard deviation of accuracy (acc/maj@30/std) remains within the range of 0.05-0.08, exhibiting an inverted V-shaped trend of first increasing and then decreasing. The standard deviation remains stable at approximately 0.055 in the early stages, increases to a peak of 0.078 in the middle of training (steps 40-70), and then gradually decreases to 0.062 in the later stages (steps 70-110). This pattern profoundly reflects the exploration-exploitation dynamic balance of reinforcement learning. The small standard deviation in the early stage indicates relatively conservative and consistent model behavior; the increase in the middle stage indicates that the model is actively exploring various tool-use strategies, generating more diverse response patterns; the decrease in the later stage indicates that the model begins to converge to validated high-quality solutions, with behavior becoming more stable and predictable. The standard deviation of best@30 similarly shows an inverted V-shaped pattern, with the peak occurring in the middle of training (approximately steps 50-60), further validating that the middle stage is the most active period for model strategy differentiation and exploration.

**Majority Voting Accuracy** (acc/maj@30/mean) provides important insights into model consistency. This metric increases from an initial ~0.28 (28%) to a final ~0.34-0.36 (34-36%), an increase of about 8 percentage points. Notably, the majority voting accuracy is consistently significantly lower than the mean@30 accuracy (by about 15-18 percentage points). This gap indicates that among the 30 responses generated by the model, the majority is not always correct, indicating substantial answer diversity. The majority voting accuracy of the green line is slightly lower than the orange line in the later stages (steps 80-110, by about 2 percentage points). Combined with its higher best@30 and mean@30 accuracy, this pattern suggests that the green configuration sacrifices some consistency in exchange for higher peak performance and average level, a natural consequence of its high-entropy exploration strategy.

### Deep Interpretation of Interaction Turn Evolution

**Complex Patterns of Training Set Interaction Turns** reveal fundamental differences in tool-use strategies between the two configurations. The average number of interaction turns for the orange line (num_turns/mean) shows a clear upward trend from an initial ~7 turns, rapidly climbing in the middle of training (steps 40-60), and finally stabilizing at a high level of 9-9.5 turns, a cumulative increase of about 35%. This growth pattern indicates that the model under the orange configuration is learning to conduct deeper verification and iteration, tending to use multiple rounds of tool calls to improve answer reliability. The green line remains at a relatively stable level of 7-8 turns, and although it also shows a slight upward trend, the magnitude is much smaller than that of the orange line. This difference stems from the trade-off in optimization objectives between the two configurations—the orange configuration may have set a lower early-stopping threshold or more conservative termination conditions, encouraging the model to conduct more thorough exploration and verification before giving a final answer.

The maximum number of interaction turns (num_turns/max) remains stable at 15-16 turns for both lines, which is the natural upper bound given the configuration parameters max_turns=8 and multiple response sampling (n_resp_per_prompt=16). Interestingly, even in the later stages of training, the maximum value remains at this upper limit, indicating that there are always some complex problems requiring the model to explore to the maximum depth; the model has not yet learned to terminate early in all cases. The minimum number of interaction turns remains stable at 2 turns, indicating that for the simplest problems, the model can quickly identify and provide answers throughout the entire training process, requiring only one round of thinking and one tool call. The stability of these extreme values contrasts with the changes in the average, suggesting that the evolution of interaction turns mainly occurs on moderately difficult problems, rather than on extremely simple or extremely difficult ones.

**Conservative Characteristics of Validation Set Interaction Turns** contrast sharply with the training set. The average number of interaction turns on the validation set (val-aux/num_turns/mean) shows a downward trend from an initial ~6.8 turns, finally stabilizing at 5.8-6.0 turns, significantly lower than the 7-9.5 turns on the training set. This difference has multiple causes. First, the different sampling parameters used during validation (top_p=0.6, temperature=1.0) are more conservative compared to the training parameters. The top_p=0.6 nucleus sampling limits the model to considering only the top 60% of vocabulary with the highest cumulative probability, reducing the possibility of generating overly risky or uncertain intermediate steps, leading to more direct reasoning paths. Second, the AIME 2025 problems on the validation set may differ in difficulty distribution from the DAPO-Math-17k training set. If the validation set problems are relatively more standard or similar to certain types of problems in the training set, the model may have learned more efficient problem-solving patterns. Third, the model is not affected by gradient updates during validation, adopting a more deterministic reasoning mode, while the exploratory needs during training drive up the number of interaction turns.

The green line shows significantly lower and more stable interaction turns on the validation set (approximately 5.8-6.0 turns), while the orange line is slightly higher (approximately 6.2-6.5 turns) and exhibits greater fluctuation. Combined with the green line's advantage in validation set accuracy, this pattern indicates that the green configuration achieves higher inference efficiency while maintaining high accuracy, reflecting its better generalization of tool-use strategies during training. Although the orange configuration uses more interaction turns on the training set (9-9.5 turns), this strategy does not translate into a proportional performance improvement on the validation set, instead incurring additional computational overhead. This suggests that some of its additional interaction turns may be overfitting to the training set rather than representing truly effective reasoning depth.

### Fine-Grained Analysis of AIME 2025 Tiered Performance

**Excellent Performance on Simple Problem Sets** demonstrates the model's solid foundation in basic reasoning capabilities. On the simplest problem set (aime_2025/score/mai@30, containing 30 relatively easy problems), the model's average score rapidly improves from an initial ~ -0.20 to a final ~0.20-0.25, achieving a transition from negative returns to significant positive returns within the scoring range (-1 to +1). The green line consistently leads the orange line by approximately 0.03-0.05 points on this metric, ultimately reaching a higher level of about 0.25. This score corresponds to an accuracy of approximately 62.5% (mapped from -1/+1 to 0-100%), indicating that the model has developed strong problem-solving abilities on simple problems. The score shows rapid improvement in the first 30 steps of training (from -0.20 to 0.05), then enters a plateau phase between steps 30-70 (0.05-0.10), and finally accelerates again between steps 70-110 (0.10-0.25). This three-stage growth pattern is highly consistent with the overall accuracy curve.

The standard deviation for the simple problem set (mai@30/std) remains within a stable range of approximately 0.48-0.52, with a slight downward trend (from 0.52 to 0.48). This relatively small standard deviation indicates that the model's performance on simple problems is relatively consistent, with smaller difficulty differences between different problems, or the model has learned general strategies for handling various types of problems within this difficulty range. The slight decrease in standard deviation further suggests that the model's handling of simple problems becomes more stable and reliable in the later stages of training.

**Balanced Development on Medium-Difficulty Problems** reflects the improvement in the model's generalization ability. The average score for the medium-difficulty problem set (maj@8, containing 8 medium-difficulty problems) increases from an initial ~ -0.30 to a final ~0.05-0.15, a cumulative improvement of about 0.35-0.45 points, corresponding to an accuracy increase from approximately 35% to 52.5-57.5%. The two lines perform similarly at this difficulty level, with a final score difference of only about 0.02-0.03 points, indicating comparable capabilities between the two configurations on medium-difficulty problems. The orange line has a slight advantage in the early stages of training (steps 0-50), while the green line overtakes in the later stages (steps 60-110), consistent with the leadership transition pattern observed in the overall performance curve.

The score curve for medium-difficulty problems exhibits more pronounced non-monotonicity, with local performance dips occurring around steps 20-30, 50-60, and 80-90, with a drop of about 0.05-0.10 points. These fluctuations are more severe than those on the simple problem set, reflecting the sensitivity of medium-difficulty problems to changes in model strategy—when the model tries new tool-use patterns, it may temporarily reduce performance on some medium-difficulty problems, but this exploration is a necessary cost for achieving higher long-term performance. The standard deviation is significantly larger on the medium-difficulty problem set (approximately 0.52-0.58) and shows a trend of first increasing and then decreasing during training, with a peak around steps 40-60 (approximately 0.60), once again validating that the middle stage is the most active period for model strategy exploration.

**Challenges and Progress on High-Difficulty Problems** reveal the model's capability boundaries and room for improvement. On the more difficult problem set (maj@4, containing 4 harder problems), the average score improves from an initial ~ -0.15 to a final ~0.05-0.10, a cumulative increase of about 0.20-0.25 points. Although the absolute improvement is smaller than on the simple problem set, considering the lower starting point and greater difficulty, this improvement is still significant. The green line shows a more pronounced advantage at this difficulty level, with a final score of about 0.10, approximately 0.03-0.05 points higher than the orange line, indicating that the green configuration's high-entropy exploration strategy demonstrates a stronger advantage on difficult problems.

The most difficult problem sets (worst@8 and worst@4, containing the 8 and 4 hardest problems, respectively) reveal the main challenges the model faces and the bottlenecks that still need to be overcome. The score for worst@8 slowly improves from an initial ~ -0.70 to a final ~ -0.20 to -0.15. Although still negative (corresponding to an accuracy below 50%), the improvement is 0.50-0.55 points, a relative improvement of about 70%. The performance on worst@4 is slightly better, finally stabilizing around -0.10 to -0.05, close to the breakeven point. These negative scores indicate that even after sufficient training, the model still faces significant challenges on extremely difficult mathematical competition problems, with accuracy below 50%. However, the continuous improvement trend (both lines show a stable upward trajectory without a plateau in the later stages of training) suggests that further training or using larger-scale models could bring additional improvements.

The standard deviation for the most difficult problem sets (worst@8/std and worst@4/std) is significantly larger, approximately in the range of 0.18-0.26, and exhibits complex fluctuation patterns during training. This high standard deviation indicates that even within the subset of the most difficult problems, there is still considerable variation in difficulty between different problems, or the model's ability to handle different types of difficult problems is uneven. The increase in standard deviation in the middle of training (from about 0.20 to 0.26) reflects significant changes in the model's strategies for handling difficult problems during the exploration phase, while the subsequent decrease (to 0.21-0.23) indicates that the model begins to converge to relatively stable patterns for solving difficult problems.

### Deep Evolution of Response Generation Patterns**The Three-Phase Growth Pattern of Response Length** is a key window into understanding the evolution of the model's reasoning strategy. The average response length (response_length/mean) experienced significant growth from an initial ~2500 tokens, peaking at ~4700-4800 tokens around training steps 60-70, before stabilizing in the 4200-4500 tokens range. The cumulative increase over the entire training process was approximately 80%. This growth can be divided into three distinct phases. The first phase (steps 0-30) is a rapid growth period, where the response length increased from 2500 tokens to 3500 tokens, with an average increase of about 33 tokens per step. This reflects the model learning to generate more detailed reasoning processes, incorporating more intermediate steps and tool calls. The second phase (steps 30-70) is a sustained growth period, where the response length increased from 3500 tokens to a peak of 4700-4800 tokens, with an average increase of about 30 tokens per step. The growth rate slowed slightly but remained significant, indicating that the model continued to deepen the complexity of its reasoning based on the earlier foundation. The third phase (steps 70-110) is a stabilization and decline period, where the response length fell from its peak and stabilized in the 4200-4500 tokens range. This decline is a manifestation of the model optimizing for efficiency—after sufficient exploration, the model learned to reduce unnecessary redundant reasoning while maintaining high accuracy.

The orange line maintained a shorter response length throughout the training process (3500-4300 tokens), with a peak around step 50 (~4300 tokens), subsequently stabilizing at 3800-4000 tokens. The green line, on the other hand, experienced more significant growth, reaching a peak of about 4800 tokens and ultimately stabilizing at 4400-4500 tokens. This difference profoundly reflects the divergence in reasoning strategies between the two configurations. The orange configuration places a greater emphasis on reasoning efficiency, achieving acceptable accuracy through a relatively concise reasoning process. The green configuration adopts a more thorough exploration strategy, generating more detailed and complex reasoning chains to pursue higher accuracy. The performance gap between the two (the green line's final accuracy is about 2-3 percentage points higher) partially stems from this difference in reasoning depth, but it also leads to a difference in training efficiency (the green line takes about 15-20% longer per step).

**The Distribution Characteristics of Response Length** provide important information about the diversity of model behavior. The minimum response length (response_length/min) shows a fluctuating downward trend, gradually decreasing from an initial ~100-300 tokens to lower levels later in training (50-200 tokens). This decline indicates that the model has learned to adopt more direct and concise solutions for simple problems, no longer generating lengthy intermediate steps for problems that do not require complex reasoning. The large fluctuations in the minimum value (which can differ by 100-200 tokens between individual steps) reflect the varying difficulty of the simplest problems in different batches, as well as changes in the model's definition of "simple" at different training stages—the early model might adopt a conservative, detailed reasoning approach for most problems, whereas the later model can quickly identify truly simple problems and take shortcuts.

The maximum response length (response_length/max) consistently remained at a high level of 10000-20000 tokens, repeatedly reaching or approaching the configured upper limit of 16384 tokens. The maximum value curve exhibits more drastic fluctuations than the average, potentially differing by 5000-8000 tokens between different batches. This fluctuation stems from the random sampling of the most complex problems and the model's changing strategies on these problems. The clip_ratio metric (the proportion of responses truncated because they reached the maximum length) shows that about 2-5% of responses hit the upper limit, with the specific proportion varying throughout the training process. The truncation ratio for the orange line was relatively stable (about 2.5-3.5%), while the green line experienced significant growth (from about 2% to a peak of about 5%), subsequently falling back to about 3-4%. The higher truncation ratio of the green line is consistent with its longer average response length and more in-depth exploration strategy. These truncated, extra-long responses typically correspond to deep exploration of extremely complex problems. Although their generation time dominates the entire Rollout phase (the bucket effect), they are also key samples for the model to learn how to handle the most difficult problems.

**The Stability of Input Prompt Length** validates the consistency of the dataset. The average prompt_length fluctuated within a very narrow range of 330-340 tokens throughout the entire training process (standard deviation of only about 2-3 tokens). The minimum value was about 256 tokens, and the maximum value ranged from 600 to 1700 tokens. This high degree of stability is expected because the description length of input problems is determined by the dataset itself and is not affected by the model's training state. The two lines overlap almost completely in prompt length, with no visible difference, confirming that they use the exact same training and validation datasets. The clip_ratio for prompt_length is consistently 0, indicating that all problem descriptions are within the limit of max_prompt_length=2048, and there are no cases of truncation due to excessively long inputs.

Although the maximum prompt length fluctuates within the 600-1700 tokens range, this fluctuation merely reflects the natural variation in the description of the most complex problems across different batches and does not indicate any training dynamics. Interestingly, there is a 5-fold gap between the maximum prompt length (up to ~1700 tokens) and the average length (~335 tokens). This suggests that the dataset contains some problem descriptions that are very detailed and complex (possibly including multiple sub-problems, extensive background information, or complex mathematical symbols), while the descriptions of most problems are relatively concise. This distribution characteristic of prompt length partially explains the wide span of response length distribution—complex problem descriptions typically require longer responses to be fully addressed.

### Systematic Analysis of Sequence Length Management

**The Continuous Growth of Global Sequence Length** directly reflects the evolution of the computational burden during training. The average global sequence length (global_seqlen/mean, measuring the total number of tokens processed per training step) steadily increased from an initial ~300,000 tokens to a final ~500,000-550,000 tokens, a cumulative increase of about 80-83%, which is highly consistent with the growth rate of response length. The growth of this metric has multiple sources: first, the direct increase in response length (from 2500 to 4200-4500 tokens); second, more complex multi-turn interactions leading to each response containing more intermediate states; and third, the cumulative effect of multiple forward passes in the training pipeline (Rollout, log probability, policy update).

The global sequence length for the orange line is significantly lower than that for the green line, ultimately reaching about 470,000 tokens vs. 550,000 tokens, a gap of about 17%. This gap is slightly larger than the difference in response length between the two (about 4000 vs. 4500 tokens, a gap of about 12.5%). This suggests that the green configuration not only generates longer individual responses but may also involve more repeated computations or deeper gradient accumulation in the training pipeline, causing the gap in total token processing volume to be amplified. This gap directly translates into a difference in training efficiency—although both configurations use the same hardware resources (8 H200 GPUs), the green configuration needs to process more tokens per step and therefore takes longer (about 8500 seconds vs. 7000 seconds, a gap of about 21%).

**The Evolution of Sequence Length Extremes** reveals changes in inter-batch heterogeneity. The maximum global sequence length (global_seqlen/max) grew from an initial ~450,000 tokens to a peak of ~560,000 tokens (an increase of about 24%), subsequently stabilizing at 540,000-560,000 tokens. The minimum global sequence length also showed an increasing trend, rising from about 280,000 tokens to about 430,000-500,000 tokens (an increase of about 54-79%). The growth rate of the minimum value is significantly greater than that of the maximum value. This indicates that even when processing "simple" batches (containing relatively simple problems or problems where the model converges quickly) in the later stages of training, the total number of tokens processed has increased substantially, consistent with the growth in average response length and more complex reasoning patterns.

The balanced_min and balanced_max metrics (sequence length extremes after some form of balancing) exhibited a similar growth pattern. The difference between them (minmax_diff, reflecting the heterogeneity of sequence lengths between batches) showed an inverted V-shaped trend during training, first increasing and then decreasing. The initial difference was about 200,000 tokens, which sharply increased to a peak of about 850,000 tokens (a 325% increase) in the middle of training (steps 40-60), before falling back to 300,000-550,000 tokens in the later stages (steps 70-110). This pattern profoundly reflects the three phases of training dynamics: in the initial phase, model behavior is relatively uniform, and the processing methods for different batches differ little; in the middle phase, the model actively explores various strategies, adopting differentiated processing methods for different types of problems, leading to a surge in inter-batch heterogeneity; in the later phase, the model's strategy matures and stabilizes, and the differences between batches diminish but remain higher than the initial level.

The peak minmax_diff for the green line (about 850,000-900,000 tokens) is significantly higher than that for the orange line (about 700,000-750,000 tokens), once again confirming the higher exploration intensity and behavioral diversity of the green configuration. It is noteworthy that even in the later stages of training, minmax_diff did not return to its initial level but stabilized at about 300,000-550,000 tokens (1.5-2.75 times the initial value). This indicates that the model's learned differentiated problem-solving strategies are retained and become part of its generalization capability.

### Panoramic Analysis of Computational Performance and Resource Utilization

**The Multidimensional Growth of Token Processing Volume** comprehensively illustrates the evolution of the training burden. The total token processing volume (perf/total_num_tokens) steadily increased from an initial ~25M tokens/step to a final ~40M tokens/step (green line) or ~35M tokens/step (orange line), a cumulative increase of 60% (orange) to 80% (green). This metric includes the forward and backward passes during Rollout generation, Reference Model log probability calculation, and Actor updates. Therefore, its value is significantly larger than the number of tokens generated for responses alone (about 2-4.5M tokens/step). The ratio of total tokens to response length is about 8-10 times, and this multiple is relatively stable, indicating that the distribution of token processing across the stages of the training pipeline remains consistent.

The growth curve of the total number of tokens clearly shows the phased characteristics of the training dynamics. Steps 0-30 are a rapid growth period (from 25M to 32M, increasing by about 0.23M per step), steps 30-70 are a sustained growth period (from 32M to 38-40M, increasing by about 0.15-0.20M per step), and steps 70-110 are a stabilization period (maintained at 38-40M, with growth near zero). This phased growth is highly synchronized with the evolution of response length, number of interaction rounds, and policy complexity, indicating that they are coordinated changes driven by the same underlying mechanism.

**The Gradual Decline in Time Efficiency** is an inevitable cost of long sequence processing. The time per step (perf/time_per_step) shows a clear increasing trend. The orange line grew from an initial ~5500 seconds (92 minutes) to a peak of ~7500 seconds (125 minutes), ultimately stabilizing at 7000-7200 seconds (117-120 minutes), a cumulative increase of about 27-36%. The growth for the green line was more significant, from an initial ~5500 seconds to a peak of ~9000 seconds (150 minutes), ultimately stabilizing at 8000-8500 seconds (133-142 minutes), a cumulative increase of about 45-64%. The time gap between the two lines expanded from nearly zero in the early stages to about 1000-1500 seconds (17-25 minutes) in the later stages, a gap of about 15-21%. This directly stems from the longer responses and larger token processing volume of the green configuration.

The main driver of the time increase is the growth in response length. Longer responses mean more token generation, more code execution waiting, and more forward pass computation. Data shows a near-linear relationship between time per step and response length: for every 1000-token increase in response length, the time increases by about 1000-1500 seconds (17-25 minutes). This linear relationship indicates that the primary bottlenecks are token generation itself (via the vllm engine) and code execution waiting (via SandboxFusion), rather than other fixed overheads. If the bottleneck were fixed overheads like model loading or batch scheduling, the time increase would be sub-linear. If the bottleneck were operations with super-linear complexity like gradient computation, the time increase would be super-linear. The observed linear relationship validates the rationality of the system design—the Rollout phase dominates the total time, and the complexity of Rollout is proportional to the number of tokens.

**The Corresponding Decline in Throughput** is the combined result of time growth and token count growth. The system throughput (perf/throughput) gradually decreased from an initial ~660 tokens/s to a final ~600-620 tokens/s (orange line) or ~580-600 tokens/s (green line), a decrease of about 8-12%. Although the total number of tokens processed per step increased by 60-80%, the actual processing capacity per unit time decreased because the time increased by 27-64%. This decline in throughput is an inherent challenge of long sequence processing, primarily due to the following reasons.

First is the decline in batch processing efficiency. Although vllm is configured with mode=async and train_batch_size=512, theoretically capable of processing 512 requests simultaneously, in actual operation, due to the different progress of requests caused by multi-turn interactions, the actual average batch size is much smaller than 512. Initially, all requests are generating text synchronously, and the batch saturation is high. As some requests encounter code execution triggers and pause to wait, the number of active requests in the batch decreases. When paused requests receive feedback and rejoin, new requests encounter triggers and pause. This dynamic change in the asynchronous batch leads to an average batch size that may be only 50-70% of the theoretical value, and a reduction in batch size directly lowers GPU utilization and throughput.

Second is the accumulation of code execution waiting time. Although a single code execution typically takes only 0.1-0.5 seconds, when a large number of requests in a batch require code execution simultaneously or nearly simultaneously, the pool of 128 workers in SandboxFusion may become saturated, causing some requests to queue up. In the later stages of training, due to an increase in the average number of interaction rounds (the orange line increased from 7 to 9.5 rounds) and an increase in the complexity of code per round, both the total number of code executions and the time per execution increase, further exacerbating the waiting time.

Third is the computational overhead of long sequences. The computational complexity of the Transformer's self-attention mechanism is O(n²), where n is the sequence length. When the response length increases from 2500 tokens to 4500 tokens (an 80% increase), the theoretical computational complexity increases by (4500/2500)² = 3.24 times. Although Ulysses sequence parallelism and various optimization techniques can mitigate this quadratic growth, the additional overhead of long sequences still exists in practice. The fact that throughput only decreased by 8-12% (rather than the theoretical 70% decrease) indicates that system optimizations largely offset the impact of long sequences, but could not completely eliminate it.

The orange line consistently has a slightly higher throughput than the green line (about 630 vs. 610 tokens/s, a gap of about 3%), reflecting its consistent advantage in efficiency. Interestingly, the decline in throughput mainly occurred in the first 60 steps of training (from 660 to 600-610 tokens/s), while it remained largely stable from steps 60 to 110. This is synchronized with the evolution of response length—response length grew rapidly in the first 60 steps, peaked around steps 60-70, and then declined and stabilized. Correspondingly, throughput declined rapidly during the same period and then stabilized. This synchronicity once again confirms that response length is the primary factor affecting training efficiency.**Exceptional Stability in VRAM Management** demonstrates the success of FSDP and memory optimization strategies. The maximum memory reserved (perf/max_memory_reserved_gb) remained within a very narrow range of 216.8-217.4 GB throughout training, with a standard deviation of only about 0.2-0.3 GB and fluctuation of less than 0.3%. The maximum memory allocated (perf/max_memory_allocated_gb) was similarly stable, staying within 204.8-205.0 GB with a standard deviation of only about 0.1 GB. This high stability indicates that even with an 80% increase in response length and a 60-80% increase in total tokens, the actual peak memory usage barely increased. This is because FSDP shards model parameters across 8 GPUs, with each GPU storing only about 1/8 of the model parameters, significantly reducing per-GPU memory requirements. Additionally, gradient checkpointing reduces memory usage by recomputing intermediate activations during backpropagation instead of storing them throughout, trading computation for memory.

The buffer space of approximately 12 GB between reserved and allocated memory (217 - 205 = 12 GB) provides a safety margin for temporary operations such as batch scheduling, dynamic KV cache expansion, and communication buffers. This buffer remained stable throughout training, indicating no memory leaks or abnormal memory accumulation. The two lines overlap almost completely in memory usage with nearly identical values (difference less than 0.1 GB), showing that memory usage is primarily determined by model size and batch configuration, with little relation to specific training dynamics (e.g., response length, number of interaction rounds). This decoupling is an ideal system design, ensuring training robustness—even significant changes in model behavior will not trigger out-of-memory errors.

The total reserved memory of 217 GB accounts for approximately 19.2% of the total VRAM capacity of 8 H200 GPUs (approximately 8 × 141 GB = 1128 GB, assuming 141 GB per H200 card), representing a relatively conservative memory utilization rate. This conservative utilization leaves room for larger batch sizes or longer sequence lengths in the future, allowing configuration parameters to be adjusted without hardware replacement if training scale needs to be expanded. Meanwhile, the allocated memory of 205 GB constitutes 94.5% of the reserved memory, indicating that the reserved memory is effectively utilized rather than being overly conservative and wasteful.

**Stable Balance of Compute Utilization** reflects the trade-offs in system design. The Model FLOPs Utilization (perf/mfu/actor) fluctuated slightly between 0.388-0.394, averaging about 39% with a standard deviation of only about 0.002-0.003. While this MFU level is lower than the theoretical peak for pure computation scenarios (typically 50-60%), it is quite reasonable given the specific characteristics of ReTool training.

Several factors reduce MFU in ReTool training. First is the waiting time for multi-turn interactions. Each code execution requires pausing generation to wait for SandboxFusion to return results, during which the GPU is idle or underutilized. Assuming an average wait of 0.3 seconds per interaction turn (0.2 seconds for code execution + 0.1 seconds for network communication), 8 interaction turns accumulate 2.4 seconds of waiting, accounting for 16-24% of the total response generation time (assuming 10-15 seconds). During this time, the GPU is almost completely idle, directly lowering MFU. Second is the CPU-GPU data transfer overhead from CPU offloading. FSDP offloads model parameters and optimizer states to CPU memory, requiring loading from CPU to GPU at the start of each mini-batch training and transferring back to CPU after computation. Although asynchronous transfer and prefetching techniques are used to hide latency, data transfer still occupies PCIe bandwidth and introduces synchronization points, reducing the proportion of effective GPU computation time. Third is the scheduling overhead of asynchronous Rollout. Multiple inference requests execute concurrently in asynchronous mode, requiring the scheduler to dynamically manage request queues, batch assembly, KV cache allocation, etc. While these operations primarily occur on the CPU, they affect the GPU instruction stream, leading to bubble time.

Despite these reducing factors, the 39% MFU still reflects successful system optimization. Compared to pure inference scenarios (typically 20-30% MFU) and simple supervised learning training (up to 45-55%), ReTool training's MFU sits at a reasonable intermediate level. This indicates that while multi-turn interactions and CPU offloading do introduce additional overhead, techniques such as asynchronous execution, batch optimization, and hybrid parallelism largely mask their impact. The two lines overlap almost completely in MFU (difference less than 0.001), showing that MFU is primarily determined by system architecture and hardware characteristics, with little relation to specific training strategies (response length, exploration intensity, etc.). This stability is ideal, meaning users can adjust training hyperparameters to optimize performance without worrying about significant MFU fluctuations affecting training efficiency.

MFU remained highly stable throughout training (fluctuation range of only 0.6%), showing no downward trend, in contrast to the 8-12% decline in throughput. The reason for this difference is that MFU measures the efficiency of GPU effective computation, while throughput measures the end-to-end token processing rate. Even if GPU computational efficiency remains stable, overall throughput still decreases due to more tokens needing computation (longer responses) and accumulated waiting time (more code execution). This observation suggests that the main cause of throughput decline is not decreased computational efficiency (MFU stable), but increased computation volume and extended waiting time.

### Detailed Analysis of Training Time Decomposition

**Dominance of Actor Update Time** highlights the bottleneck in the Rollout phase. The time to update the actor (timing_s/update_actor, comprising three sub-stages: Rollout generation, log probability computation, and policy update) grew from an initial approximately 1700 seconds (28 minutes) to a peak of about 3000 seconds (50 minutes), eventually stabilizing at 2600-2900 seconds (43-48 minutes). The orange line's update_actor time is significantly lower than the green line, at about 2400 seconds vs 2900 seconds, a difference of approximately 500 seconds (8 minutes) or 21%. This phase accounts for 35-40% of the total training step time (for steps without validation), making it the single largest time overhead.

From known detailed decomposition data (based on actual observations from the first ten steps), within update_actor time, Rollout generation accounts for about 2500-3000 seconds (42-50 minutes), log probability computation for about 500-550 seconds (8-9 minutes), and policy update for about 1800-2000 seconds (30-33 minutes). The ratio is approximately 50%:10%:40%, with Rollout and policy update being the two major overheads. The high Rollout time is due to the complete generation of 512 responses, including multi-turn interactions and code execution waiting. The high policy update time is mainly due to CPU-GPU data transfer from CPU offloading—parameters need to be loaded at the start of each mini-batch and transferred back after updates. This frequent data transfer between CPU and GPU accumulates significant time. Log probability computation is relatively fast because it only requires forward propagation, no backpropagation or gradient updates, and can leverage cached KV cache for acceleration.

**Reasonableness of Validation Testing Time** validates the efficiency of the evaluation strategy. Validation testing time (timing_s/testing, non-zero only in steps with validation) appears as approximately 550-800 seconds (9-13 minutes) across various validation steps, averaging about 650 seconds (10.8 minutes). This time includes the complete inference process for generating 30 responses each for 30 validation questions (900 responses total), as well as answer extraction and accuracy calculation. Validation time shows an increasing trend, from about 550 seconds at step 5 to about 800 seconds at step 110, a cumulative increase of about 45%, which is slightly smaller than the response length increase (about 60-80%), suggesting that the validation process may employ certain optimizations (e.g., shorter max_response_length or earlier early stopping).

Validation time accounts for approximately 10-15% of the total time for steps with validation (e.g., step 10's total time of 7700 seconds includes 1200 seconds for validation), which is an acceptable proportion. The current configuration validates every 5 steps, meaning the average per-step validation overhead is approximately (650 seconds / 5) = 130 seconds, accounting for 1.7% of the average step time (about 7500 seconds). This lightweight validation overhead ensures timely monitoring of training progress and model performance without significantly slowing overall training speed.

The difference in validation time between the two lines (green about 750-800 seconds, orange about 650-700 seconds, difference about 100-150 seconds or 15-19%) is consistent with their difference in training response length, indicating that the validation process indeed reflects the model's actual generation behavior on the validation set, rather than using a fixed evaluation setup. This consistency ensures the representativeness of validation results—validation accuracy can truly reflect the model's performance on the validation set under the same generation strategy.

**Comprehensive Evolution of Total Step Time** integrates all phase overheads. The total time per training step (timing_s/step, identical to perf/time_per_step) fully reflects changes in training efficiency, as analyzed in detail earlier. It is worth adding that by comparing steps with and without validation, the additive relationship of phase times can be verified. For example, step 10 (with validation) has a total time of about 7700 seconds = update_actor about 2900 seconds + testing about 1200 seconds + other overhead about 3600 seconds. "Other overhead" includes Reference Model computation, data loading, checkpoint saving, metric logging, etc., accounting for about 47%. This relatively high proportion indicates that besides Rollout and validation, there are numerous auxiliary operations in the training pipeline.

The total time for checkpoint-saving steps (30, 60, 90, etc.) is not significantly higher than adjacent steps (difference less than 100 seconds), indicating that checkpoint saving is performed in parallel or asynchronously with other operations, without causing noticeable additional waiting. This efficient checkpoint saving mechanism (achieved through FSDP's distributed saving) ensures smooth training flow, without performance spikes due to periodic I/O operations.

**Negligibility of Profiling Overhead** confirms the lightweight design of the monitoring system. The time overhead related to profiling (timing_s/stop_profile and timing_s/start_profile) is close to zero, with values in the range of 0.0001-0.0002 seconds, accounting for less than 0.000003% of the total step time. This indicates that data collection by wandb and other performance monitoring tools has almost no measurable impact on training. Modern deep learning frameworks minimize monitoring overhead through techniques such as asynchronous logging, batch uploading, and low-priority background threads, allowing users to enable detailed logging without concern to gain a comprehensive understanding of training dynamics.

**Efficient Execution of Checkpoint Saving** demonstrates the advantages of FSDP's distributed saving. Checkpoint saving time (timing_s/save_checkpoint, non-zero only in saving steps) appears as approximately 46-54 seconds across various saving steps (30, 60, 90, ...), averaging about 50 seconds. For a 32B parameter model (approximately 64 GB in FP16 format), plus optimizer states (approximately 128 GB, as Adam requires storing first and second moments), totaling about 192 GB of data, saving within 50 seconds is quite efficient. This is thanks to FSDP's distributed saving mechanism—each GPU independently saves its responsible model shard (approximately 192 GB / 8 = 24 GB), keeping the total saving time to the time required for a single GPU to save 24 GB of data through parallel I/O. Assuming a disk write speed of 500 MB/s (typical SSD RAID performance), saving 24 GB theoretically takes 48 seconds, which closely matches the observed 46-54 seconds, indicating that I/O bandwidth is fully utilized without significant bottlenecks or inefficiencies.

Checkpoint saving frequency is every 30 steps, meaning the average per-step saving overhead is approximately (50 seconds / 30) = 1.67 seconds, accounting for 0.022% of the average step time (about 7500 seconds), which is completely negligible. Even considering validation overhead (1.7%) and saving overhead (0.022%), the total "non-training" overhead is still only about 1.7%, with over 98% of training time dedicated to actual model optimization—a hallmark of an efficient training system.

### Combined Theoretical and Practical Analysis of Reinforcement Learning Algorithm Metrics

**Minimal KL Divergence Characteristics** validates the stability design of the DAPO algorithm. The KL divergence (actor/ppo_kl, measuring the difference between the new and old policies) remained at extremely low levels throughout training, with values ranging from 1e-5 to 2.5e-4 and a median of about 5e-5. This extremely small KL divergence (compared to typical PPO training values of 1e-3 to 1e-2) indicates that the difference between old and new policies is tightly controlled, with each update being a small incremental adjustment. The training process is very stable, with no risk of policy collapse or sudden performance degradation.

KL divergence shows a slight increasing trend, from an initial about 1-2e-5 to a later about 1-2e-4, an order of magnitude increase, but the absolute value remains extremely small. This increase is reasonable, reflecting that as model capability improves, the magnitude of policy adjustments increases slightly, but still within strict control. The orange line's KL divergence (about 1-5e-5) is significantly lower than the green line (about 5-2.5e-4), differing by an order of magnitude. This difference suggests that the orange configuration adopts a more conservative policy update—each update changes the policy less, possibly achieved through a smaller learning rate, stronger clipping, or a larger KL penalty coefficient (although the configuration shows kl_coef=0.0, there may be implicit KL constraints in practice).

The extremely small KL divergence, combined with a low clipping ratio (actor/pg_clipfrac about 0.01-0.03%, detailed later), together form a dual guarantee of training stability. KL divergence ensures no sudden policy changes, while the clipping mechanism prevents extreme single-step updates. Since the configuration sets kl_coef=0.0, the KL divergence term is not directly added to the loss function; these observed small KL values are naturally produced by the clipping mechanism and small learning rate (1e-6). This phenomenon demonstrates the inherent stability of the DAPO algorithm—even without explicitly adding KL penalty, through reasonable clipping and learning rate settings, the algorithm can naturally maintain small KL divergence and avoid policy divergence.

**Near-Zero Policy Gradient Loss** indicates that the policy is close to a stable point. The policy gradient loss (actor/pg_loss) remained within a very small range throughout training, fluctuating between -0.001 and +0.001, with an average absolute value of about 0.0003, approaching zero overall. This small fluctuation is normal, reflecting fine-tuning of the policy near a local optimum. A near-zero policy gradient loss does not mean training stagnation; rather, it indicates that the magnitude of policy updates is tightly controlled, avoiding excessive oscillations. In fact, even with small losses, accumulated tiny updates can still bring significant performance improvements—from an initial 25% accuracy to a final 52%, with pg_loss remaining near zero throughout the process.Two lines exhibit an interesting mirror symmetry in the policy gradient loss. The orange line primarily fluctuates in the negative region (approximately -0.0005 to 0), while the green line is more often in the positive region (approximately 0 to +0.0005), but their absolute values are of the same order of magnitude (approximately 0.0003-0.0005). This difference may stem from different initializations, minor hyperparameter variations (such as a 1e-7 level difference in learning rate), or random seeds. However, since the absolute values are very small, this difference does not lead to a significant divergence in training trajectories, and the final performance of the two lines remains similar. The sign difference in the loss may reflect subtle differences in the optimization direction—the orange configuration might focus more on reducing the probability of low-advantage samples (negative loss), while the green configuration might focus more on increasing the probability of high-advantage samples (positive loss). However, due to GRPO's relative advantage design, these two directions are mathematically equivalent, differing only in implementation.

The policy gradient loss shows no clear trend during training (neither consistently increasing nor decreasing) but fluctuates randomly around zero. This trendless fluctuation indicates that the policy has reached a dynamic equilibrium—while model performance continues to improve, the rate of policy change remains stable, neither accelerating nor decelerating. This is a hallmark of mature reinforcement learning training, indicating that the algorithm successfully balances exploration and exploitation, maintaining a robust learning process.

### In-depth Analysis of the Clipping Mechanism

**The extremely low level of policy clipping ratio** confirms the success of the Clip-Higher strategy. The policy clipping ratio (actor/pg_clipfrac, measuring the proportion of samples that trigger the clipping protection mechanism) remains at an extremely low level throughout training, with values ranging from 1e-7 to 3e-4, corresponding to percentages of 0.00001% to 0.03%. This means that, on average, only 0.05-0.15 samples out of 512 training samples (i.e., almost none) trigger the clipping mechanism. This extremely low clipping ratio indicates that the vast majority of policy updates stay within the allowed range (clip_ratio_low=0.2 to clip_ratio_high=0.28), without attempting overly aggressive updates.

The clipping ratio exhibits an inverted V-shaped trend, first increasing and then decreasing. In the early stage (steps 0-20), it remains around 5e-5 (0.005%); in the middle stage (steps 20-70), it rises to a peak of about 2-3e-4 (0.02-0.03%); in the later stage (steps 70-110), it falls back to about 1-1.5e-4 (0.01-0.015%). This pattern reflects the evolution of training dynamics. The extremely low clipping ratio in the early stage indicates that the model has just started RL training from an SFT checkpoint, and policy adjustments are very cautious. The slight increase in the middle stage (though the absolute value remains very small) suggests that as the model's capabilities improve and policy exploration deepens, the magnitude of policy updates on some samples increases, occasionally hitting the clipping boundary. The decline in the later stage indicates that the model's policy is maturing, and the policy for most samples has converged, no longer requiring large adjustments.

Despite the very low clipping ratio, the Clip-Higher strategy still plays a crucial role. By setting an asymmetric clipping range (0.2 vs 0.28), the algorithm provides more room for upward updates (increasing the probability of high-advantage samples) (28% vs 20%) and less room for downward updates (decreasing the probability of low-advantage samples). Even though very few samples trigger clipping, this asymmetry implicitly guides the optimization direction—when the advantage function sends a strong signal (a sample is significantly better or worse than average), the algorithm allows larger reinforcement for "good" cases and more conservative penalties for "bad" cases. This bias accumulates over time, forming a sustained exploration drive that successfully prevents policy entropy collapse (see the entropy analysis below).

The two lines show similar trends and magnitudes in the clipping ratio, both within the range of 1e-5 to 3e-4, with no significant difference. This indicates that the operational state of the clipping mechanism is primarily determined by the shared algorithm design and hyperparameters (clip_ratio_low/high) and is not significantly affected by specific training dynamics (response length, number of interaction rounds, etc.). This robustness is ideal, ensuring the stability and predictability of the training process.

**The near-zero lower-bound clipping ratio** indicates that the policy has not degenerated. The lower-bound clipping ratio (actor/pg_clipfrac_lower, measuring the proportion of samples that trigger lower-bound clipping due to the policy excessively reducing the probability of certain tokens) is close to zero at all training steps, with values between 1e-8 and 5e-8, corresponding to percentages of 0.000001% to 0.000005%. This extremely small value (3-4 orders of magnitude lower than the overall clipping ratio) indicates that downward updates almost never exceed the allowed range. On average, only 0.00005-0.00025 samples out of 512 (i.e., at the level of statistical error) trigger lower-bound clipping, which can be considered as never triggered.

This near-zero lower-bound clipping ratio is a very positive signal, indicating that the policy has not shown any trend of performance degradation throughout training. If the model excessively reduced the probability of high-quality responses on some samples, it would trigger lower-bound clipping protection, but the actual data shows this almost never happens. Combined with the small positive and negative fluctuations in the policy gradient loss (rather than sustained negative values) and the continuous increase in rewards, it can be confirmed that the direction of policy updates is correct, primarily reinforcing good behavior rather than punishing bad behavior. This is fully consistent with the design philosophy of DAPO (encouraging exploration and upward updates).

The two lines completely overlap in the lower-bound clipping ratio, with nearly identical values (difference less than 1e-9), indicating that this metric is entirely determined by the algorithm mechanism and is independent of the specific configuration. This consistency further validates the inherent robustness of the DAPO algorithm in preventing policy degradation, requiring no additional manual intervention or parameter tuning.

### Key Analysis of Policy Exploration

**The miracle of continuously rising policy entropy** is the most important achievement of the DAPO algorithm. Policy entropy (actor/entropy, measuring the randomness and diversity of the policy output distribution) continuously increases from an initial value of about 0.16 to a final value of about 0.42-0.44, a cumulative increase of nearly 180%, almost 2.75-2.8 times the initial value. This sustained increase in entropy is an extremely rare and valuable phenomenon, almost impossible to observe in traditional GRPO or PPO training. Typically, reinforcement learning training leads to a rapid decline in policy entropy—the model tries various behaviors in the early exploration phase, but as it discovers high-reward behavior patterns, the policy gradually converges to these deterministic behaviors, and entropy collapses to near zero. Once entropy collapses, the model loses its exploration ability, falls into a local optimum, and cannot discover better strategies even if they exist.

DAPO successfully solves the entropy collapse problem through the Clip-Higher strategy. The asymmetric clipping (clip_ratio_low=0.2, clip_ratio_high=0.28) provides 40% more room for upward updates (0.28 vs 0.20). This asymmetry provides a slight encouragement for exploratory behavior in each policy update. Although the impact of a single step is small (clipping ratio only 0.01-0.03%), the cumulative effect over 110 training steps successfully maintains and enhances policy diversity. From the data, the growth in entropy persists almost throughout the entire training process, with no plateau or decline, indicating that the exploration mechanism has been operating effectively and has not been suppressed by exploitation.

The green line shows a more significant increase in entropy (from 0.16 to 0.44, a 175% increase), while the orange line is more conservative (from 0.16 to 0.38, a 138% increase). This difference is fully consistent with their performance differences in accuracy and response diversity. The high entropy of the green configuration means its policy considers a more diverse set of token choices at each decision point, without prematurely locking into a fixed pattern. This allows it to explore a broader policy space, discover better tool-use strategies, and ultimately achieve higher accuracy (52% vs 48%) and best@30 metrics (85% vs 82%). However, high entropy also implies lower output consistency, which explains why the green line has a slightly lower majority voting accuracy (maj@30) than the orange line—the 30 generated responses are more diverse, making it harder to reach a consensus through voting.

The moderate entropy increase (138%) of the orange configuration strikes a good balance between stability and exploration. Although the final entropy (0.38) is lower than that of the green line, it is still significantly higher than the initial value (a 138% increase) and far above traditional methods (where entropy typically drops below 0.05). This indicates that the orange configuration also successfully avoids entropy collapse and maintains a certain level of exploration ability, though it tends to exploit discovered high-quality strategies more than the green configuration. This strategic difference gives the orange configuration an advantage in training efficiency (about 15-20% shorter per-step time) but slightly inferior final performance.

The simultaneous increase in entropy and accuracy (entropy from 0.16 to 0.42, accuracy from 25% to 52%) breaks the traditional notion that "exploration and exploitation are a zero-sum game." It is commonly believed that increasing exploration (high entropy) sacrifices performance (because outputs are more random), and improving performance requires reducing exploration (low entropy, deterministic policy). However, ReTool's data shows that with appropriate algorithm design (Clip-Higher) and task characteristics (diverse math problems requiring diverse tool-use strategies), exploration and performance can improve together. High entropy is not random noise but the ability of the policy to adopt differentiated approaches when facing different problems, and this flexibility is a manifestation of generalization ability.

### Fine-grained Analysis of Gradient Dynamics

**The stable decline of gradient norm** indicates healthy convergence of the optimization process. The gradient norm (actor/grad_norm, measuring the magnitude of parameter update gradients) gradually decreases from an initial value of about 0.15 to a final value of about 0.08-0.11, showing a continuous downward trend with a cumulative decrease of about 30-47%. The magnitude of the gradient norm directly reflects the intensity of parameter updates—a larger gradient norm means more drastic parameter changes; a smaller gradient norm means gentler parameter changes. The downward trend indicates that the model parameters are gradually approaching a local optimum, the gradient of the loss function becomes smaller, and the required adjustment magnitude decreases. This is a sign of normal convergence in the optimization process, similar to the natural reduction in step size as gradient descent approaches the optimum.

The decline in gradient norm is not linear but exhibits stage-wise characteristics. In the early stage (steps 0-30), it declines rapidly (from 0.15 to 0.12, a 20% decrease); in the middle stage (steps 30-70), the decline slows (from 0.12 to 0.10, a 17% decrease); in the later stage (steps 70-110), it stabilizes (fluctuating between 0.08 and 0.11, with no clear trend). This stage-wise decline is synchronized with other indicators of training dynamics—the early stage is a rapid learning phase with larger parameter adjustments; the middle stage is an exploration and optimization phase with gradually decreasing adjustment magnitude; the later stage is a stable convergence phase where parameters are close to optimal, requiring only fine-tuning.

Throughout the training process, the gradient norm remains within the healthy range of 0.07-0.15, with neither vanishing gradients (< 0.01, which would cause training stagnation) nor exploding gradients (> 1.0, which would cause training divergence or numerical instability). This indicates that the backpropagation process runs smoothly, gradients can be effectively transmitted from the output layer to all parameters in the input layers, and gradient clipping (if any) is set appropriately, without excessively suppressing or amplifying gradients. The stability of the gradient norm is key to the success of large-scale model training—the backpropagation of a 32B parameter model involves gradient accumulation across hundreds of layers, and any numerical instability could lead to gradient anomalies, but the actual data shows the entire process is very smooth.

The gradient norm of the orange line is slightly higher than that of the green line (about 0.10 vs 0.09, a difference of about 10%), which seems contradictory to its more conservative policy updates and smaller KL divergence. It is generally believed that more conservative updates should correspond to smaller gradient norms. This counterintuitive phenomenon may stem from the following reasons: the gradient norm measures the magnitude of the raw, unclipped gradient, while the actual parameter updates may undergo clipping, scaling, or other transformations, and the two are not strictly linearly related. The orange configuration may use a larger gradient clipping threshold or different optimizer parameters (such as Adam's β1, β2), resulting in larger raw gradients but smaller actual updates. Alternatively, the gradient directions in the orange configuration may be more dispersed across samples (gradients from different samples partially cancel out), so while the gradient norm for individual samples is large, the combined norm of the batch gradient may be smaller. This detailed difference requires more in-depth diagnostic analysis to determine, but from a macro perspective, the gradient norms of both lines are within a healthy range, and the impact of the difference on training stability is negligible.

**The constancy and scheduling of the learning rate** reflect the conservatism of the training strategy. The learning rate (actor/lr) shows a basically constant pattern for both lines, with values maintained at the configured 1e-6 level. The learning rate curve exhibits slight sawtooth fluctuations (between 9.8e-7 and 1.02e-6). These minor fluctuations (amplitude of only 2%) may stem from numerical precision, slight differences between mini-batches, or brief perturbations introduced by periodic operations (such as checkpoint saving, validation), but essentially the learning rate is fixed, with no learning rate scheduler (such as cosine annealing or step decay) employed.

Using a fixed and relatively small learning rate (1e-6) is a reasonable training strategy. First, the model starts RL training from an SFT checkpoint, already possessing basic tool-use capabilities and language understanding. The goal of the RL phase is to fine-tune the policy to optimize rewards, not to learn entirely new abilities from scratch, so careful and cautious updates are needed to avoid destroying the knowledge learned during the SFT phase. Second, a small learning rate combined with a small batch size (ppo_mini_batch_size=64) and multiple gradient accumulations (512/64=8 mini-batches) makes policy updates very smooth, without large oscillations. Third, a fixed learning rate simplifies the training process, avoiding the additional hyperparameter tuning of learning rate scheduling, making it suitable for exploratory experiments.

From the training results, the fixed small learning rate is successful—accuracy improves from 25% to 52%, policy entropy grows from 0.16 to 0.42, and the training process is highly stable (very small KL divergence, healthy gradient norm). This indicates that a learning rate of 1e-6 is appropriate for the current configuration, neither too large to cause instability nor too small to cause slow convergence. However, for longer training (e.g., 500-1000 steps), introducing learning rate decay may be necessary to further stabilize later training and avoid oscillations near the optimum. The current training length of 110 steps is at the boundary where learning rate decay is not necessary but could be beneficial.

### Comprehensive Analysis of Rewards and Advantage Estimation

**The fluctuating upward trajectory of training rewards** fully reflects learning progress. The average score on the training set (critic/score/mean, i.e., average reward) fluctuates upward from an initial value of about 0.06 (corresponding to about 53% accuracy, since reward = 2 × accuracy - 1) to a final value of about 0.40-0.50 (corresponding to about 70-75% accuracy), a cumulative increase of about 0.34-0.44, a relative improvement of about 567-733%. This substantial absolute and relative improvement indicates that the model's problem-solving ability on the training set has been significantly enhanced, and the tool-use strategy has been effectively optimized.

The reward curve exhibits clear non-monotonic and stage-wise characteristics. In the early stage (steps 0-20), it increases rapidly (from 0.06 to 0.15, an average increase of 0.0045 per step). This is the phase where the model quickly learns basic tool-use patterns, with obvious increasing returns. In the middle stage (steps 20-70), it rises with fluctuations (from 0.15 to 0.30, an average increase of 0.003 per step, but accompanied by multiple declines). This is the phase where the model explores more complex strategies and switches between different strategies; short-term performance may decline, but the long-term trend is upward. In the later stage (steps 70-110), it accelerates upward (from 0.30 to 0.40-0.50, an average increase of 0.0025-0.005 per step). This is the phase where the model achieves a breakthrough in strategy optimization based on earlier exploration. Although the per-step improvement is similar to the middle stage, it is more stable, with fewer declines.The green line outperforms the orange line for most of the training process, with a lead ranging from 0.02 to 0.08 (corresponding to a 1-4 percentage point higher accuracy). Particularly in the later stages of training (steps 80-110), the green line stabilizes between 0.48 and 0.52 (74-76% accuracy), while the orange line remains between 0.40 and 0.45 (70-72.5% accuracy), resulting in a gap of 0.05 to 0.10 (a 2.5-5 percentage point difference in accuracy). This sustained performance advantage stems from the green configuration's higher exploration intensity (entropy 0.44 vs. 0.38) and deeper reasoning (response length 4400-4500 vs. 3800-4000 tokens). Although these characteristics incur higher computational costs (approximately 15-20% longer per step), they are worthwhile when pursuing optimal performance.

Reward volatility is most pronounced in the middle phase, with a standard deviation of approximately 0.05-0.08 (not directly given but estimable from the curves), while volatility is lower in the early and late phases (approximately 0.02-0.04). This fluctuation pattern is perfectly synchronized with the evolution of policy entropy, changes in response length, and trends in the clipping ratio, once again confirming that these are different facets of the same training dynamics. The high volatility in the middle phase reflects the model's uncertainty during active exploration—trying new tool-use patterns may temporarily degrade performance, but this is a necessary path to discovering superior strategies. The low volatility in the later phase indicates that the model's strategy is maturing, with performance improvements becoming more stable and predictable.

**The extreme value distribution of rewards** validates the design of the reward function and data quality. The minimum reward (critic/score/min) consistently remains at the lower bound of -1, with no step deviating from this value. This is expected because the reward function is designed to be binary (+1 for correct, -1 for incorrect), with no intermediate values. The persistent presence of -1 indicates that even in the later stages of training, the model still produces at least one completely incorrect response in each batch. Considering that a batch contains 512 responses (32 questions × 16 responses/question), it is reasonable to have at least 1-2 completely incorrect responses—some questions may be extremely difficult, or the sampling randomness of certain responses may lead to low-quality outputs.

The maximum reward (critic/score/max) also consistently remains at the upper bound of +1, indicating that the model can correctly answer at least some questions in each batch. Statistically, a maximum value of +1 means that at least one out of 512 responses is completely correct. Given n_resp_per_prompt=16, this is equivalent to at least one correct response among the 16 responses for at least one of the 32 questions, a fairly low threshold. In practice, as training progresses, the number of correct responses should increase significantly (the average reward increasing from 0.06 to 0.40-0.50 implies the accuracy rate increases from 53% to 70-75%), but the fact that the maximum remains stuck at +1 merely reflects the upper bound of the reward function and contains no further information.

Ideally, if data annotation included partially correct grades (e.g., +0.5 for partially correct), the reward distribution would be more granular and provide richer learning signals. However, the current binary reward design simplifies reward calculation (only requiring judgment of answer equivalence) and avoids biases that complex heuristic rules might introduce, aligning with the minimalist reward philosophy of the ReTool paper. Judging from the training results, the binary reward is sufficiently effective, and the model can learn complex tool-use strategies under this simple feedback.

**The distribution characteristics of returns and advantage functions** reveal the internal workings of the algorithm. The average return (critic/returns/mean) is completely consistent with the average reward (critic/score/mean), with the curves perfectly overlapping. This is because, in the current design, there is no discount factor (γ=1), so the return is the immediate reward, without considering the accumulation of future rewards. This design is reasonable because the generation of each response is an independent event without long-term dependencies across responses, so there is no need to introduce a discount factor to balance immediate rewards and long-term returns.

The extreme value range of returns (critic/returns/min and max) is not the expected -1 to +1, but a wider range of -3.75 to +3.75. This expanded range may originate from reward clipping, normalization, or some transformation mechanism. One possible explanation is that the system standardizes the raw rewards (subtracting the mean and dividing by the standard deviation), converting them to z-scores, thereby mapping the reward distribution from [-1, +1] to a wider range. Another possibility is that the system applies some form of reward shaping or advantage estimation transformation. Although the configuration shows no additional reward terms, the implementation details may contain implicit transformations. A third possibility is that the returns actually encompass the accumulation of multiple time steps (although the generation of a single response is a complete event, it may be internally decomposed into multiple decision points), leading to the range expansion.

The average value of the advantage function (critic/advantages) remains close to zero throughout the training process (between -0.05 and +0.05), which perfectly aligns with the design principle of the GRPO algorithm. GRPO estimates the advantage function by calculating the relative quality of each response compared to other responses in the same batch. The specific formula is A(s,a) = R(s,a) - mean(R(s,:)), where R(s,:) is the reward for all responses to the same question s. Since the advantage function is defined as the deviation from the mean, its average is mathematically bound to be close to zero (exactly zero, but may deviate slightly due to numerical errors and sampling randomness). The benefit of this relative advantage estimation is that it automatically performs baseline correction without the need to train a separate value network (critic), greatly simplifying the algorithm and reducing computational overhead.

The extreme value range of the advantage function is stable at -3.75 to +3.75, which is completely consistent with the extreme value range of returns. This further confirms that the advantage function is directly calculated based on returns (by subtracting the batch mean). This symmetrical range indicates that the batch contains both responses that are significantly better than average (advantage +3.75) and responses that are significantly worse than average (advantage -3.75), with similar magnitudes for both extremes. This suggests that the quality distribution within the batch is relatively balanced, without extreme skewness. The extreme value range of the advantage function remains stable throughout training (no trend of expansion or contraction), indicating that the heterogeneity of response quality within the batch remains consistent. The model does not exhibit convergence of all responses (narrowing advantage range) or increased quality divergence (expanding advantage range), which is a sign of healthy training.

The stability of the advantage function distribution indicates that the algorithm's relative quality estimation mechanism is functioning properly, effectively identifying the strengths and weaknesses of different responses and providing clear learning signals for the policy gradient. The application of the Token-Level Policy Gradient Loss ensures that these advantage values are fairly distributed across sequences of different lengths, preventing long sequences from receiving disproportionately large gradients due to containing more tokens. Regardless of how the response length changes (from 2500 to 4500 tokens), the distribution characteristics of the advantage function remain consistent, demonstrating the effectiveness of the length normalization mechanism.

### Comprehensive Evaluation of Training Stability and Convergence Characteristics

**The three-stage pattern of the overall training trajectory** clearly demonstrates a mature reinforcement learning convergence process. Based on a comprehensive analysis of all metrics, the 110 training steps can be divided into three distinct phases, each with its own unique dynamic characteristics and learning objectives.

**The initial exploration phase (steps 1-20)** is a golden period of rapid learning. During this phase, the validation set accuracy rapidly increases from 25% to 35% (a 0.5 percentage point improvement per step), the training set reward increases from 0.06 to 0.15 (an increase of 0.0045 per step), the response length increases from 2500 tokens to 3500 tokens (a growth of 50 tokens per step), and the policy entropy increases from 0.16 to 0.22 (a growth of 0.003 per step). All performance metrics show an accelerating upward trend with the steepest curve slopes, indicating that the model is rapidly learning basic tool-use patterns and reasoning strategies. The characteristics of the initial phase are high returns, low volatility, and fast pace—the knowledge carried over from the SFT checkpoint provides a good initialization for RL optimization, allowing early training to efficiently converge to a basically feasible strategy. The gradient norm is relatively high during this phase (0.12-0.15), indicating large parameter adjustments as the model actively corrects deficiencies in the initial strategy.

**The intermediate optimization phase (steps 20-70)** is a critical period for strategy exploration. During this phase, accuracy growth slows but volatility intensifies (increasing from 35% to 40-45%, accompanied by multiple 2-3 percentage point dips), response length continues to grow but the growth rate decreases (from 3500 tokens to a peak of 4700-4800 tokens, a growth of 24-30 tokens per step), policy entropy increases significantly (from 0.22 to 0.35, a growth of 0.0026 per step), the clipping ratio reaches its peak during training (0.02-0.03%), and the gradient norm gradually decreases (from 0.12 to 0.10). The fluctuating improvement during this phase reflects the dynamic balance between exploration and exploitation—when the model tries new tool-use strategies, short-term performance may decline (e.g., local dips at steps 30-35 and 50-55), but these explorations lay the foundation for breakthroughs in the later phase. All standard deviation metrics (accuracy, response length, sequence length variance) reach their peak during this phase, reflecting a surge in policy diversity. The two configuration lines begin to diverge during this phase, with the green line showing stronger volatility and higher entropy, while the orange line is relatively conservative and stable.

**The later stabilization phase (steps 70-110)** is the harvest period of strategy maturation. During this phase, accuracy accelerates again and tends to converge (the green line increases from 42% to 52%, the orange line from 38% to 48%), response length decreases from its peak and stabilizes (the green line stabilizes at 4400-4500 tokens, the orange line at 3800-4000 tokens), policy entropy continues to grow moderately (the green line from 0.35 to 0.44, the orange line from 0.32 to 0.38), all standard deviation metrics fall to lower levels, and the gradient norm further decreases and stabilizes (0.08-0.11). The characteristics of this phase are high performance, low volatility, and stable convergence—the model filters out the most effective strategies based on previous explorations and stabilizes them through continuous optimization. The fluctuation amplitude of the performance curves significantly decreases (from ±3% in the middle phase to ±1% in the later phase), indicating that the model's behavior becomes more consistent and predictable. The decrease in response length reflects efficiency optimization, as the model learns to reduce unnecessary redundant reasoning while maintaining high accuracy.

**The comparative strategies and trade-offs of the two configurations** provide valuable references for different application scenarios. The orange line configuration represents an efficiency-prioritized training strategy, characterized by shorter response lengths (saving approximately 12%), faster training speed (saving approximately 15-20% per step), higher throughput (approximately 3% higher), lower policy entropy (0.38 vs. 0.44), more conservative KL divergence (an order of magnitude lower), and a more stable training process (smaller fluctuations). This configuration ultimately achieves approximately 48% validation accuracy and an 82% best@30 metric. Computational cost analysis shows that completing 110 steps of training with the orange configuration requires approximately 770,000 seconds (214 hours). This configuration is suitable for scenarios with limited computational resources, a need for rapid iteration, or less stringent final performance requirements, such as rapid prototype validation, resource-constrained environments, or cost-sensitive production deployments.

The green line configuration represents a performance-prioritized training strategy, characterized by longer response lengths (approximately 12-15% more), deeper exploration (higher interaction rounds and policy entropy), more aggressive policy updates (higher KL divergence), larger performance fluctuations (significant fluctuations in the middle phase), and higher computational costs (approximately 15-20% more time per step). This configuration ultimately achieves approximately 52% validation accuracy and an 85% best@30 metric, outperforming the orange configuration by about 4 percentage points in accuracy and about 3 percentage points in best@30. Computational cost analysis shows that completing 110 steps of training with the green configuration requires approximately 935,000 seconds (260 hours). This configuration is suitable for scenarios pursuing optimal performance, with ample computational resources, or with high demands on model capability, such as competition performance optimization, academic research benchmarks, or high-end product deployments.

From a cost-benefit perspective, the orange configuration achieves 92% of the performance (48%/52%) with 82% of the computational cost, offering higher cost-effectiveness. The green configuration invests an additional 18% in computation for an 8% performance improvement, with diminishing marginal returns, but it is still worthwhile for scenarios pursuing extreme performance. The final performance gap between the two configurations (4 percentage points) is smaller than the maximum gap during training (which reached 6-8 percentage points in the middle phase). This indicates that the orange configuration achieves some degree of catch-up in the later phase, and its conservative strategy, while limiting the breadth of exploration, ensures the stable accumulation of learning effects.

**Multi-dimensional verification of training stability** proves the reliability and robustness of the system design. Throughout the training process of over 110 steps and a cumulative duration of approximately 850,000 seconds (236 hours), no serious issues such as abnormal performance drops, gradient explosions, out-of-memory errors, or numerical instability were observed. All key metrics show smooth trends without drastic jumps or discontinuities. The KL divergence consistently remains at very small values (1e-5 to 2.5e-4), policy updates are highly incremental, with small adjustments per step but significant cumulative effects. The gradient norm remains within a healthy range (0.07-0.15), with neither vanishing nor exploding gradients, ensuring stable and reliable backpropagation. GPU memory usage is highly stable (216.8-217.4 GB), with fluctuations of less than 0.3%. Even an 80% increase in response length does not lead to memory growth, demonstrating the effectiveness of FSDP and gradient checkpointing. CPU memory usage remains in the 220-228 GB range, with no continuous growth or leakage, indicating that the memory management mechanism is functioning well.

All validation steps during training are completed successfully without interruption due to timeouts, crashes, or resource exhaustion. Checkpoint saving (every 30 steps) executes normally, with an average time of approximately 50 seconds, demonstrating efficient distributed I/O. Wandb logs are continuously uploaded, and all metrics are fully recorded without data loss or upload failures. This comprehensive stability is a hallmark of a mature training system, allowing users to confidently run long training sessions without frequent manual intervention or monitoring.

### Performance Optimization Suggestions and Future Improvement Directions

Based on an in-depth analysis of training dynamics and precise identification of bottlenecks, we can propose the following targeted optimization suggestions to help users further improve training efficiency, reduce costs, or enhance final performance.

**Refinement of response length management** is the primary direction for improving training efficiency. Currently, approximately 3-5% of responses reach the 16384 token limit and are truncated. The generation time for these extremely long responses (a single response can take 70-76 minutes) dominates the total time of the Rollout phase, creating a significant bottleneck effect. It is recommended to introduce the Overlong Reward Shaping mechanism proposed in the DAPO paper, adding a mild length penalty to the reward function. A specific implementation could use piecewise linear penalties: no penalty for lengths < 8000 tokens, a penalty of -0.01 for every additional 1000 tokens between 8000-12000 tokens, and a penalty of -0.05 for every additional 1000 tokens between 12000-16384 tokens. This mild penalty will not forcefully restrict length but will guide the model to generate more concise and efficient responses while ensuring reasoning quality. The expected effects are a 10-15% reduction in average response length (from 4400 to 3700-4000 tokens), a 50% reduction in the proportion of truncated responses (from 3-5% to 1.5-2.5%), a 15-20% reduction in time per step (from 8000 seconds to 6400-6800 seconds), and a decrease in accuracy of no more than 1-2 percentage points (from 52% to 50-51%). Overall, trading a slight performance sacrifice for significant efficiency gains offers extremely high cost-effectiveness.**Intelligent Dynamic Sampling Strategy** can save computational resources while maintaining training quality. The current configuration generates a fixed 16 responses per prompt (n_resp_per_prompt=16), while the Dynamic Sampling technique proposed in the DAPO paper suggests adjusting the number of samples dynamically based on training progress and reward distribution. The specific plan is to use more samples (20-24) in the early training stage (steps 0-30) to obtain stable advantage estimates and help the model quickly establish a base policy; use standard sampling (16) in the middle stage (steps 30-80) to balance exploration and efficiency; and reduce sampling (10-12) in the later stage (after step 80) when the policy stabilizes to improve efficiency. Additionally, the number of samples can be adapted based on problem difficulty: for simple problems that the model can already answer correctly and stably (e.g., accuracy > 90% for 3 consecutive batches), reduce sampling to 8; for difficult problems the model is still struggling with (accuracy < 50%), maintain or increase sampling to 20-24. The expected effect is a 15-20% reduction in the average number of responses per step (from 512 to 410-435) while maintaining training quality (accuracy change < ±0.5%), corresponding to a 15-20% reduction in Rollout time and approximately 10-12% reduction in total training time (since Rollout accounts for 50-60% of total time).

**Dynamic Adjustment of Validation Strategy** can reduce total training time without sacrificing monitoring capability. Currently, validation is performed every 5 steps, with each validation taking approximately 10-15 minutes. Considering that performance stabilizes in the later stages of training (accuracy fluctuation in steps 80-110 is only ±1%), a dynamic validation frequency can be adopted: early stage (steps 0-30) validate every 3 steps to closely monitor progress during the rapid learning phase and promptly identify issues; middle stage (steps 30-80) validate every 5 steps to balance monitoring needs and computational overhead; later stage (after step 80) validate every 10 steps to reduce redundant evaluation. Furthermore, lightweight fast validation can be implemented (generating only 10-15 responses instead of 30, evaluating only 15-20 problems instead of all 30) for high-frequency monitoring, with a full validation performed every 15-20 steps to obtain accurate performance baselines. The expected effect is a 30-40% reduction in total validation time (from approximately 150 minutes to 90-100 minutes), decreasing its proportion of total training time from 1.7% to about 1.0%, while monitoring capability remains largely unaffected.

**Optimization of Batch Processing Efficiency** can improve throughput and GPU utilization. Currently, asynchronous waiting caused by multi-turn interactions reduces the average batch size, with the actual batch size potentially only 50-70% of the theoretical value (512). It is recommended to implement a more intelligent batch scheduling strategy: when a request is paused waiting for code execution, temporarily move it out of the active batch and fill the slot with a new request, maintaining a near-full batch state; when the paused request receives feedback, add it to the next available batch instead of waiting for its original batch. This dynamic batch reorganization requires customized modifications to the vllm engine, with high implementation complexity but significant potential benefits. The expected effect is an increase in average batch size to 75-85% of the theoretical value (up from the current 50-70%), corresponding to a 10-20% increase in GPU utilization (from the current 39% to 43-47%), a 15-25% increase in throughput (from 600 tokens/s to 690-750 tokens/s), and a 12-18% reduction in per-step Rollout time (from 2500 seconds to 2050-2200 seconds). Since this optimization requires in-depth modifications to the inference engine, it is recommended for scenarios with sufficient resources and long-term training needs.

**Space Optimization of Checkpoint Strategy** can save disk space without affecting training safety. Currently, a full checkpoint is saved every 30 steps, with each checkpoint approximately 192 GB (model 64 GB + optimizer state 128 GB). A 110-step training run produces about 4 checkpoints, totaling approximately 768 GB. Considering that most intermediate checkpoints will not be used after training is complete, a rolling save strategy is recommended: keep only the most recent 3 checkpoints (e.g., steps 90, 60, 30), automatically deleting the oldest when saving a new checkpoint (delete step 30 when saving step 120); simultaneously retain the best-performing checkpoint (determined by validation accuracy) and the final checkpoint. Additionally, checkpoint compression techniques can be explored, such as using lossy compression for optimizer states (retaining FP16 instead of FP32 precision) or saving only model weights without optimizer states (sacrificing perfect recovery capability but significantly reducing space). The expected effect is a 60-75% reduction in disk usage (from 768 GB to 192-307 GB), while training safety is almost unaffected (still recoverable to one of the most recent 3 checkpoints).

**Further Exploration of Hyperparameter Tuning** may yield additional performance gains. Based on insights from current experiments, it is recommended to focus on adjusting the following parameters: the learning rate (actor_lr) can be slightly increased to 1.5e-6 or 2e-6, using a larger learning rate in the first 50 steps to accelerate early learning, then decaying with cosine to 5e-7 from steps 50-110; this learning rate schedule may achieve higher performance within the same number of steps or reach the same performance in fewer steps. The asymmetric ratio of Clip-Higher can be further increased (e.g., clip_ratio_low=0.15, clip_ratio_high=0.35) to provide a stronger driving force for exploration, potentially further improving policy entropy and final performance. n_resp_per_prompt can be adjusted to 12 (sampling from 42.67 problems) or 20 (sampling from 25.6 problems) while keeping the total training batch size of 512 unchanged, exploring the impact of different sampling granularities on performance. It is recommended to use small-scale experiments (e.g., 30-50 steps) to quickly evaluate the effects of these parameter changes, then select the optimal configuration for full training.

**Expansion of Multimodal Tool Integration** can further enhance the model's problem-solving capability. Currently, the model can only use the code interpreter (code_interpreter), while many mathematical problems could benefit from other tools, such as symbolic computation engines (calling Mathematica or SymPy) for complex algebraic derivations, numerical optimizers for solving constrained optimization problems, or visualization tools for generating charts to aid in understanding geometric problems. It is recommended to expand the tool set and include examples of multi-tool usage in the training data, allowing the model to learn to select the most suitable tool combination for different types of problems. This multi-tool strategy could potentially further improve the accuracy on AIME 2025 from the current 52% to 60-65%, especially on specific domain problems such as geometry and probability/statistics.

**Feasibility Assessment of Long-Term Training** suggests room for further performance improvement. The current training still shows an upward trend after 110 steps (the green line is still rising in steps 100-110, without an obvious plateau), indicating that the model has not fully converged, and continued training may yield additional gains. According to the ReTool paper, training to 400 steps can achieve 67% accuracy (compared to the current 52% at 110 steps, there is still room for a 15 percentage point improvement). It is recommended to extend training to 200-300 steps if resources permit, with an expected accuracy of 58-63%. At the same time, monitor the validation set for signs of overfitting (training set accuracy continues to rise while validation set accuracy stagnates or declines); if overfitting is detected, training should be stopped promptly, or regularization techniques should be introduced (such as increasing the KL penalty coefficient, reducing the learning rate, or increasing dropout).

## Detailed Explanation of RL Training Recipe Parameters

The parameter configuration for reinforcement learning training scripts is more complex than that for the SFT stage, involving multiple dimensions such as policy optimization, reward calculation, and multi-turn interaction. Understanding these parameters is crucial for fully leveraging the potential of the ReTool method.

Data and model path configurations define the basic resources for training. `train_files` points to the DAPO-Math-17k dataset, a large-scale training corpus containing 1.79 million math problems. `test_files` in this configuration points to aime_2025, used for periodic evaluation during training. The `model_path` parameter points to the model checkpoint that was trained in the SFT stage and converted to Hugging Face format; this model already possesses basic tool-use capabilities, and RL training will further optimize it on this basis. `tool_config_path` specifies the configuration file path for the SandboxFusion tool, defining various parameters of the code execution environment.

Algorithm-related parameters control the core mechanisms of reinforcement learning. `adv_estimator` is set to `grpo` (Group Relative Policy Optimization), which is the foundational component of the DAPO algorithm, responsible for optimizing the policy through relative advantage estimation. DAPO adds four key improvements on top of the GRPO framework (Clip-Higher, Dynamic Sampling, Token-Level Loss, and Overlong Reward Shaping), making it particularly suitable for long chain-of-thought scenarios. Compared to the traditional PPO algorithm, GRPO does not require training a separate critic model; instead, it estimates advantages based on the relative quality of different responses within the same batch, significantly simplifying the training process and improving sample efficiency. The `use_kl_in_reward` and `kl_coef` parameters control whether a KL divergence penalty term is added to the reward; both are set to `False` and `0.0` here, indicating that no explicit KL constraint is used, relying entirely on DAPO's clipping mechanism to control the magnitude of policy updates. `clip_ratio_low` and `clip_ratio_high` are set to 0.2 and 0.28 respectively; this asymmetric clipping range embodies DAPO's Clip-Higher strategy—providing more room for upward policy updates (0.28 > 0.2), encouraging exploration of high-reward patterns while preventing performance degradation.

Sequence generation and batch configuration parameters determine the model's inference method. `max_turns` is set to 8, allowing the model up to 8 rounds of interaction loops involving thinking and tool calls. This setting provides ample space for deep exploration of complex problems, allowing the model to repeatedly verify hypotheses and adjust strategies. `max_prompt_length` is set to 2048, and `max_response_length` is set to 16384; the difference between the two reflects the characteristics of the ReTool method: input problems are usually short, but response sequences containing multi-turn interactions and code execution results can be very long. `train_batch_size` is set to 512, which is a relatively large batch, but it is actually achieved through `n_resp_per_prompt=16`, i.e., generating 16 different responses for each problem and then comparing their relative quality. `ppo_mini_batch_size` is set to 64, meaning that during policy updates, the 512 samples are divided into multiple mini-batches for gradient descent.

Performance optimization parameters are crucial for efficiently utilizing GPU resources. `infer_tp` is set to 4, indicating the use of tensor parallelism in the vllm engine during inference, splitting the model across 4 GPUs for fast generation. `train_sp` is set to 8, indicating the use of Ulysses sequence parallelism during training, splitting long sequences across all 8 GPUs for processing. `offload` is set to `True`, enabling CPU offloading of parameters and optimizer states, which is necessary for training a 32B parameter model with limited GPU memory. Although CPU offloading introduces some speed overhead, it makes it possible to complete the entire training process on a single server.

Multi-turn interaction configuration embodies the core characteristics of ReTool. `multi_turn.enable` enables multi-turn dialogue mode, with `max_user_turns` and `max_assistant_turns` both set to 8, corresponding to the `max_turns` parameter. `tool_config_path` points to the configuration file for SandboxFusion, defining the interface and execution environment for tool calls. `format` is set to `hermes`, a standardized tool call format ensuring that tool call requests generated by the model can be correctly parsed and executed by SandboxFusion. The `rollout` mode is set to `async`, allowing multiple inference requests to execute concurrently, fully leveraging the high throughput of the vllm engine.

Sampling strategy parameters affect the diversity of responses. During training, `n_resp_per_prompt=16` generates 16 different responses for each problem; the diversity of these responses provides a rich basis for comparison in DAPO's relative advantage estimation. Although the current configuration uses a fixed number of samples, DAPO's Dynamic Sampling technique allows this parameter to be adjusted dynamically during training as needed. During validation, `n_resp_per_prompt_val=30` generates more responses, using sampling parameters of `top_p=0.6` and `temperature=1.0` to maintain some randomness while avoiding generating overly absurd answers. `gpu_memory_utilization` is set to 0.9, meaning the vllm engine can use 90% of the GPU memory, reserving sufficient KV cache space for inference.

Training control parameters determine the pace and monitoring method of training. `val_before_train` is set to `True`, performing a validation before training starts to establish a performance baseline. `log_val_generations` is set to 100, meaning the first 100 generated samples during validation are logged to wandb, facilitating manual inspection of the model's reasoning process and tool usage. `save_freq` is set to 30, saving a checkpoint every 30 training steps; `test_freq` is set to 5, performing validation every 5 steps. `total_epochs` is set to 1, as the DAPO-Math-17k dataset is already large enough that a single pass can yield significant performance improvements. `actor_lr` is set to 1e-6, a relatively small learning rate because the model has already learned basic capabilities during the SFT stage, and the RL stage only requires fine-tuning.

## References

- [DAPO Paper: Large-Scale LLM Reinforcement Learning System](https://arxiv.org/pdf/2503.14476)
- [ReTool Paper: Multi-Turn Dialogue and Code Sandbox for Improving Mathematical Reasoning](https://arxiv.org/pdf/2504.11536)
- [verl Official Repository](https://github.com/volcengine/verl/)
- [SandboxFusion Official Repository](https://github.com/bojieli/SandboxFusion)
- [Qwen2.5 Model](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct)
- [AIME 2024 Dataset](https://huggingface.co/datasets/BytedTsinghua-SIA/AIME-2024)
- [DAPO-Math-17k Dataset](https://huggingface.co/datasets/BytedTsinghua-SIA/DAPO-Math-17k)

## Frequently Asked Questions

### What to do if GPU memory is insufficient?

If you encounter insufficient GPU memory, you can try the following solutions:

1. Reduce the micro-batch size (micro_batch_size_per_gpu)
2. Enable the CPU offload option
3. Reduce the sequence length (max_length)
4. Use gradient accumulation to simulate a larger batch

### How to resume training after interruption?The verl framework supports resuming training from checkpoints. Set the `resume_mode` and `resume_from_path` parameters in the training script. There are two common recovery modes:

**Method 1: Specify a specific checkpoint (recommended)**

If training is interrupted at step 54, you can resume from the checkpoint at step 50:

```bash
bash recipe/retool/run_qwen2-32b_dapo.sh \
    trainer.resume_mode=resume_path \
    trainer.resume_from_path=recipe/retool/checkpoint/qwen2.5-32b_dapo_with_tool/global_step_50
```

This method requires explicitly specifying the checkpoint path containing `global_step_`. Training will continue from this checkpoint, and the global step will be automatically set to 50.

**Method 2: Automatically resume the latest checkpoint**

If you want the system to automatically find and resume the latest checkpoint, use the `auto` mode:

```bash
bash recipe/retool/run_qwen2-32b_dapo.sh \
    trainer.resume_mode=auto
```

This method automatically searches for the latest checkpoint in the `default_local_dir` directory and resumes from it. If no checkpoint is found, training will start from scratch.

The training script will automatically load the model weights, optimizer state, data loader state, and training progress, ensuring seamless continuation of training.

### How to evaluate model performance?

Whether training is complete or in progress, you can evaluate specific checkpoints. Evaluation consists of two steps: first, merge the model, then run the evaluation.

**Step 1: Merge model checkpoints**

Since training uses FSDP to save model shards, you need to merge the checkpoints into the Hugging Face standard format before evaluation. For example, to evaluate the checkpoint at step 40:

```bash
python3 -m verl.model_merger merge \
    --backend fsdp \
    --local_dir qwen2.5-32b_dapo_with_tool/global_step_40/actor/ \
    --target_dir qwen2.5-32b_dapo_with_tool/global_step_40/actor/huggingface
```

Parameter explanation:
- `--backend fsdp`: Specifies the source checkpoint format as FSDP
- `--local_dir`: Path to the FSDP sharded checkpoint (usually the `global_step_X/actor/` directory)
- `--target_dir`: Save path for the merged model (recommended to use the `/huggingface` subdirectory)

The merging process reads all shard files, reconstructs the complete model weights, and saves them in the Hugging Face Transformers standard format. This process requires sufficient disk space to store the merged model files.

**Step 2: Run evaluation**

After merging, use the evaluation script provided by verl, input the test data and the path to the merged model. The script will automatically run inference and calculate metrics such as accuracy. Evaluation can be performed on any checkpoint during training, making it easy to track model performance at different training stages.

### How to configure multi-machine training?

For multi-machine training, you need to configure the same environment on each machine and set the correct number of nodes (nnodes) and node rank in the training script. verl uses PyTorch's distributed training mechanism, requiring the master node's address and port for inter-node communication.

The statistical distribution of the advantage function (critic/advantages) remains relatively consistent across steps. The average advantage value fluctuates between 0.013 and 0.054, close to zero, which aligns with DAPO's design inherited from GRPO—the advantage function measures performance relative to the batch average, so its mean should theoretically be near zero. The extreme values of the advantage function are stable between -3.75 and +3.75. This symmetric range indicates that the batch contains both significantly above-average and below-average responses, providing clear learning signals for policy gradients. The application of Token-Level Policy Gradient Loss ensures that these advantage values are fairly distributed across sequences of different lengths, preventing long sequences from receiving disproportionately large gradients due to containing more tokens. The stability of the advantage function distribution indicates that the algorithm's relative quality estimation mechanism is functioning correctly, effectively identifying the quality of different responses.

---

## 中文

# ReTool：使用多轮对话和代码沙箱提升大语言模型数学推理能力

## 概述

ReTool 是一种创新的强化学习方法，旨在通过多轮对话和代码沙箱执行来显著提升大语言模型在数学推理任务上的表现。该方法的核心思想是让模型学会使用工具（特别是代码执行环境）来辅助数学问题的求解，而不是仅依赖于语言模型自身的推理能力。通过有监督微调（SFT）和强化学习（RL）两个阶段的训练，ReTool 能够教会模型何时以及如何调用代码沙箱来验证计算结果、测试假设或探索问题空间。

本文档详细记录了 ReTool 方法的完整复现步骤，包括环境配置、模型训练以及评估过程。该复现基于 verl 框架，使用 Qwen2.5-32B-Instruct 作为基础模型，并在 AIME 2024 数学竞赛数据集上进行训练。整个训练过程分为两个主要阶段：首先通过有监督微调使模型学会基本的工具使用模式，然后通过强化学习进一步优化模型在实际问题求解中的表现。

## 硬件与软件要求

### 硬件配置

复现 ReTool 需要强大的 GPU 计算资源。推荐的硬件配置包括以下两种方案：

第一种方案是使用一台配备 8 卡 H200 GPU 的服务器。H200 GPU 具有较大的显存容量和强大的计算能力，能够高效地进行大规模模型的训练。单台服务器的配置简化了分布式训练的复杂性，特别适合初次尝试复现的研究者。

第二种方案是使用 2 台 8 卡 A100 或 H100 GPU 的服务器。这种配置提供了更大的总计算能力，但需要配置多机分布式训练。如果选择这种方案，建议使用原始的 verl 框架而非修改版本。

### 软件环境

推荐使用以下软件环境组合以获得最佳的兼容性和性能：

- **CUDA 版本**：12.6.2
- **操作系统**：Ubuntu 24.04 LTS
- **Python 版本**：3.13

这些版本的选择基于对最新深度学习框架的支持以及稳定性考虑。CUDA 12.6.2 提供了对最新 GPU 架构的优化支持，Ubuntu 24.04 是长期支持版本，确保了系统的稳定性，而 Python 3.13 则提供了最新的语言特性和性能改进。

## 环境搭建

### 下载 verl 框架

verl 是一个高效的强化学习框架，专门为大语言模型的 RLHF（Reinforcement Learning from Human Feedback）训练而设计。对于单台 8 卡 H200 服务器的配置，建议使用经过修改的版本：

```bash
git clone https://github.com/bojieli/verl
```

该修改版本针对单台 8 卡 H200 的配置进行了优化。如果使用多机配置，则应该使用原始的 verl 框架：

```bash
git clone https://github.com/volcengine/verl/
```

### 安装 Miniconda

Miniconda 是一个轻量级的 Python 环境管理工具，能够方便地创建和管理独立的 Python 环境，避免依赖冲突。安装步骤如下：

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

安装过程中按照提示完成配置。安装完成后，建议重新启动终端以使环境变量生效。

### 创建 Conda 环境

为了避免与系统中其他项目的依赖冲突，创建一个专门用于 ReTool 训练的 Conda 环境：

```bash
conda create -n verl python==3.13
conda activate verl
```

激活环境后，所有后续的包安装和命令执行都将在这个隔离的环境中进行。

### 安装依赖包

进入 verl 目录并安装所需的依赖包。这个过程包括安装基础依赖、CUDA 相关依赖以及 verl 本身：

```bash
cd verl
pip install -r requirements.txt
pip install -r requirements-cuda.txt
pip install -e .
```

其中 `requirements.txt` 包含了基础的 Python 包依赖，`requirements-cuda.txt` 包含了 CUDA 相关的深度学习框架和库，而 `pip install -e .` 则以可编辑模式安装 verl 框架本身，方便后续的开发和调试。

### 下载基础模型

ReTool 使用 Qwen2.5-32B-Instruct 作为基础模型。这是一个经过指令微调的大语言模型，具有较强的指令遵循能力和推理能力。首先创建模型存储目录，然后使用 Hugging Face CLI 下载模型：

```bash
mkdir -p /root/verl/recipe/retool/model/
huggingface-cli download Qwen/Qwen2.5-32B-Instruct \
    --local-dir /root/verl/recipe/retool/model/Qwen2.5-32B-Instruct \
    --local-dir-use-symlinks False
```

参数 `--local-dir-use-symlinks False` 确保文件被完整复制而非使用符号链接，这在某些训练场景下更加稳定可靠。

### 下载训练数据

ReTool 的有监督微调阶段使用 AIME 2024 数据集。首先需要运行预处理脚本，然后下载数据集：

```bash
python3 recipe/retool/retool_sft_preprocess.py
huggingface-cli download --repo-type dataset --resume-download \
    BytedTsinghua-SIA/AIME-2024 \
    --local-dir /dataset/BytedTsinghua-SIA/AIME_2024
```

预处理脚本会准备数据集的格式，使其符合训练框架的输入要求。参数 `--resume-download` 允许在网络中断时继续下载，提高了下载的健壮性。

## 有监督微调（SFT）

### 启动训练

有监督微调是 ReTool 训练的第一个阶段，目的是让模型学会基本的工具使用模式和多轮对话格式。进入配方目录并执行训练脚本：

```bash
cd recipe/retool
bash run_qwen2-32b_sft.sh
```

### 配置 Wandb

训练开始时，系统会提示配置 Weights & Biases（wandb），这是一个流行的机器学习实验跟踪工具。首先需要在 wandb.ai 注册账号，然后按照提示操作：

1. 选择"Use an existing W&B account"（选项 2）
2. 访问 https://wandb.ai/authorize 获取 API key
3. 将 API key 粘贴到终端提示符中

配置完成后，训练过程的所有指标都会自动上传到 wandb 平台，可以通过网页界面实时监控训练进度和模型性能。

### 训练过程解析

训练开始后，系统会显示详细的配置信息和训练参数。根据数据集大小和批次设置，训练过程包括 6 个 epoch，每个 epoch 62 个 steps，总共 372 个训练步骤。

训练配置的关键参数包括：

- **批次大小**：训练批次大小为 16，每个 GPU 的微批次大小为 4
- **序列长度**：最大序列长度为 16384，支持长文本的多轮对话
- **优化器配置**：学习率为 1e-5，使用 Adam 优化器，权重衰减为 0.01
- **并行策略**：使用 Ulysses 序列并行，并行大小为 4，有效处理长序列
- **模型策略**：使用 FSDP（Fully Sharded Data Parallel）进行分布式训练，并启用梯度检查点以节省显存

训练过程中会输出每个步骤的损失值、学习率和执行时间。典型的训练日志如下：

```
step:1 - train/loss:0.8078852891921997 - train/lr(1e-3):0.0002702702702702703 - train/time(s):14.796027898788452
step:2 - train/loss:0.7787683010101318 - train/lr(1e-3):0.0005405405405405405 - train/time(s):7.293778896331787
step:3 - train/loss:0.7899439334869385 - train/lr(1e-3):0.0008108108108108109 - train/time(s):6.083798885345459
```

可以观察到，初始步骤由于各种初始化操作耗时较长（约 15 秒），但后续步骤稳定在每步 6-7 秒左右。随着训练的进行，损失值逐渐下降，表明模型正在学习任务。

到第 3 个 epoch 时，损失已经显著降低：

```
step:127 - train/loss:0.1943996697664261 - train/lr(1e-3):0.00832235736719411 - train/time(s):6.062393665313721
step:128 - train/loss:0.1821298599243164 - train/lr(1e-3):0.008287170670328432 - train/time(s):6.20814323425293
```

学习率采用 cosine 调度策略，在训练过程中逐渐衰减，这有助于模型在训练后期更加稳定地收敛。


### 训练时长估算

根据实际测试，在 8 卡 H200 GPU 配置下，平均每个 step 耗时约 7 秒。完成全部 372 个 steps 大约需要 45 分钟。实际时间可能因 GPU 配置有所不同。

训练完成后，终端会输出总结信息，可以点击 wandb 链接来查看训练过程的详细信息。

```
Total time for train steps: 2627.97s
Final validation metrics: {'val/loss': 0.019425522536039352}
Epoch 6/6:  98%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████▎  | 61/62 [09:53<00:09,  9.73s/it]
wandb:
wandb: Run history:
wandb:     train/loss █▇▇▇▅▅▅▅▅▄▄▄▄▄▂▂▂▂▃▂▂▂▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁
wandb: train/lr(1e-3) ▄▅▆▆██████▇▇▇▇▆▆▆▆▆▆▄▄▄▄▃▃▃▃▃▂▂▂▂▁▁▁▁▁▁▁
wandb:  train/time(s) ▅▃▆▆▃▃▂█▁▃▆▆▁▆▄▅▂▃▄▂▅▁▄▅▄▇▄▁▂▂▂▂▄▂▃▄▄█▁▅
wandb:       val/loss ▁
wandb:
wandb: Run summary:
wandb:     train/loss 0.01913
wandb: train/lr(1e-3) 0
wandb:  train/time(s) 6.46921
wandb:       val/loss 0.01943
wandb:
wandb: 🚀 View run multiturn-sft-qwen-2.5-32b-instruct at: https://wandb.ai/bojieli-pine-ai/boj-multiturn-sft/runs/7zndjepf
wandb: ⭐️ View project at: https://wandb.ai/bojieli-pine-ai/boj-multiturn-sft
wandb: Synced 5 W&B file(s), 0 media file(s), 0 artifact file(s) and 0 other file(s)
```

训练完成后，模型检查点会保存在指定的目录中（默认为 `/root/verl/recipe/retool/checkpoint/multiturn-sft-qwen-2.5-32b-instruct`），用于后续的强化学习阶段。

### SFT 训练配方参数详解

理解训练脚本的参数配置对于调整训练过程和优化性能至关重要。SFT 训练脚本通过 torchrun 启动分布式训练，其中 nnodes 和 nproc_per_node 参数分别指定了节点数量和每个节点的进程数。对于单台 8 卡 H200 服务器，这两个参数分别设置为 1 和 8，意味着在单个节点上使用全部 8 张 GPU 进行训练。standalone 选项表示不需要配置主节点地址，简化了单机训练的启动流程。

数据相关的参数决定了模型的输入处理方式。train_files 和 val_files 参数指定训练和验证数据的路径，这里使用的是 ReTool-SFT 数据集的 parquet 格式文件。max_length 参数设置为 16384，这是一个相当长的序列长度，允许模型处理包含多轮对话和代码执行结果的复杂交互序列。train_batch_size 设置为 32，表示每个训练步骤处理 32 个样本，而 micro_batch_size_per_gpu 设置为 4，意味着每张 GPU 实际一次处理 4 个样本，通过梯度累积实现更大的有效批次大小。这种设计在有限的 GPU 显存下平衡了训练稳定性和效率。

多轮对话的配置是 ReTool 训练的关键特性。data.multiturn.enable 参数启用多轮对话模式，messages_key 和 tools_key 参数分别指定数据集中对话消息和工具定义的字段名称。这使得模型能够学习在对话过程中适时调用工具的能力。模型通过观察示例数据中的消息序列和工具调用模式，逐渐理解何时需要使用工具、如何构造工具调用请求以及如何解释工具返回的结果。

模型和训练策略参数控制了模型的加载和优化方式。partial_pretrain 参数指向 Qwen2.5-32B-Instruct 基础模型的路径，模型将从这个预训练检查点开始微调。strategy 参数设置为 fsdp（Fully Sharded Data Parallel），这是一种先进的分布式训练策略，将模型参数、梯度和优化器状态分片到多个 GPU 上，大幅降低单卡显存需求。

序列并行和优化参数进一步提升了训练效率。ulysses_sequence_parallel_size 设置为 4，表示使用 Ulysses 序列并行算法将长序列切分到 4 张 GPU 上并行处理。这对于处理 16384 长度的序列至关重要，避免了单卡显存的瓶颈。use_remove_padding 参数启用动态填充移除优化，只对实际的有效 token 进行计算，跳过填充 token，显著提升了训练效率，特别是在处理变长序列时效果明显。

实验管理参数帮助组织和追踪训练过程。project_name 和 experiment_name 用于在 wandb 平台上标识训练任务，便于后续查看和对比不同实验的结果。default_local_dir 指定检查点的本地保存路径，训练过程中会定期保存模型状态。logger 参数设置为同时使用控制台和 wandb 两种日志方式，确保既能实时观察训练进度，又能通过 wandb 网页界面进行深入分析。total_epochs 设置为 6，表示完整遍历训练数据集 6 次。

## 强化学习环境：SandboxFusion

### 环境简介

SandboxFusion 是 ReTool 强化学习阶段使用的代码执行沙箱环境。它提供了一个安全、隔离的 Python 代码执行环境，允许模型在训练过程中实际执行代码并获得执行结果的反馈。这种交互式的学习方式是 ReTool 能够有效提升模型工具使用能力的关键。

### 安装步骤

下载 SandboxFusion 的修改版本，该版本支持在本地运行 128 个并行 worker，满足大规模训练的需求：

```bash
git clone https://github.com/bojieli/SandboxFusion
cd SandboxFusion/
```

为 SandboxFusion 创建独立的 Conda 环境。注意这里使用 Python 3.12 而非 3.13，这是为了与 SandboxFusion 的依赖保持最佳兼容性：

```bash
conda create -n sandbox python==3.12
conda activate sandbox
```

使用 Poetry 安装依赖。Poetry 是一个现代化的 Python 依赖管理工具，能够更好地处理复杂的依赖关系：

```bash
pip install poetry
poetry install
```

新建一个用于代码执行沙盒的 conda 环境，并安装常见的科学计算、数学相关库。

```bash
conda create -n sandbox-runtime -y python=3.11
conda activate sandbox-runtime
pip install -r ./requirements.txt --ignore-requires-python

# for NaturalCodeBench python problem 29
python -c "import nltk; nltk.download('punkt')"

# for CIBench nltk problems
python -c "import nltk; nltk.download('stopwords')"
```

启动 SandboxFusion 服务（默认并行 128 个进程，如果机器配置较低，可修改 Makefile）。该服务会监听来自训练进程的代码执行请求：

```bash
make run-online
```

为了确保服务能够正常执行科学计算代码，建议使用如下命令测试：

```bash
curl 'http://localhost:8080/run_code' \
  -H 'Content-Type: application/json' \
  --data-raw '{"code": "import sympy\n\n# Define symbolic variables\nx, y = sympy.symbols(\"x y\")\n\n# Basic algebra\nexpr = x**2 + 2*x + 1\nfactored = sympy.factor(expr)\nprint(f\"Expression: {expr}\")\nprint(f\"Factored: {factored}\")\n\n# Solve equation\nsolution = sympy.solve(x**2 - 4, x)\nprint(f\"Solution to x^2 - 4 = 0: {solution}\")\n\n# Calculus\nderivative = sympy.diff(x**3 + 2*x**2 + x, x)\nprint(f\"Derivative of x^3 + 2x^2 + x: {derivative}\")\n\n# Integration\nintegral = sympy.integrate(x**2, x)\nprint(f\"Integral of x^2: {integral}\")\n\nprint(\"\\nSympy test completed successfully!\")", "language": "python"}'
```

如果服务运行正常，将输出下述结果。

```
{"status":"Success","message":"","compile_result":null,"run_result":{"status":"Finished","execution_time":0.2835578918457031,"return_code":0,"stdout":"Expression: x**2 + 2*x + 1\nFactored: (x + 1)**2\nSolution to x^2 - 4 = 0: [-2, 2]\nDerivative of x^3 + 2x^2 + x: 3*x**2 + 4*x + 1\nIntegral of x^2: x**3/3\n\nSympy test completed successfully!\n","stderr":""},"executor_pod_name":null,"files":{}}
```

服务正常启动后，强化学习训练进程就可以通过 API 调用 SandboxFusion 来执行模型生成的代码，并将执行结果作为奖励信号反馈给训练过程。

## 强化学习训练（RL）

### 准备 SFT 模型检查点

完成有监督微调后，需要将 FSDP 格式的检查点转换为 Hugging Face 标准格式，以便在强化学习阶段使用。verl 框架提供了模型合并工具来完成这一转换过程。SFT 训练共 372 个步骤，使用最后一个检查点进行转换：

```bash
python3 -m verl.model_merger merge \
    --backend fsdp \
    --local_dir /root/verl/recipe/retool/checkpoint/multiturn-sft-qwen-2.5-32b-instruct/global_step_372 \
    --target_dir /root/verl/recipe/retool/checkpoint/multiturn-sft-qwen-2.5-32b-instruct/global_step_372/huggingface
```

这个转换过程会将分布式训练中分片保存的模型权重合并为单一的模型文件，并转换为 Hugging Face Transformers 库的标准格式。转换后的模型将保存在指定的 `huggingface` 子目录中，可以直接用于后续的强化学习训练或推理评估。需要注意的是，这个过程需要足够的磁盘空间来存储转换后的模型文件。

### ReTool 训练原理

在深入 RL 训练步骤之前，有必要理解 ReTool 方法的核心原理。根据 [ReTool 论文](https://arxiv.org/pdf/2504.11536)，ReTool 的创新之处在于将工具使用能力整合到大语言模型的推理过程中，使模型能够像人类数学家一样利用计算工具来辅助问题求解。传统的推理模型（如 DeepSeek R1 和 OpenAI o1）虽然在纯文本推理任务上表现出色，但在需要精确数值计算或符号操作的场景中仍然存在明显局限。文本推理过程容易产生累积误差和计算错误，而代码解释器通过提供形式化和可执行的接口，能够实现精确的数值验证，显著减少了这类问题。

ReTool 的训练流程分为两个关键阶段。在有监督微调（SFT）阶段，模型通过学习高质量的代码增强推理轨迹来掌握基本的工具调用模式。数据构建流程首先从开源数据集（如 OpenThoughts）收集数学推理数据，经过人类专家和 DeepSeek-R1 的双重验证筛选后，使用结构化提示模板将文本推理过程转换为代码集成的推理数据。这个转换过程会将原始思考过程中可以通过代码执行获益的手工计算步骤替换为相应的代码片段及其执行结果。转换后的数据经过格式验证和答案验证两个阶段，确保语法一致性和结果正确性。SFT 阶段使用 swordfaith/ReTool-SFT-multi-turn 数据集，该数据集包含 2000 个数学问题及其详细的多轮对话解答过程，每个样本都标注了 tool_call 属性。通过这种监督学习，模型建立了工具使用的基础认知框架。

强化学习阶段则采用 DAPO（Decoupled Clip and Dynamic Sampling Policy Optimization）算法，这是专门为大规模长思维链 RL 场景设计的优化方法。根据 [DAPO 论文](https://arxiv.org/pdf/2503.14476)，该算法在 Qwen2.5-32B 模型上达到了 AIME 2024 的 50 分准确率，超越了 DeepSeek-R1-Zero-Qwen-32B 的 47 分，且仅使用了后者 50% 的训练步数。DAPO 在 GRPO（Group Relative Policy Optimization）的基础上引入了四项关键技术创新，专门解决长思维链 RL 训练中的熵崩溃、奖励噪声和训练不稳定等问题。

第一项技术是 Clip-Higher 策略，旨在促进系统多样性并避免熵崩溃。传统 PPO 使用对称的裁剪范围（如 1-ε 到 1+ε），但在长思维链场景中，这种对称裁剪会导致模型过早收敛到确定性策略，丧失探索能力。Clip-Higher 通过使用不对称的裁剪区间（clip_ratio_low=0.2, clip_ratio_high=0.28），为向上的策略更新提供更大的空间，鼓励模型探索高奖励的响应模式，同时严格限制向下的更新以防止性能退化。这种设计在保持训练稳定性的同时，有效维持了策略的探索性，避免了熵过早崩溃到接近零的状态。

第二项技术是动态采样（Dynamic Sampling），用于提高训练效率和稳定性。在标准 GRPO 中，每个问题固定生成 G 个响应用于相对优势估计。动态采样根据训练进程和奖励分布动态调整每个问题的采样数量，在训练初期使用更多采样以获得稳定的优势估计，在训练后期当策略趋于稳定时减少采样以提高效率。第三项技术是 Token-Level Policy Gradient Loss，这在长思维链场景中至关重要。传统方法对整个序列使用单一的奖励信号，而 DAPO 将损失函数在 token 级别进行归一化，确保长短序列获得公平的梯度权重，避免超长序列主导训练过程。第四项技术是 Overlong Reward Shaping，通过对超长响应施加轻微的长度惩罚来减少奖励噪声。这个机制不是硬性限制长度，而是在奖励函数中引入温和的负反馈，引导模型在保证推理质量的前提下生成更简洁高效的响应。

ReTool 的核心创新在于支持交织的实时代码执行的 rollout 机制。在生成过程中，策略模型与代码沙箱协作，动态产生混合内容——包括文本推理、代码片段和实时的解释器反馈。具体而言，模型使用特定的标签（`<code></code>`）标记生成的代码边界。当检测到代码终止触发器（`</code>`）时，生成暂停，解析后的代码被发送到沙箱执行。沙箱的输出（成功结果或错误消息）被填充在 `<interpreter></interpreter>` 标签中并反馈给模型，模型继续生成推理轨迹，最终产生形如 `[文本₁ ⊕ 代码₁ ⊕ 反馈₁ ⊕ ... ⊕ 答案]` 的混合推理序列。

奖励设计采用了极简主义的准则驱动方法。ReTool 使用基于规则的准确性奖励，当预测答案与标准答案等价时获得 +1 奖励，否则获得 -1 奖励。这种简化的奖励设计旨在缓解奖励欺骗问题，并在仅基于结果反馈的情况下促进更多样化的问题解决行为。论文中明确指出不考虑代码可执行性奖励，而是让模型通过结果反馈自主学习何时以及如何调用工具。这种设计理念的关键在于相信模型能够通过足够的探索，自主发现最优的工具调用模式，而不需要人为设定工具使用的先验规则。

实验结果充分验证了 ReTool 方法的有效性。在 AIME 2024 数据集上，基于 Qwen2.5-32B-Instruct 的 ReTool 模型仅用 400 个训练步骤就达到了 67.0% 的准确率，而文本 RL 基线即使经过 1080 个训练步骤也只达到 40.0% 的准确率。这一显著差距表明，显式地将工具使用建模为决策过程的一部分，不仅推动了模型推理能力的边界，还大幅提升了训练效率。在扩展设置下，ReTool-32B 达到了 72.5% 的准确率，超越 OpenAI 的 o1-preview 模型 27.9 个百分点。

ReTool 方法的另一个重要特点是其多轮交互机制和涌现行为。与传统的单次生成不同，ReTool 允许模型进行多轮思考和工具调用。模型可以先提出假设，然后通过代码验证假设的正确性，根据验证结果调整推理方向，再进行下一轮探索。特别值得注意的是，模型在 RL 训练过程中展现出了代码自我修正的涌现能力。当生成的代码因函数未定义等错误而执行失败时，模型能够识别错误并自主生成修正后的可执行代码，这种元认知能力的出现标志着一个"顿悟时刻"（aha moment），表明模型已经掌握了自适应工具使用的能力。

训练过程中的行为演化分析揭示了几个关键趋势。首先，响应长度在 RL 训练后减少了约 40%（从 10k token 降至 6k token），这表明代码驱动的推理方法通过用简洁的代码替代复杂的计算过程，显著提升了推理 token 的利用效率。其次，代码比率、代码行数和正确代码数量在训练过程中持续上升，代码调用时机也逐渐提前，这些趋势共同表明模型的代码使用能力和策略性工具使用能力在不断发展。此外，代码用途分析显示，RL 训练后模型的代码目的变得更加多样化，从主要的计算和验证扩展到更广泛的问题类型，展现了自适应工具选择的元认知发展。

### 准备 RL 训练数据

强化学习阶段的核心训练数据是 BytedTsinghua-SIA/DAPO-Math-17k 数据集。这是一个大规模的数学问题集合，包含 179 万个数学问题及其答案，涵盖了从基础算术到高等数学的广泛主题。数据集的规模确保了模型能够在多样化的问题场景中学习和泛化工具使用策略。下载该数据集：

```bash
huggingface-cli download --repo-type dataset --resume-download \
    BytedTsinghua-SIA/DAPO-Math-17k \
    --local-dir /dataset/BytedTsinghua-SIA/DAPO-Math-17k
```

评估数据集使用 BytedTsinghua-SIA/AIME-2024，这是美国数学邀请赛（American Invitational Mathematics Examination）2024 年的试题集，包含 30 个高难度数学竞赛问题。AIME 是美国最具挑战性的高中数学竞赛之一，其题目需要深度推理和创造性的问题解决能力。该数据集应该在 SFT 阶段已经下载，位于 `/dataset/BytedTsinghua-SIA/AIME_2024` 目录。如果需要重新下载：

```bash
huggingface-cli download --repo-type dataset --resume-download \
    BytedTsinghua-SIA/AIME-2024 \
    --local-dir /dataset/BytedTsinghua-SIA/AIME_2024
```

值得注意的是，RL 训练数据集的规模远大于 SFT 阶段。这种设计是有意为之的：SFT 阶段通过少量高质量示例建立基础能力，而 RL 阶段则通过大规模数据的探索学习来提升模型的泛化能力和策略优化。DAPO-Math-17k 的 179 万问题为模型提供了充足的探索空间，使其能够在各种数学问题场景中发现有效的工具使用模式。

### 启动强化学习训练

在确保 SandboxFusion 服务正在运行的前提下，可以启动强化学习训练。首先确保已经切换回 verl 的 conda 环境，然后进入配方目录并执行 RL 训练脚本：

```bash
conda activate verl
bash recipe/retool/run_qwen2-32b_dapo.sh
```

强化学习训练使用 DAPO（Direct Alignment from Preferences Optimization）方法，这是一种高效的偏好优化算法。在训练过程中，模型会生成多个候选答案，并通过与代码沙箱的交互来验证答案的正确性。正确的答案会获得正向奖励，而错误的答案则会获得负向奖励。通过这种奖励机制，模型逐渐学会生成更准确的推理过程和更有效的工具使用策略。

强化学习阶段的训练时间通常比 SFT 阶段更长，因为每个训练步骤都涉及模型推理、代码执行和奖励计算等多个环节。训练过程同样会记录到 wandb 平台，可以实时监控奖励值、成功率等关键指标的变化趋势。随着训练的推进，应该能够观察到模型在数学问题求解上的准确率逐步提升，工具使用的效率也会不断优化。

### 训练监控与评估

在强化学习训练期间，需要密切关注几个关键指标来评估训练效果。首先是平均奖励值，它反映了模型生成答案的整体质量。随着训练的进行，平均奖励应该呈现上升趋势。其次是问题求解成功率，即模型能够正确回答的问题比例。这个指标直接反映了模型的实际能力提升。此外，还应关注工具调用频率和工具使用成功率，这些指标能够揭示模型是否学会了有效利用代码沙箱来辅助推理。

通过 wandb 界面，可以可视化这些指标的变化曲线，并与 SFT 阶段的基线进行对比。如果发现训练停滞或性能下降，可能需要调整学习率、奖励函数权重或其他超参数。定期在验证集上评估模型性能，有助于及时发现过拟合等问题并采取相应的调整措施。

### RL 训练过程实例

在 RL 训练过程中，可以观察到模型与 SandboxFusion 代码沙箱的实时交互。训练日志清晰地展示了模型生成代码、沙箱执行代码并返回结果的完整循环。以下是训练过程中 SandboxFusion 服务的典型日志输出：

```
2025-10-01 08:10:56 [debug] start processing python request with code ```
import math

x_approx = (4 * math.sqrt(3) - 2) / 5
print(f"Approximate x: {x_approx}")
``` and files []...(memory_limit: 1024MB) [sandbox.server.sandbox_api]
2025-10-01 08:10:56 [debug] running command python /tmp/tmppzrv67yh/tmp1y8y74j1.py [sandbox.runners.base]
2025-10-01 08:10:56 [debug] stop running command python /tmp/tmppzrv67yh/tmp1y8y74j1.py [sandbox.runners.base]

2025-10-01 08:10:57 [debug] start processing python request with code ```
from itertools import product

# Define all edges with indices (0-11)
edges = {
    'T1': 0, 'T2': 1
``` and files []...(memory_limit: 1024MB) [sandbox.server.sandbox_api]
2025-10-01 08:10:57 [debug] running command python /tmp/tmpy_ac6y5a/tmpxn02qp2v.py [sandbox.runners.base]
2025-10-01 08:10:57 [debug] stop running command python /tmp/tmpy_ac6y5a/tmpxn02qp2v.py [sandbox.runners.base]

2025-10-01 08:11:04 [debug] start processing python request with code ```
def is_greedy_successful(N):
    # Calculate the greedy result
    q = N // 25
    r = N % 25
    gr
``` and files []...(memory_limit: 1024MB) [sandbox.server.sandbox_api]
2025-10-01 08:11:04 [debug] running command python /tmp/tmpyqtl99_8/tmph_t_tj6u.py [sandbox.runners.base]
2025-10-01 08:11:04 [debug] stop running command python /tmp/tmpyqtl99_8/tmph_t_tj6u.py [sandbox.runners.base]

2025-10-01 08:11:07 [debug] start processing python request with code ```
import math

z_numerator = 9 * math.sqrt(5) - 1
z = z_numerator / 4
print(f"z = {z}")
``` and files []...(memory_limit: 1024MB) [sandbox.server.sandbox_api]
2025-10-01 08:11:07 [debug] running command python /tmp/tmpbk3a7frj/tmp12g7qyuf.py [sandbox.runners.base]
2025-10-01 08:11:07 [debug] stop running command python /tmp/tmpbk3a7frj/tmp12g7qyuf.py [sandbox.runners.base]
```

这些日志展示了 RL 训练的几个重要特征。首先，模型在处理不同类型的数学问题时会生成多样化的代码片段，从简单的数值计算（使用 math 模块）到复杂的算法实现（使用 itertools 等标准库）。其次，每个代码请求都在隔离的临时目录中执行，确保了执行环境的安全性和独立性。沙箱为每次执行创建独特的临时文件（如 `tmp1y8y74j1.py`），执行完成后立即清理，避免了状态污染。

从日志的时间戳可以看出，代码执行的速度非常快，大多数简单计算在毫秒级完成。这种高效的执行机制使得模型能够在训练过程中进行大量的工具调用尝试，快速积累经验。日志中还可以观察到，模型会针对同一个问题生成多个候选解决方案（体现在相近时间戳的多个代码请求），这正是 DAPO 算法基于 GRPO 框架的工作方式——通过生成和比较多个响应来估计相对优势。

值得注意的是，每个代码请求都设置了内存限制（memory_limit: 1024MB），这是沙箱环境的安全机制之一，防止恶意或低效的代码消耗过多系统资源。这种资源限制确保了训练过程的稳定性，即使模型生成了有问题的代码，也不会影响整个训练系统的运行。

### 训练启动与初始验证

当 RL 训练启动时，系统会输出详细的初始化和验证信息。首先是 AgentLoopWorker 的初始化日志，显示了代码解释器工具的配置：

```
(AgentLoopWorker pid=235550) Performing class-level ToolAgentLoop initialization [repeated 7x across cluster]
(AgentLoopWorker pid=235550) {
(AgentLoopWorker pid=235550)   "type": "function",
(AgentLoopWorker pid=235550)   "function": {
(AgentLoopWorker pid=235550)     "name": "code_interpreter",
(AgentLoopWorker pid=235550)     "description": "A tool for executing code.",
(AgentLoopWorker pid=235550)     "parameters": {
(AgentLoopWorker pid=235550)       "type": "object",
(AgentLoopWorker pid=235550)       "properties": {
(AgentLoopWorker pid=235550)         "code": {
(AgentLoopWorker pid=235550)           "type": "string",
(AgentLoopWorker pid=235550)           "description": "The code to execute."
(AgentLoopWorker pid=235550)         }
(AgentLoopWorker pid=235550)       },
(AgentLoopWorker pid=235550)       "required": ["code"]
(AgentLoopWorker pid=235550)     }
(AgentLoopWorker pid=235550)   }
(AgentLoopWorker pid=235550) }
(AgentLoopWorker pid=235550) Initialized tools: {'code_interpreter': <recipe.retool.retool.CustomSandboxFusionTool object at 0x7b4207c44c20>}
```

这些日志表明系统正在初始化 8 个 AgentLoopWorker（对应 8 张 GPU），每个 worker 都配置了相同的代码解释器工具。工具定义采用标准的函数调用格式，包含工具名称、描述和参数规范。"repeated 7x across cluster" 表示这个初始化过程在除主进程外的 7 个 worker 进程中重复执行，确保了分布式训练中各个进程的配置一致性。

接下来是初始验证阶段（val_before_train），这是 RL 训练前的基线性能评估。系统会在 AIME 2025 验证集上生成多个响应（30 个），并计算各种统计指标：

```
(TaskRunner pid=221183) Initial validation metrics: 
  'val-core/aime_2025/acc/mean@30': 0.1856 (平均准确率 18.56%)
  'val-core/aime_2025/acc/best@30/mean': 0.6362 (最佳答案准确率 63.62%)
  'val-core/aime_2025/acc/maj@30/mean': 0.2778 (多数投票准确率 27.78%)
  'val-aux/num_turns/min': 2 (最少交互轮数)
  'val-aux/num_turns/max': 16 (最多交互轮数)
  'val-aux/num_turns/mean': 6.59 (平均交互轮数)
```

这些指标揭示了训练前模型的几个重要特征。mean@30 表示对每个问题生成 30 个响应后的平均准确率，这个基线为 18.56%。best@30 表示在这 30 个响应中选择最佳答案的准确率，达到 63.62%，这说明模型有能力生成正确答案，但缺乏一致性。maj@30 表示通过多数投票选择答案的准确率为 27.78%，高于平均值但低于最佳值，说明多样化采样能够一定程度改善结果。

奖励值的统计同样重要。验证集上的平均奖励为 -0.464，这是因为奖励设计为正确答案 +1、错误答案 -1，负值表明初始模型的错误率较高。best@2、best@4、best@8 等指标分别表示在 2、4、8 个响应中选择最佳答案的平均奖励，这些值随着候选数量增加而提升（从 -0.263 到 0.290），验证了采样多样性对性能的积极影响。worst 指标则展示了最差答案的表现，始终保持负值且随候选数量增加而下降，这是预期行为。

num_turns 统计揭示了模型的交互模式。平均交互轮数为 6.59，范围从 2 到 16，说明模型在不同问题上采用了不同的策略，简单问题可能只需要少量交互，而复杂问题则需要多轮迭代。这个基线数据为后续观察训练过程中工具使用模式的演化提供了参照点。

训练进度条显示数据集完整遍历需要 3499 个训练步骤（基于 DAPO-Math-17k 数据集大小 179 万问题 / 批次大小 512 × 1 epoch）。但根据论文实验结果，ReTool 方法的一个显著优势是训练效率高，实际上只需要约 400 个训练步骤就能达到优异的性能。这意味着模型仅使用数据集的约 11% 就能充分学习工具使用策略，大幅缩短了训练周期。随着训练的进行，可以通过 wandb 界面实时监控这些指标的变化趋势，观察模型性能的提升轨迹。

### RL 训练循环机制

初始验证完成后，系统进入正式的 RL 训练循环。ReTool 采用基于 PPO 的训练流程，每个训练步骤都包含采样（Rollout）、奖励计算（Reward Computation）和策略更新（Policy Update）三个核心阶段，这个循环会在整个训练过程中反复执行。

**Rollout 阶段（采样与推理）**是训练循环中最耗时的部分。当前策略模型从训练集中抽取一批数学问题（每个 iteration 处理 32 个问题），对每个问题生成多个候选解答。根据配置参数 n_resp_per_prompt=16，系统会对每个问题生成 16 个不同的响应，总计 512 个响应。这些响应通过采样策略（temperature=1.0）产生，确保了足够的多样性以支持 DAPO 算法的相对优势估计。

在生成过程中，系统使用 vllm 推理引擎，配置了 infer_tp=4 的张量并行，将模型切分到 4 张 GPU 上进行高效推理。关键的是，模型与 SandboxFusion 代码沙箱进行实时交互。当模型生成代码片段并使用 `<code></code>` 标签标记时，vllm 暂停生成，将代码发送到沙箱执行。沙箱采用异步架构，维护一个包含 128 个 worker 的池，独立处理代码执行任务。执行完成后，结果（或错误信息）被包装在 `<interpreter></interpreter>` 标签中返回给模型。模型接收到反馈后继续生成，可以根据执行结果调整推理方向或尝试修正代码。这种交互可以重复多次，直到模型给出最终答案。每个响应都是一个完整的推理轨迹，包含交织的文本推理、代码片段和解释器输出。由于涉及代码执行等待和多轮交互，Rollout 阶段通常占据每个 iteration 的主要时间。

训练过程中可能出现工具调用解码错误，这是正常现象：

```
(AgentLoopWorker pid=235547) ERROR:2025-10-01 08:14:21,179:Failed to decode tool call: Invalid \escape: line 2 column 135 (char 135)
(AgentLoopWorker pid=235547) ERROR:2025-10-01 08:14:28,934:Failed to decode tool call: Extra data: line 2 column 228 (char 228)
(AgentLoopWorker pid=235548) ERROR:2025-10-01 08:15:37,582:Failed to decode tool call: Invalid \escape: line 2 column 480 (char 480)
```

这些错误表明模型在探索阶段生成了格式不完全正确的工具调用代码，比如包含未转义的反斜杠、多余的数据或缺少分隔符等。这正是强化学习探索过程的体现——模型需要尝试各种可能的代码生成方式，包括一些会失败的尝试，然后通过奖励信号学习哪些是有效的。随着训练的进行，这类错误的频率会逐渐降低，因为模型学会了生成格式正确的工具调用。

**奖励计算阶段（Reward Computation）**是一个相对快速的 CPU 密集型过程。系统收集 Rollout 阶段生成的全部 512 个响应，提取每个响应的最终答案（通常包含在 `<answer></answer>` 或 `\boxed{}` 标记中）。答案提取器会处理各种格式变体，确保能够可靠地识别模型给出的数值、表达式或符号答案。然后将提取的答案与标准答案进行比较，使用等价性检查而非简单的字符串匹配，例如数学表达式 "1/2" 和 "0.5" 会被判定为等价。正确答案获得 +1 奖励，错误答案获得 -1 奖励。

这种简单的二值奖励设计是 ReTool 方法的一个重要特点。与一些方法尝试对代码可执行性、中间步骤正确性等给予额外奖励不同，ReTool 只关注最终结果，让模型完全基于结果反馈来学习。这种设计避免了复杂的启发式规则可能引入的偏差，给予模型更大的探索自由度。对于每个问题的 16 个响应，系统计算出 16 个对应的奖励值。这些奖励值在 DAPO 算法中用于估计相对优势——每个响应的质量相对于同一问题的其他响应如何。同一问题的多个响应之间的奖励差异直接反映了不同策略的优劣，为策略梯度提供了明确的学习信号。DAPO 的 Token-Level Policy Gradient Loss 确保这些奖励信号被公平地分配到不同长度的响应上，避免超长响应主导训练过程。

**策略更新阶段（Policy Update）**是 PPO 算法的核心，也是唯一需要反向传播的阶段。系统将 train_batch_size=512 个样本（来自 32 个问题 × 16 个响应）作为一个完整的训练批次。为了适应 GPU 显存限制并提高训练稳定性，这个大批次被进一步分割成若干个 ppo_mini_batch_size=64 的小批次，依次进行梯度下降。具体来说，512 个样本被分成 8 个 mini-batch，每个包含 64 个样本。

对于每个 mini-batch，训练过程如下：首先，策略模型对这 64 个响应进行前向传播，计算在当前策略下生成这些响应的对数概率。然后，计算策略比率，即当前策略相对于旧策略（生成这些响应时的策略）生成该响应的概率比。接下来，使用 DAPO 算法估计的优势函数和改进的裁剪目标函数计算损失。裁剪机制通过 clip_ratio_low=0.2 和 clip_ratio_high=0.28 实现不对称裁剪，这是 DAPO 的 Clip-Higher 策略的核心——为向上更新提供 28% 的空间，为向下更新仅提供 20% 的空间，确保新策略在探索高奖励模式的同时不会出现性能退化。Token-Level Policy Gradient Loss 在此阶段发挥作用，对损失函数按响应长度进行归一化，确保长短序列获得公平的梯度权重。最后，进行反向传播和参数更新。

由于启用了 FSDP 和 CPU offload，这个阶段涉及复杂的内存管理。模型参数和优化器状态在 CPU 和 GPU 之间频繁传输。每个 mini-batch 的训练开始时，相关参数从 CPU 加载到 GPU；计算完成后，更新的参数和梯度信息又被传回 CPU。全部 8 个 mini-batch 处理完成后，一次完整的策略更新就完成了。DAPO 继承了 GRPO 不需要单独训练价值网络的优势，通过同批次响应的相对质量来估计优势函数，大幅简化了训练流程并减少了显存需求。在此基础上，DAPO 的四项技术创新进一步提升了训练的效率和稳定性，使其能够在 50% 的训练步数内超越传统方法的性能。

这个采样-奖励-更新的循环在整个训练过程中持续进行。每完成一个训练步骤，策略模型的参数就得到一次更新，生成能力略有提升。然后进入下一个循环，使用更新后的策略重新采样，获得新的响应和奖励，再次更新策略。正是通过这种迭代优化，模型逐渐学会了何时调用工具、如何编写有效代码、怎样利用执行结果来辅助推理等复杂技能。

根据配置，每 5 个训练步骤（test_freq=5）会进行一次验证，评估当前策略在验证集上的表现。每 30 个步骤（save_freq=30）会保存一次模型检查点，用于后续恢复或分析。根据论文实验结果，训练约 400 个这样的循环就能达到 67% 的 AIME 2024 准确率，显著超越仅用文本推理的基线模型（40%）。这种高效的训练特性使得 ReTool 在实际应用中具有很强的可行性。

随着训练的深入，可以观察到几个重要的演化趋势。代码使用频率逐渐提高，模型学会在更多问题上主动调用工具。代码的复杂度增加，从简单的计算扩展到复杂的算法实现。工具调用的时机提前，模型学会尽早引入代码来避免累积误差。最引人注目的是涌现行为的出现——模型开始展现代码自我修正能力，能够从执行错误中学习并生成修正版本，这种元认知能力标志着模型已经掌握了真正自适应的工具使用策略。

### Rollout 时间估算方法

理解 Rollout 阶段的时间构成对于合理规划训练周期至关重要。虽然 SandboxFusion 代码沙箱能够高速处理代码执行请求（每秒处理数个请求），但整个 Rollout 阶段的耗时远不止代码执行本身。

**实际工作量计算**涉及多个维度的乘积。根据配置参数，每个训练步骤需要生成 train_batch_size=512 个完整响应，这实际上是从 32 个数学问题（512 / n_resp_per_prompt = 512 / 16 = 32）分别生成 16 个不同的候选答案。每个响应不是一次性生成，而是通过多轮交互逐步构建的推理轨迹。从实际训练数据可以看出，平均每个响应包含约 7.82 轮交互（num_turns/mean），每轮交互通常包含一次文本推理生成、一个代码片段的生成和执行、以及解释器反馈的处理。因此，完成一个完整的 Rollout 需要的代码执行次数为：512 个响应 × 7.82 轮/响应 ≈ 4000 次代码执行。这个数字远超表面上的 512 个响应，解释了为什么即使 SandboxFusion 每秒能处理多个请求，整个 Rollout 阶段仍需要较长时间。

**Token 生成量和实际性能表现**可以从训练日志中获得准确数据。从第一个训练步骤的统计来看，512 个响应的平均长度为 2707 tokens，范围从最短的 288 tokens 到达到上限的 16384 tokens。约 0.85% 的响应（4-5 个）达到了最大长度限制被截断。整个训练步骤处理的总 token 数为 24,892,834 tokens，这包括了 Rollout 生成、Reference Model 的 log probability 计算以及 Actor 更新过程中的前向和反向传播。系统的整体吞吐量为 641 tokens/秒，显著低于纯文本生成场景，这是多轮交互、代码执行等待和 CPU offload 等因素共同作用的结果。

**训练各阶段的实际耗时**揭示了计算资源的分配模式。从第一个训练步骤的统计数据看，Rollout 生成阶段耗时 2529 秒（42 分钟），这是训练循环中最耗时的阶段，期间 vllm 引擎需要生成 512 个响应并与 SandboxFusion 进行约 4000 次代码执行交互。Reference Model 的 log probability 计算耗时 525 秒（8.7 分钟），这个阶段对已生成的 512 个响应进行前向传播以获取旧策略下的概率值，相比 Rollout 阶段要快得多。策略更新阶段耗时 1795 秒（30 分钟），这个阶段将 512 个样本分成 8 个 mini-batch 依次进行梯度下降，由于启用了 FSDP 和 CPU offload，大量时间消耗在参数的 CPU-GPU 传输上，因此成为除 Rollout 外的第二大时间开销。整个训练步骤的总耗时为 4853 秒（约 81 分钟），这个时间**不包括**初始验证阶段，初始验证在训练正式开始前独立完成。

**批处理效率下降**是多轮交互场景的固有挑战。虽然 vllm 配置了异步模式（mode=async），但在实际运行中，512 个请求的进度并不同步。开始时，vllm 可能以接近满批次的状态处理请求，但随着部分请求遇到代码执行触发器并暂停等待，实际的并发批次大小会逐渐下降。当一些请求在等待沙箱返回结果时，其他请求继续生成；当暂停的请求收到反馈后重新加入批次时，又有新的请求遇到代码触发器而暂停。这种动态的批次大小波动导致实际的平均批处理大小远小于理论上的 512，进而降低了整体吞吐量。

**通过 SandboxFusion 日志估算进度**是一个实用的监控方法。通过统计日志条目的数量，可以粗略估算已完成的响应数。基于实际统计，平均每个响应约有 8 次代码调用（num_turns/mean: 7.82），因此已完成响应数 ≈ 代码执行请求数 / 8。进度百分比 = 已完成响应数 / 512 × 100%。

**第一个训练步骤的实际表现**提供了宝贵的性能基准。根据实际运行数据，完整的第一个训练步骤耗时 4853 秒（约 81 分钟），处理了总计 24,892,834 个 tokens，整体吞吐量为 641 tokens/秒。训练过程的平均奖励从初始验证的 -0.464 提升到 0.058，表明模型在单个训练步骤后就开始展现学习效果。响应长度统计显示，平均响应为 2707 tokens，最短 288 tokens，最长达到上限的 16384 tokens。约 0.85% 的响应（4-5 个）达到了最大长度限制被截断。输入提示的平均长度为 332 tokens，最长 787 tokens，说明数学问题的描述相对简洁，而模型的推理过程则相当详细。

**资源利用和性能指标**反映了训练系统的效率水平。GPU 显存方面，单步训练的峰值显存分配达到 214.8 GB，显存预留为 226.8 GB，接近 8 张 H200 GPU 的总显存容量。CPU 内存使用达到 213.0 GB，这是启用 CPU offload 后将大量模型参数和优化器状态卸载到 CPU 内存的结果。模型的 FLOPs 利用率（MFU）为 39.7%，这个数值虽然低于纯计算场景的理论峰值，但考虑到多轮交互的等待、CPU-GPU 数据传输以及异步 rollout 的调度开销，是一个合理的利用水平。最慢的单个响应生成耗时 2492 秒（41.5 分钟），该响应达到了最大长度 16384 tokens，其生成时间几乎决定了整个 Rollout 阶段的总耗时，体现了典型的"木桶效应"。

**后续训练步骤的稳定性与学习曲线**可以从 step 2 的数据中得到验证。第二个训练步骤的总耗时为 4859 秒（81 分钟），与第一步几乎完全一致，表明训练流程已经进入稳定状态，初始化开销并非主要瓶颈。各阶段的时间分布保持高度一致：Rollout 生成 2543 秒（42.4 分钟），log probability 计算 510 秒（8.5 分钟），策略更新 1801 秒（30 分钟）。然而，在训练效果方面，模型展现出了快速的学习进展。平均奖励从 step 1 的 0.058 大幅跃升至 step 2 的 0.164，提升了 182%，对应的准确率从约 53% 提升到 58%。这种显著的性能改善验证了 ReTool 方法的有效性——模型正在快速学习何时以及如何使用代码工具来提升数学推理能力。

值得注意的是，响应模式出现了分化。最短响应从 288 tokens 降至 60 tokens，表明模型学会了对简单问题采用更直接的解法；而最长响应仍然达到 16384 tokens 上限，且被截断的响应比例从 0.85% 增加到 0.94%，说明对复杂问题的探索更加深入。平均交互轮数略微下降（从 7.82 到 7.79），但结合奖励提升来看，这反映了工具使用效率的改善而非探索深度的减少。系统的整体吞吐量从 641 tokens/s 提升到 650 tokens/s，虽然提升幅度不大，但表明训练流程在持续优化。CPU 内存使用从 213 GB 增加到 227 GB，这种增长趋势需要持续监控，以防在长时间训练后出现内存溢出。

**前十个训练步骤的实际观察**揭示了训练过程的动态特征和性能演化趋势。步骤一和步骤二的耗时高度一致，分别为 4853 秒和 4859 秒（均为 81 分钟），表明训练流程在初始阶段已经进入稳定状态。然而，从步骤三开始出现了显著的耗时增长现象，这一趋势持续到步骤九，总耗时从 81 分钟增长到 136 分钟，增幅达 68%。步骤十的总耗时为 128 分钟（包含 19.4 分钟的验证时间），纯训练时间为 109 分钟，虽然比步骤九略有下降，但仍然显著高于初始水平。

这种耗时增长的主要驱动因素是响应长度的持续增加。平均响应长度从步骤一的 2707 tokens 持续增长至步骤九的 4330 tokens，累计增长达 60%。步骤十首次出现了响应长度的回落，降至 4116 tokens，下降了 5%，这可能标志着响应长度增长趋势开始趋于稳定。被截断响应的比例同样经历了大幅增长，从步骤一的 0.85%（4-5 个响应）增长到步骤九的 3.70%（19 个响应），步骤十略有回落至 2.93%（15 个响应）。这些触及 16384 tokens 上限的超长响应，其生成时间从步骤一的 41.5 分钟增长到步骤九的 76.2 分钟，步骤十回落至 70.8 分钟，始终主导着整个 Rollout 阶段的总耗时。

步骤五是第一个包含验证的步骤，总耗时达到 6069 秒（101.2 分钟），其中验证阶段单独耗时 913 秒（15.2 分钟）。验证阶段需要对 30 个问题分别生成 30 个响应（n_resp_per_prompt_val=30），总计 900 个响应。有趣的是，验证阶段的平均交互轮数为 6.98，明显低于训练阶段的 7.84，这可能与验证时使用的不同采样参数（top_p=0.6, temperature=1.0）有关。扣除验证时间后，步骤五的纯训练时间为 5156 秒（86 分钟），仍然高于前两步的 81 分钟，但低于步骤四的 94 分钟，显示出一定的波动性。

**模型学习进展**在前十个步骤中呈现出波动上升的轨迹。训练集上的平均奖励从步骤一的 0.058 波动上升至步骤十的 0.251，对应的准确率从约 53% 提升到 63%，累计提升了 10 个百分点。学习曲线呈现非单调特征，步骤一到二有大幅提升（+5 个百分点），步骤二到五增速放缓，步骤六达到局部峰值（0.251，63%），步骤七出现回落（0.206，60%），随后在步骤八再次攀升（0.264，63%），步骤九和十维持在 0.25 左右的水平。这种波动是强化学习训练的正常现象，反映了策略在探索和优化之间的动态平衡。

验证集性能的演化提供了模型泛化能力的关键洞察。步骤五的验证结果显示，平均准确率（mean@30）为 27.9%，Best-of-30 指标为 62.9%，多数投票准确率（maj@30）为 36.9%。到步骤十，平均准确率略微提升至 28.3%，但 Best-of-30 指标显著提升至 67.4%，增长了 4.5 个百分点，表明模型的峰值能力在持续增强。然而，多数投票准确率下降至 33.8%，降低了 3.1 个百分点，这种分化现象说明模型虽然能够生成更高质量的答案，但一致性有所下降。验证阶段的平均交互轮数从步骤五的 6.98 降至步骤十的 5.85，减少了 16%，这与训练阶段的交互模式演化（轮数减少但每轮更复杂）呈现相似的趋势。训练集与验证集之间存在明显的性能差距，训练集准确率达到 63%，而验证集平均准确率仅为 28%，但 Best-of-30 达到 67.4%，说明模型具备生成正确答案的能力，主要挑战在于提高生成的一致性和可靠性。

**响应生成模式的演化**在前十个步骤中展现出先增长后稳定的趋势。平均响应长度从步骤一的 2707 tokens 持续增长至步骤九的 4330 tokens，累计增长达 60%，步骤十首次回落至 4116 tokens。平均交互轮数则呈现相反的趋势，从步骤一的 7.82 轮逐渐降至步骤十的 7.10 轮，下降了 9%，但每轮交互产生的内容大幅增加，从平均每轮 346 tokens 增长到步骤十的 580 tokens，增幅达 68%。这种模式转变表明模型正在学习生成更复杂、更详细的单轮推理，而不是简单地增加交互轮数。最慢的单个响应生成时间从步骤一的 41.5 分钟增长到步骤九的 76.2 分钟，步骤十回落至 70.8 分钟，这些超长响应的生成时间几乎完全决定了整个 Rollout 阶段的总耗时，木桶效应贯穿整个训练过程。整个训练步骤处理的 token 总量从步骤一的 24.9M 增长到步骤十的 36.5M，增幅达 47%，这种增长既来自响应长度的增加，也来自训练流程中多次前向传播的累积效应。

**系统资源利用情况**在前十个步骤中展现出良好的稳定性。GPU 显存使用从步骤一的 214.8 GB 逐渐增长到步骤十的 216.1 GB，增长不到 1 GB，始终保持在 8 张 H200 GPU 总容量的安全范围内。CPU 内存使用在步骤二达到 227 GB 后在 220-228 GB 范围内波动，步骤十为 221.8 GB，没有出现持续增长导致内存溢出的风险。模型的算力利用率（MFU）在 39.7%-40.3% 之间小幅波动，保持在稳定的水平，这个利用率虽然低于纯计算场景的理论峰值，但考虑到多轮交互等待、CPU-GPU 数据传输和异步调度等开销，反映了当前配置下的实际表现。整体吞吐量从步骤二的 650 tokens/s 峰值持续下降到步骤十的 595 tokens/s，下降了 8.5%，这种下降与响应长度增加和处理更长序列的额外开销直接相关。

**训练内部技术指标**展现了 DAPO 算法的稳定运行状态和设计优势。策略梯度损失（actor/pg_loss）在前十个步骤中保持在 -0.0022 到 +0.0011 之间的小幅波动，绝对值很小且稳定，表明策略更新处于平稳状态。策略裁剪比例（actor/pg_clipfrac）从步骤一的 0.197% 逐渐下降到步骤十的 0.157%，始终保持在很低的水平，说明几乎所有的策略更新都在允许的范围内，没有触发过度更新的保护机制。这个持续的低裁剪比例验证了 Clip-Higher 策略的有效性——通过不对称裁剪（clip_ratio_low=0.2, clip_ratio_high=0.28），为向上更新预留了足够空间，避免了过度裁剪导致的训练停滞。下界裁剪比例（actor/pg_clipfrac_lower）在所有步骤中都接近于零（最大仅为 1.2e-7），表明没有出现策略退化的情况，证明了严格限制向下更新的策略是成功的。

KL 散度（actor/ppo_kl）在前十个步骤中始终保持在 1.3e-5 到 2.4e-5 之间（除步骤五的异常低值 1.51e-6），数值极小且波动范围很窄。步骤十的 KL 散度为 1.46e-5，处于正常范围内。这种极小的 KL 散度配合较低的裁剪比例，共同保证了训练的稳定性，避免了策略崩溃或性能突然下降的风险。由于配置中设置了 kl_coef=0.0，KL 散度项并未直接加入损失函数，这些观察到的小 KL 值完全是裁剪机制和小学习率（1e-6）自然产生的结果，体现了 DAPO 算法内在的稳定性。

梯度范数（actor/grad_norm）在前十个步骤中呈现持续的下降趋势，从步骤一的 0.132 降至步骤十的 0.104，累计下降了 21%。梯度范数的大小直接反映了参数更新的强度，其下降趋势说明模型参数在逐渐接近某个局部最优点，需要的调整幅度越来越小。所有步骤的梯度范数都保持在 0.096-0.133 的健康范围内，既没有出现梯度消失也没有梯度爆炸，表明反向传播过程运行良好。特别值得关注的是策略熵（actor/entropy）的演化轨迹，从步骤一的 0.158 逐渐上升至步骤十的 0.180，增长了 14%。这种熵值的持续上升是 DAPO 算法 Clip-Higher 策略成功的有力证据——在使用对称裁剪的传统 GRPO 基线中，熵往往会在训练早期快速下降到接近零，导致模型失去探索能力和输出多样性。DAPO 通过不对称裁剪成功维持并增强了策略的探索性，避免了熵崩溃问题。

优势函数（critic/advantages）的统计分布在各步骤中保持相对一致的模式。平均优势值在 0.013-0.054 之间波动，接近于零，这符合 DAPO 继承自 GRPO 的设计——优势函数衡量的是相对于批次平均水平的好坏，因此其均值理论上应该接近零。优势函数的极值范围稳定在 -3.75 到 +3.75 之间，这个对称的范围表明批次中既有显著优于平均水平的优秀响应，也有明显劣于平均水平的较差响应，为策略梯度提供了清晰的学习信号。Token-Level Policy Gradient Loss 的应用确保了这些优势值被公平地分配到不同长度的序列上，避免了长序列因为包含更多 token 而获得不成比例的大梯度。优势函数分布的稳定性表明算法的相对质量估计机制运行正常，能够有效识别不同响应的优劣。

## Wandb 完整训练实验结果深度分析

### 训练动态总览

通过对完整训练过程的 wandb 日志系统性分析，我们可以深入理解 ReTool 方法在 DAPO 算法优化下的全周期学习动态。实验比较了两个训练配置的模型性能，两者都使用 qwen2.5-32b 作为基础模型并配合工具使用训练，但在探索策略和优化参数上存在差异。从整体趋势来看，训练过程经历了约 110 个训练步骤，展现出稳定的学习曲线和明显的性能提升，最终在 AIME 2025 验证集上达到了 52% 的平均准确率和 85% 的 Best-of-30 准确率。

### 核心性能指标深度分析

**验证集准确率演化轨迹**展现了模型能力的阶段性提升特征。在 val-core 指标组中，mean@30 准确率（对每个问题生成 30 个响应后的平均准确率）从训练初始的约 0.25（25%）经过三个明显的上升阶段最终达到 0.52（52%），累计提升了 27 个百分点。第一个快速提升阶段出现在前 20 步，准确率从 25% 攀升至 35%，每步平均提升 0.5 个百分点，这是模型快速学习基本工具使用模式的关键时期。第二个平台期出现在 20-60 步，准确率在 35-40% 之间波动，增长放缓，这反映了模型在巩固已学技能并探索更复杂策略时的过渡阶段。第三个加速提升阶段出现在 60-100 步，准确率从 40% 快速上升到 52%，这是模型在前期探索基础上实现策略优化突破的体现。

更值得关注的是 best@30 指标（在 30 次尝试中至少生成一次正确答案的能力），从初始的约 0.60（60%）持续提升到最终的 0.85（85%），累计增长 25 个百分点。这个指标的持续上升表明模型的峰值能力在不断增强，即使平均水平存在波动，模型在探索空间中找到正确解的能力仍在稳步提高。橙色和绿色两条曲线在训练过程中表现出高度一致的整体趋势但存在阶段性领先转换，橙色线在前 40 步表现更优（best@30 约高 2-3 个百分点），这可能源于其更保守的策略更新带来的初期稳定性优势。绿色线在 60 步后实现反超并最终达到更高的准确率水平（85% vs 82%），这表明其更激进的探索策略在充分训练后展现出更强的长期潜力。

准确率的标准差指标（acc/maj@30/std）维持在 0.05-0.08 的范围内，呈现出先增后减的倒 V 字形趋势。标准差在初期维持在约 0.055 的稳定水平，在训练中期（40-70 步）增长到峰值 0.078，随后在后期（70-110 步）逐渐回落到 0.062。这种模式深刻反映了强化学习的探索-利用动态平衡。初期标准差较小说明模型行为相对保守和一致，中期标准差增大表明模型在积极探索各种工具使用策略，产生了更多样化的响应模式，后期标准差回落则表明模型开始收敛到经过验证的高质量解决方案，行为变得更加稳定和可预测。best@30 的标准差同样呈现相似的倒 V 字形模式，峰值出现在训练中期（约 50-60 步），这进一步验证了中期是模型策略分化和探索最活跃的阶段。

**多数投票准确率**（acc/maj@30/mean）提供了关于模型一致性的重要洞察。这个指标从初始的约 0.28（28%）增长到最终的约 0.34-0.36（34-36%），增幅约 8 个百分点。值得注意的是，多数投票准确率始终显著低于 mean@30 准确率（低约 15-18 个百分点），这种差距表明模型生成的 30 个响应中并非总是多数正确，存在较大的答案多样性。绿色线的多数投票准确率在后期（80-110 步）略低于橙色线（约低 2 个百分点），结合其更高的 best@30 和 mean@30 准确率，这种模式表明绿色配置牺牲了部分一致性来换取更高的峰值表现和平均水平，这是其高熵探索策略的自然结果。

### 交互轮数演化的深层解读

**训练集交互轮数的复杂模式**揭示了两种配置在工具使用策略上的本质差异。橙色线的平均交互轮数（num_turns/mean）从初始的约 7 轮呈现明显的增长趋势，在训练中期（40-60 步）快速攀升，最终稳定在 9-9.5 轮的高位水平，累计增长约 35%。这种增长模式表明橙色配置的模型正在学习进行更深入的验证和迭代，倾向于通过多轮工具调用来提高答案的可靠性。绿色线则维持在相对稳定的 7-8 轮水平，虽然也有轻微的增长趋势，但幅度远小于橙色线。这种差异根源于两种配置的优化目标权衡——橙色配置可能设置了更低的早停阈值或更保守的终止条件，鼓励模型在给出最终答案前进行更充分的探索和验证。

最大交互轮数（num_turns/max）在两条线上都始终保持在 15-16 轮的稳定水平，这是由配置参数 max_turns=8 在多个响应采样（n_resp_per_prompt=16）下的自然上界。有趣的是，即使在训练后期，最大值仍然维持在这个上限，说明始终存在一些复杂问题需要模型进行最大深度的探索，模型尚未学会在所有情况下提前终止。最小交互轮数保持在 2 轮的稳定水平，这表明对于最简单的问题，模型在整个训练过程中都能够快速识别并给出答案，只需要一轮思考和一次工具调用即可完成。这种极值的稳定性与平均值的变化形成对比，说明交互轮数的演化主要发生在中等难度问题上，而不是在极端简单或极端困难的问题上。

**验证集交互轮数的保守特征**与训练集形成鲜明对比。验证集上的平均交互轮数（val-aux/num_turns/mean）从初始的约 6.8 轮呈现下降趋势，最终稳定在 5.8-6.0 轮，显著低于训练集的 7-9.5 轮。这种差异有多重原因。首先，验证时使用的不同采样参数（top_p=0.6, temperature=1.0）相比训练时的参数更加保守，top_p=0.6 的核采样限制了模型只考虑累积概率最高的 60% 的词汇，这减少了生成过于冒险或不确定的中间步骤的可能性，导致推理路径更加直接。其次，验证集上的 AIME 2025 问题可能与训练集的 DAPO-Math-17k 在难度分布上存在差异，如果验证集问题相对更规范或与训练集中某些类型问题相似，模型可能学会了更高效的解题模式。第三，模型在验证时不受梯度更新的影响，采用确定性更强的推理模式，而训练时的探索性需求推高了交互轮数。

绿色线在验证集上的交互轮数明显更低且更稳定（约 5.8-6.0 轮），而橙色线则略高（约 6.2-6.5 轮）并展现出更大的波动。结合绿色线在验证集准确率上的优势，这种模式表明绿色配置在保持高准确率的同时实现了更高的推理效率，这是其在训练过程中更好地泛化了工具使用策略的体现。橙色配置虽然在训练集上采用了更多轮的交互（9-9.5 轮），但这种策略并未在验证集上转化为等比例的性能提升，反而造成了额外的计算开销，这暗示其部分额外的交互轮数可能是对训练集的过度拟合，而非真正有效的推理深度。

### AIME 2025 分层性能的细粒度分析

**简单问题集的卓越表现**展现了模型在基础推理能力上的坚实基础。在最简单的问题集（aime_2025/score/mai@30，包含相对较易的 30 道题）上，模型的平均得分从初始的约 -0.20 快速提升到最终的约 0.20-0.25，在评分范围（-1 到 +1）内实现了从负向收益到显著正向收益的转变。绿色线在此指标上始终领先橙色线约 0.03-0.05 分，最终达到约 0.25 的更高水平。这个得分对应的准确率约为 62.5%（从 -1/+1 映射到 0-100%），说明模型在简单问题上已经具备了较强的求解能力。得分在训练前 30 步有快速提升（从 -0.20 到 0.05），随后在 30-70 步进入平台期（0.05-0.10），最后在 70-110 步再次加速（0.10-0.25），这种三段式增长模式与整体准确率曲线高度一致。

简单问题集的标准差（mai@30/std）维持在约 0.48-0.52 的稳定范围，略有下降趋势（从 0.52 降至 0.48）。这个相对较小的标准差表明模型在简单问题上的表现相对一致，不同问题之间的难度差异较小，或者模型已经学会了处理这个难度范围内各类问题的通用策略。标准差的轻微下降进一步表明模型在训练后期对简单问题的处理更加稳定和可靠。

**中等难度问题的均衡发展**体现了模型泛化能力的提升。中等难度问题集（maj@8，包含 8 道中等难度题目）的平均得分从初始的约 -0.30 提升到最终的约 0.05-0.15，累计提升约 0.35-0.45 分，对应准确率从约 35% 提升到 52.5-57.5%。两条线在这个难度级别上表现接近，最终得分差距仅约 0.02-0.03 分，说明两种配置在中等难度问题上的能力相当。橙色线在训练前期（0-50 步）略有优势，绿色线在后期（60-110 步）实现反超，这与整体性能曲线的领先转换模式一致。

中等难度问题的得分曲线呈现出更明显的非单调性，在 20-30 步、50-60 步和 80-90 步都出现了局部的性能回落，回落幅度约 0.05-0.10 分。这种波动比简单问题集更加剧烈，反映了中等难度问题对模型策略变化的敏感性——当模型尝试新的工具使用模式时，可能暂时性地降低了在某些中等难度问题上的表现，但这种探索是达到更高长期性能的必要代价。标准差在中等难度问题集上显著更大（约 0.52-0.58），且在训练过程中呈现先增后减的趋势，峰值出现在 40-60 步（约 0.60），这再次验证了中期是模型策略探索最活跃的阶段。

**高难度问题的挑战与进步**揭示了模型的能力边界和提升空间。在较难的问题集（maj@4，包含 4 道较难题目）上，平均得分从初始的约 -0.15 提升到最终的约 0.05-0.10，累计提升约 0.20-0.25 分。虽然绝对提升幅度不如简单问题集，但考虑到起点更低且问题更难，这个提升仍然是显著的。绿色线在这个难度级别上的优势更加明显，最终得分约 0.10，比橙色线高约 0.03-0.05 分，这表明绿色配置的高熵探索策略在困难问题上展现出更强的优势。

最困难的问题集（worst@8 和 worst@4，包含最难的 8 道和 4 道题目）则展现了模型面临的主要挑战和仍需突破的瓶颈。worst@8 的得分从初始的约 -0.70 缓慢提升到最终的约 -0.20 到 -0.15，虽然仍为负值（对应准确率低于 50%），但提升幅度达到 0.50-0.55 分，相对改善约 70%。worst@4 的表现略好，最终稳定在约 -0.10 到 -0.05 的水平，接近盈亏平衡点。这些负分表明即使经过充分训练，模型在极端困难的数学竞赛问题上仍然面临显著挑战，正确率低于 50%，但持续的改进趋势（两条线都展现出稳定的上升轨迹，没有在训练后期出现平台期）表明进一步训练或采用更大规模模型可能带来更多提升。

最难问题集的标准差（worst@8/std 和 worst@4/std）显著更大，约在 0.18-0.26 范围内，且在训练过程中呈现复杂的波动模式。这种高标准差表明即使在最难的问题子集内，不同问题的难度仍然存在较大差异，或者模型对不同类型的困难问题的处理能力参差不齐。标准差在训练中期的增大（从约 0.20 增至 0.26）反映了模型在探索阶段对困难问题的处理策略变化较大，而后期的回落（降至 0.21-0.23）则表明模型开始收敛到相对稳定的困难问题解决模式。

### 响应生成模式的深层演化

**响应长度的三阶段增长模式**是理解模型推理策略演化的关键窗口。平均响应长度（response_length/mean）从初始的约 2500 tokens 经历了显著的增长，在训练 60-70 步达到峰值的约 4700-4800 tokens，随后稳定在 4200-4500 tokens 范围内，整个训练过程累计增长约 80%。这种增长可以划分为三个明显的阶段。第一阶段（0-30 步）是快速增长期，响应长度从 2500 tokens 增至 3500 tokens，每步平均增长约 33 tokens，这反映了模型正在学习生成更详细的推理过程，包含更多的中间步骤和工具调用。第二阶段（30-70 步）是持续增长期，响应长度从 3500 tokens 增至峰值 4700-4800 tokens，每步平均增长约 30 tokens，增速略有放缓但仍然显著，这表明模型在前期基础上继续深化推理复杂度。第三阶段（70-110 步）是稳定回落期，响应长度从峰值回落并稳定在 4200-4500 tokens，这种回落是模型优化效率的体现——经过充分探索后，模型学会了在保持高准确率的同时减少不必要的冗余推理。

橙色线在整个训练过程中维持着更短的响应长度（3500-4300 tokens），峰值出现在约 50 步（约 4300 tokens），随后稳定在 3800-4000 tokens。绿色线则经历了更显著的增长，峰值达到约 4800 tokens，最终稳定在 4400-4500 tokens。这种差异深刻反映了两种配置的推理策略差异。橙色配置更注重推理效率，通过相对简洁的推理过程达到可接受的准确率；绿色配置则采取更彻底的探索策略，生成更详细复杂的推理链来追求更高的准确率。两者的性能差距（绿色最终准确率约高 2-3 个百分点）部分来源于这种推理深度的差异，但同时也导致了训练效率的差异（绿色每步耗时约长 15-20%）。

**响应长度的分布特征**提供了关于模型行为多样性的重要信息。响应长度的最小值（response_length/min）展现出波动下降的趋势，从初始的约 100-300 tokens 逐渐降至训练后期的更低水平（50-200 tokens）。这种下降说明模型学会了对简单问题采用更直接简洁的解法，不再为不需要复杂推理的问题生成冗长的中间步骤。最小值的大幅波动（单步之间可能相差 100-200 tokens）反映了不同批次中最简单问题的难度差异，以及模型在不同训练阶段对"简单"的定义变化——早期模型可能对大多数问题都采取保守的详细推理，而后期模型则能够快速识别真正简单的问题并采用快捷路径。

响应长度的最大值（response_length/max）始终维持在 10000-20000 tokens 的高位水平，多次触及或接近配置的 16384 tokens 上限。最大值曲线呈现出比平均值更加剧烈的波动，在不同批次之间可能相差 5000-8000 tokens，这种波动源于最复杂问题的随机采样和模型在这些问题上的策略变化。clip_ratio 指标（达到最大长度被截断的响应比例）显示约 2-5% 的响应达到上限，具体比例随训练进程而变化。橙色线的截断比例相对稳定（约 2.5-3.5%），而绿色线则经历了显著的增长（从约 2% 增至峰值约 5%），随后回落到约 3-4%。绿色线更高的截断比例与其更长的平均响应长度和更深入的探索策略一致，这些被截断的超长响应通常对应于极端复杂问题的深度探索，虽然它们的生成耗时主导了整个 Rollout 阶段（木桶效应），但它们也是模型学习处理最困难问题的关键样本。

**输入提示长度的稳定性**验证了数据集的一致性。平均 prompt_length 在整个训练过程中维持在 330-340 tokens 之间的极小范围内波动（标准差仅约 2-3 tokens），最小值约 256 tokens，最大值在 600-1700 tokens 范围内，这种高度稳定性是预期的，因为输入问题的描述长度由数据集本身决定，不受模型训练状态影响。两条线在提示长度上几乎完全重叠，没有任何可见差异，这证实了它们使用完全相同的训练数据集和验证数据集。prompt_length 的 clip_ratio 始终为 0，表明所有问题描述都在 max_prompt_length=2048 的限制范围内，不存在因输入过长而被截断的情况。

提示长度的最大值虽然在 600-1700 tokens 范围内波动，但这种波动仅仅反映了不同批次中最复杂问题描述的自然差异，并不表示任何训练动态。有趣的是，最大提示长度（最高约 1700 tokens）与平均长度（约 335 tokens）之间存在 5 倍的差距，这表明数据集中存在一些问题描述非常详细复杂（可能包含多个子问题、大量背景信息或复杂的数学符号），而大多数问题的描述则相对简洁。这种提示长度的分布特征部分解释了响应长度的大跨度分布——复杂的问题描述通常需要更长的响应来充分处理。

### 序列长度管理的系统性分析

**全局序列长度的持续增长**直接反映了训练过程的计算负担演化。平均全局序列长度（global_seqlen/mean，衡量每个训练步骤处理的总 token 数量）从初始的约 300000 tokens 稳步增长到最终的约 500000-550000 tokens，累计增长约 80-83%，与响应长度的增长幅度高度一致。这个指标的增长有多重来源：首先是响应长度的直接增长（从 2500 增至 4200-4500 tokens），其次是更复杂的多轮交互导致每个响应包含更多的中间状态，第三是训练流程中的多次前向传播（Rollout、log probability、策略更新）累积效应。

橙色线的全局序列长度显著低于绿色线，最终约 470000 tokens vs 550000 tokens，差距约 17%。这个差距与两者在响应长度上的差异（约 4000 vs 4500 tokens，差距约 12.5%）相比略大，这暗示绿色配置不仅生成更长的单个响应，而且在训练流程中可能涉及更多的重复计算或更深的梯度累积，导致总 token 处理量的差距被放大。这种差距直接转化为训练效率的差异——虽然两种配置使用相同的硬件资源（8 张 H200 GPU），但绿色配置每步需要处理更多的 tokens，因此耗时更长（约 8500 秒 vs 7000 秒，差距约 21%）。

**序列长度的极值演化**揭示了批次间异质性的变化。最大全局序列长度（global_seqlen/max）从初始的约 450000 tokens 增长到峰值的约 560000 tokens（约增长 24%），随后稳定在 540000-560000 tokens。最小全局序列长度同样呈现增长趋势，从约 280000 tokens 增至约 430000-500000 tokens（约增长 54-79%）。最小值的增长幅度显著大于最大值，这表明训练后期即使是处理"简单"批次（包含相对简单问题或模型快速收敛的问题）的总 token 数也大幅增加，这与平均响应长度增长和更复杂的推理模式一致。

balanced_min 和 balanced_max 指标（经过某种均衡处理的序列长度极值）展现了类似的增长模式，它们之间的差值（minmax_diff，反映批次间序列长度的异质性）在训练过程中呈现先增后减的倒 V 字形趋势。初始差值约 200000 tokens，在训练中期（40-60 步）急剧增加到峰值约 850000 tokens（增长 325%），随后在训练后期（70-110 步）回落到 300000-550000 tokens。这种模式深刻反映了训练动态的三个阶段：初期阶段模型行为相对一致，不同批次的处理方式差异较小；中期阶段模型积极探索各种策略，对不同类型问题采取差异化的处理方式，导致批次间异质性激增；后期阶段模型策略趋于成熟和稳定，批次间差异缩小但仍高于初始水平。

绿色线的 minmax_diff 峰值（约 850000-900000 tokens）显著高于橙色线（约 700000-750000 tokens），这再次验证了绿色配置更高的探索强度和行为多样性。值得注意的是，即使在训练后期，minmax_diff 也未回落到初始水平，而是稳定在约 300000-550000 tokens（初始值的 1.5-2.75 倍），这表明模型学到的差异化问题处理策略被保留了下来，成为其泛化能力的一部分。

### 计算性能与资源利用的全景分析

**Token 处理量的多维增长**全面展现了训练负担的演化。总 token 处理量（perf/total_num_tokens）从初始的约 25M tokens/step 稳步增长到最终的约 40M tokens/step（绿色线）或约 35M tokens/step（橙色线），累计增长 60%（橙色）到 80%（绿色）。这个指标包含了 Rollout 生成、Reference Model 的 log probability 计算以及 Actor 更新过程中的前向和反向传播，因此其数值显著大于单纯的响应生成 token 数（约 2-4.5M tokens/step）。总 token 数与响应长度的比率约为 8-10 倍，这个倍数相对稳定，表明训练流程中各阶段的 token 处理分布保持一致。

从总 token 数的增长曲线可以清晰地看到训练动态的阶段性特征。0-30 步是快速增长期（从 25M 增至 32M，每步增长约 0.23M），30-70 步是持续增长期（从 32M 增至 38-40M，每步增长约 0.15-0.20M），70-110 步是稳定期（维持在 38-40M，增速接近零）。这种阶段性增长与响应长度、交互轮数和策略复杂度的演化高度同步，表明它们是同一套底层机制驱动的协同变化。

**时间效率的逐步下降**是长序列处理的必然代价。每步耗时（perf/time_per_step）呈现出明显的增长趋势，橙色线从初始的约 5500 秒（92 分钟）增长到峰值的约 7500 秒（125 分钟），最终稳定在 7000-7200 秒（117-120 分钟），累计增长约 27-36%。绿色线的增长更加显著，从初始的约 5500 秒增长到峰值的约 9000 秒（150 分钟），最终稳定在 8000-8500 秒（133-142 分钟），累计增长约 45-64%。两条线之间的耗时差距从初期的几乎为零扩大到后期的约 1000-1500 秒（17-25 分钟），差距约 15-21%，这直接源于绿色配置更长的响应和更大的 token 处理量。

时间增长的主要驱动因素是响应长度的增加，更长的响应意味着更多的 token 生成、更多的代码执行等待和更多的前向传播计算。从数据上看，每步耗时与响应长度之间存在近乎线性的关系，响应长度每增长 1000 tokens，耗时约增加 1000-1500 秒（17-25 分钟）。这种线性关系表明主要瓶颈是 token 生成本身（通过 vllm 引擎）和代码执行等待（通过 SandboxFusion），而不是其他固定开销。如果瓶颈在于模型加载、批次调度等固定开销，耗时增长应该是次线性的；如果瓶颈在于梯度计算这种超线性复杂度的操作，耗时增长应该是超线性的。实际观察到的线性关系验证了系统设计的合理性——Rollout 阶段主导了总耗时，而 Rollout 的复杂度与 token 数成正比。

**吞吐量的对应下降**是时间增长和 token 数增长共同作用的结果。系统吞吐量（perf/throughput）从初始的约 660 tokens/s 逐渐下降到最终的约 600-620 tokens/s（橙色线）或约 580-600 tokens/s（绿色线），降幅约 8-12%。虽然每步处理的总 token 数增加了 60-80%，但由于耗时增加了 27-64%，实际的单位时间处理能力反而下降。这种吞吐量下降是长序列处理的固有挑战，主要有以下几个原因。

首先是批处理效率的下降。虽然 vllm 配置了 mode=async 和 train_batch_size=512，理论上可以同时处理 512 个请求，但在实际运行中，由于多轮交互导致不同请求的进度差异，实际的平均批处理大小远小于 512。初期所有请求都在同步生成文本，批次饱和度较高；随着部分请求遇到代码执行触发器并暂停等待，批次中的活跃请求数减少；当暂停的请求收到反馈后重新加入时，又有新的请求遇到触发器而暂停。这种异步批次的动态变化导致平均批处理大小可能只有理论值的 50-70%，而批处理大小的减少直接降低了 GPU 利用率和吞吐量。

其次是代码执行等待的累积。虽然单次代码执行通常只需要 0.1-0.5 秒，但当一个批次中有大量请求同时或接近同时需要代码执行时，SandboxFusion 的 128 个 worker 池可能达到饱和，导致部分请求需要排队等待。训练后期由于平均交互轮数增加（橙色线从 7 增至 9.5 轮）和每轮代码复杂度提升，代码执行的总次数和单次耗时都有所增加，这进一步加剧了等待时间。

第三是长序列的计算开销。Transformer 的自注意力机制的计算复杂度是 O(n²)，其中 n 是序列长度。当响应长度从 2500 tokens 增至 4500 tokens（增长 80%）时，理论的计算复杂度增长达到 (4500/2500)² = 3.24 倍。虽然 Ulysses 序列并行和各种优化技术能够缓解这种二次增长，但长序列的额外开销仍然是实际存在的。从吞吐量仅下降 8-12%（而非理论的 70% 下降）来看，系统优化在很大程度上抵消了长序列的影响，但未能完全消除。

橙色线在吞吐量上始终略高于绿色线（约 630 vs 610 tokens/s，差距约 3%），这体现了其在效率上的一贯优势。有趣的是，吞吐量的下降主要发生在训练前 60 步（从 660 降至 600-610 tokens/s），而在 60-110 步则基本稳定。这与响应长度的演化同步——响应长度在前 60 步快速增长，60-70 步达到峰值后回落并稳定，相应地吞吐量在同期快速下降后趋于稳定。这种同步性再次验证了响应长度是影响训练效率的主要因素。

**显存管理的卓越稳定性**展现了 FSDP 和内存优化策略的成功。最大显存预留（perf/max_memory_reserved_gb）在整个训练过程中保持在 216.8-217.4 GB 的极窄范围内，标准差仅约 0.2-0.3 GB，波动幅度不到 0.3%。最大显存分配（perf/max_memory_allocated_gb）同样稳定在 204.8-205.0 GB 范围内，标准差仅约 0.1 GB。这种高度稳定性表明，即使响应长度增长了 80%、总 token 数增长了 60-80%，实际的峰值显存使用几乎没有增长。这是因为 FSDP 将模型参数分片到 8 张 GPU 上，每张 GPU 只需存储约 1/8 的模型参数，大幅降低了单卡显存需求。同时，梯度检查点（gradient checkpointing）技术通过牺牲计算换取显存，在反向传播时重新计算中间激活值而非全程保存，进一步减少了显存占用。

预留显存与分配显存之间约 12 GB 的缓冲空间（217 - 205 = 12 GB）为临时操作提供了安全余量，如批次调度、KV cache 动态扩展、通信缓冲区等。这个缓冲空间在整个训练过程中保持稳定，表明没有发生显存泄漏或异常的显存累积。两条线在显存使用上几乎完全重叠且数值完全一致（差距小于 0.1 GB），说明显存使用主要由模型大小和批次配置决定，与具体的训练动态（如响应长度、交互轮数）关系不大。这种解耦合是理想的系统设计，确保了训练过程的鲁棒性——即使模型行为发生较大变化，也不会触发显存溢出。

预留显存总量 217 GB 在 8 张 H200 GPU 的总显存容量（约 8 × 141 GB = 1128 GB，假设 H200 每卡 141 GB）中占比约 19.2%，显存利用率相对保守。这种保守的利用率为更大的批次大小或更长的序列长度预留了空间，如果未来需要进一步扩展训练规模，可以在不更换硬件的前提下调整配置参数。同时，分配显存 205 GB 占预留显存的 94.5%，这个高占比说明预留的显存确实被有效使用，而非过度保守导致资源浪费。

**算力利用率的稳定平衡**反映了系统设计的权衡。模型算力利用率（perf/mfu/actor，Model FLOPs Utilization）在 0.388-0.394 之间小幅波动，平均约 39%，标准差仅约 0.002-0.003。这个 MFU 水平虽然低于纯计算场景的理论峰值（通常可达 50-60%），但考虑到 ReTool 训练的特殊性，39% 的 MFU 实际上是相当合理的。

ReTool 训练中存在多种降低 MFU 的因素。首先是多轮交互的等待时间，每次代码执行都需要暂停生成等待 SandboxFusion 返回结果，这段时间 GPU 处于空闲或低利用率状态。假设平均每轮交互有 0.3 秒等待（代码执行 0.2 秒 + 网络通信 0.1 秒），8 轮交互累积等待 2.4 秒，占整个响应生成时间（假设 10-15 秒）的 16-24%，这部分时间 GPU 几乎完全空闲，直接拉低了 MFU。其次是 CPU offload 导致的 CPU-GPU 数据传输开销。FSDP 将模型参数和优化器状态卸载到 CPU 内存，在每个 mini-batch 训练时需要从 CPU 加载到 GPU，计算完成后又传回 CPU。虽然使用了异步传输和预取技术来隐藏延迟，但数据传输仍然占用 PCIe 带宽并引入同步点，降低了 GPU 的有效计算时间占比。第三是异步 Rollout 的调度开销。多个推理请求在异步模式下并发执行，调度器需要动态管理请求队列、批次组装、KV cache 分配等，这些操作虽然主要在 CPU 上进行，但会影响 GPU 的指令流，导致气泡（bubble）时间的产生。

尽管存在这些降低因素，39% 的 MFU 仍然体现了系统优化的成功。对比纯推理场景（通常 MFU 在 20-30%）和简单的监督学习训练（可达 45-55%），ReTool 训练的 MFU 处于合理的中间位置。这表明虽然多轮交互和 CPU offload 确实引入了额外开销，但通过异步执行、批处理优化、混合并行等技术，系统在很大程度上掩盖了这些开销的影响。两条线在 MFU 上几乎完全重叠（差距小于 0.001），说明 MFU 主要由系统架构和硬件特性决定，与具体的训练策略（响应长度、探索强度等）关系不大。这种稳定性是理想的，意味着用户可以调整训练超参数来优化性能，而不必担心 MFU 的大幅波动影响训练效率。

MFU 在整个训练过程中保持高度稳定（波动范围仅 0.6%），没有出现下降趋势，这与吞吐量的下降（8-12%）形成对比。这种差异的原因在于 MFU 衡量的是 GPU 执行有效计算的效率，而吞吐量衡量的是端到端的 token 处理速率。即使 GPU 的计算效率保持稳定，由于需要计算的 tokens 增多（响应更长）且等待时间累积（更多代码执行），整体吞吐量仍然会下降。这个观察表明吞吐量下降的主要原因不是计算效率下降（MFU 稳定），而是计算量增加和等待时间延长。

### 训练时间分解的精细剖析

**Actor 更新时间的主导地位**凸显了 Rollout 阶段的瓶颈。更新 actor 的时间（timing_s/update_actor，包含 Rollout 生成、log probability 计算和策略更新三个子阶段）从初始的约 1700 秒（28 分钟）增长到峰值的约 3000 秒（50 分钟），最终稳定在 2600-2900 秒（43-48 分钟）。橙色线的 update_actor 时间明显低于绿色线，约 2400 秒 vs 2900 秒，差距约 500 秒（8 分钟）或 21%。这个阶段的耗时占整个训练步骤的 35-40%（对于不包含验证的步骤），是单阶段最大的时间开销。

从已知的详细分解数据（来自前十步的实际观察）可知，update_actor 时间中 Rollout 生成占约 2500-3000 秒（42-50 分钟），log probability 计算占约 500-550 秒（8-9 分钟），策略更新占约 1800-2000 秒（30-33 分钟）。三者的比例约为 50%:10%:40%，Rollout 和策略更新是两大主要开销。Rollout 的耗时高是因为它涉及 512 个响应的完整生成，包括多轮交互和代码执行等待。策略更新的耗时高则主要由于 CPU offload 导致的 CPU-GPU 数据传输——每个 mini-batch 开始时需要加载参数，结束时需要传回更新，这种频繁的数据传输在 CPU 和 GPU 之间累积了大量时间。log probability 计算相对较快是因为它只需要前向传播，不需要反向传播和梯度更新，且可以利用已缓存的 KV cache 加速。

**验证测试时间的合理性**验证了评估策略的效率。验证测试时间（timing_s/testing，仅在包含验证的步骤中非零）在各个验证步骤中显示为约 550-800 秒（9-13 分钟），平均约 650 秒（10.8 分钟）。这个时间包括对 30 个验证问题分别生成 30 个响应（共 900 个响应）的完整推理过程，以及响应的答案提取和准确率计算。验证时间呈现增长趋势，从步骤 5 的约 550 秒增至步骤 110 的约 800 秒，累计增长约 45%，这与响应长度的增长（约 60-80%）相比略小，说明验证过程可能采用了某些优化（如更短的 max_response_length 或更早的早停）。

验证时间占包含验证步骤总耗时的约 10-15%（例如步骤 10 的总耗时 7700 秒中验证占 1200 秒），这个占比是可接受的。当前配置的验证频率是每 5 步一次，意味着平均每步分摊的验证开销约为 (650 秒 / 5) = 130 秒，占平均步骤时间（约 7500 秒）的 1.7%。这个轻量级的验证开销确保了能够及时监控训练进度和模型性能，而不会显著拖慢整体训练速度。

两条线在验证时间上的差异（绿色约 750-800 秒，橙色约 650-700 秒，差距约 100-150 秒或 15-19%）与它们在训练响应长度上的差异相一致，表明验证过程确实反映了模型在验证集上的实际生成行为，而非使用固定的评估设置。这种一致性确保了验证结果的代表性——验证准确率能够真实反映模型在相同生成策略下在验证集上的表现。

**步骤总时间的综合演化**整合了所有阶段的开销。每个训练步骤的总时间（timing_s/step，与 perf/time_per_step 完全一致）全面反映了训练效率的变化，前文已详细分析。值得补充的是，通过对比包含验证和不包含验证的步骤，可以验证各阶段时间的加和关系。例如步骤 10（包含验证）的总时间约 7700 秒 = update_actor 约 2900 秒 + testing 约 1200 秒 + 其他开销约 3600 秒。"其他开销"包括 Reference Model 的计算、数据加载、检查点保存、指标记录等，占比约 47%，这个较高的占比表明除了 Rollout 和验证，训练流程中还存在大量的辅助操作。

步骤 30、60、90 等检查点保存步骤的总时间并未显著高于相邻步骤（差距小于 100 秒），这表明检查点保存与其他操作并行或异步执行，不会造成明显的额外等待。这种高效的检查点保存机制（通过 FSDP 的分布式保存实现）确保了训练流程的流畅性，不会因为周期性的 I/O 操作而产生性能尖峰。

**Profiling 开销的可忽略性**证实了监控系统的轻量级设计。Profiling 相关的时间开销（timing_s/stop_profile 和 timing_s/start_profile）均接近于零，数值在 0.0001-0.0002 秒范围内，占总步骤时间的不到 0.000003%。这表明 wandb 和其他性能监控工具的数据收集几乎不对训练产生可测量的影响。现代深度学习框架通过异步日志、批量上传、低优先级后台线程等技术，将监控开销降到了最低，使得用户可以无顾虑地启用详细的日志记录来全面了解训练动态。

**检查点保存的高效执行**体现了 FSDP 分布式保存的优势。检查点保存时间（timing_s/save_checkpoint，仅在保存步骤中非零）在各个保存步骤（30, 60, 90, ...）显示为约 46-54 秒，平均约 50 秒。对于一个 32B 参数的模型（FP16 格式约 64 GB），加上优化器状态（约 128 GB，因为 Adam 需要存储一阶和二阶动量），总共约 192 GB 的数据，能够在 50 秒内保存是相当高效的。这得益于 FSDP 的分布式保存机制——每张 GPU 独立保存其负责的模型分片（约 192 GB / 8 = 24 GB），通过并行 I/O 将总保存时间控制在单卡保存 24 GB 数据所需的时间。假设磁盘写入速度为 500 MB/s（典型的 SSD RAID 性能），保存 24 GB 理论需要 48 秒，与实际观察的 46-54 秒高度吻合，表明 I/O 带宽得到了充分利用，没有明显的瓶颈或低效。

检查点保存频率为每 30 步一次，意味着平均每步分摊的保存开销约为 (50 秒 / 30) = 1.67 秒，占平均步骤时间（约 7500 秒）的 0.022%，完全可以忽略不计。即使考虑验证开销（1.7%）和保存开销（0.022%），总的"非训练"开销仍然只有约 1.7%，训练过程的 98% 以上时间都用于实际的模型优化，这是高效训练系统的标志。

### 强化学习算法指标的理论与实践结合分析

**KL 散度的极小值特征**验证了 DAPO 算法的稳定性设计。KL 散度（actor/ppo_kl，衡量新策略与旧策略之间的差异）在整个训练过程中维持在极小的水平，数值范围在 1e-5 到 2.5e-4 之间，中位数约 5e-5。这种极小的 KL 散度（相比典型 PPO 训练的 1e-3 到 1e-2）表明新旧策略之间的差异被严格控制，每次更新都是微小的渐进式调整，训练过程非常稳定，不会出现策略崩溃或性能突然下降的风险。

KL 散度呈现轻微的增长趋势，从初始的约 1-2e-5 增至后期的约 1-2e-4，增长了一个数量级，但绝对值仍然极小。这种增长是合理的，反映了随着模型能力增强，策略调整的幅度略有增大，但仍然在严格的控制范围内。橙色线的 KL 散度（约 1-5e-5）显著低于绿色线（约 5-2.5e-4），两者相差一个数量级。这种差异表明橙色配置采用了更加保守的策略更新——每次更新对策略的改变更小，这可能通过更小的学习率、更强的裁剪或更大的 KL 惩罚系数实现（虽然配置显示 kl_coef=0.0，但实际可能存在隐式的 KL 约束）。

极小的 KL 散度配合较低的裁剪比例（actor/pg_clipfrac 约 0.01-0.03%，详见后文），共同构成了训练稳定性的双重保障。KL 散度确保了策略不会发生突变，裁剪机制则防止了极端的单步更新。由于配置中设置了 kl_coef=0.0，KL 散度项并未直接加入损失函数，这些观察到的小 KL 值完全是裁剪机制和小学习率（1e-6）自然产生的结果。这个现象体现了 DAPO 算法内在的稳定性——即使不显式添加 KL 惩罚，通过合理的裁剪和学习率设置，算法也能自然地维持小 KL 散度，避免策略发散。

**策略梯度损失的接近零特征**表明策略已接近稳定点。策略梯度损失（actor/pg_loss）在整个训练过程中维持在非常小的范围内，数值在 -0.001 到 +0.001 之间波动，绝对值平均约 0.0003，整体趋近于零。这种小幅波动是正常的，反映了策略在局部最优点附近的微调。策略梯度损失接近零并不意味着训练停滞，而是表明策略更新的幅度被严格控制，避免了过大的振荡。实际上，即使损失很小，累积的微小更新仍然能够带来显著的性能提升——从初始的 25% 准确率提升到最终的 52%，整个过程中 pg_loss 始终接近零。

两条线在策略梯度损失上展现出有趣的镜像对称性。橙色线主要在负值区域波动（约 -0.0005 到 0），绿色线则更多在正值区域（约 0 到 +0.0005），但绝对值都在同一量级（约 0.0003-0.0005）。这种差异可能源于不同的初始化、微小的超参数差异（如学习率的 1e-7 级差异）或随机种子，但由于绝对值都很小，这种差异并未导致训练轨迹的显著分化，两条线的最终性能仍然相近。损失的符号差异可能反映了优化方向的微妙不同——橙色配置可能更多地减少低优势样本的概率（负损失），而绿色配置则更多地增加高优势样本的概率（正损失），但由于 GRPO 的相对优势设计，这两种方向在数学上是等价的，只是实现方式不同。

策略梯度损失在训练过程中没有明显的趋势（既不持续增长也不持续下降），而是在零附近随机波动。这种无趋势的波动表明策略已经达到了一种动态平衡状态——虽然模型性能在持续提升，但策略本身的变化速率保持稳定，没有加速也没有减速。这是成熟的强化学习训练的标志，表明算法成功地平衡了探索与利用，维持了稳健的学习进程。

### 裁剪机制的深入分析

**策略裁剪比例的极低水平**证实了 Clip-Higher 策略的成功。策略裁剪比例（actor/pg_clipfrac，衡量触发裁剪保护机制的样本比例）在整个训练过程中保持在极低水平，数值范围在 1e-7 到 3e-4 之间，百分比形式为 0.00001% 到 0.03%。这意味着在 512 个训练样本中，平均只有 0.05-0.15 个样本（即几乎没有）触发了裁剪机制。这个极低的裁剪比例表明绝大多数策略更新都在允许的范围内（clip_ratio_low=0.2 到 clip_ratio_high=0.28），没有试图进行过度激进的更新。

裁剪比例呈现先增后减的倒 V 字形趋势。初期（0-20 步）维持在约 5e-5（0.005%），中期（20-70 步）增长到峰值约 2-3e-4（0.02-0.03%），后期（70-110 步）回落到约 1-1.5e-4（0.01-0.015%）。这种模式反映了训练动态的演化。初期裁剪比例极低说明模型刚从 SFT 检查点开始 RL 训练，策略调整非常小心谨慎。中期裁剪比例略有上升（但绝对值仍然很小）说明随着模型能力增强和策略探索加深，部分样本上的策略更新幅度增大，偶尔触碰到裁剪边界。后期裁剪比例回落说明模型策略趋于成熟，大部分样本上的策略已经收敛，不再需要大幅度调整。

尽管裁剪比例很低，Clip-Higher 策略仍然发挥了关键作用。通过设置不对称的裁剪范围（0.2 vs 0.28），算法为向上更新（增加高优势样本的概率）提供了更大空间（28% vs 20%），而为向下更新（减少低优势样本的概率）提供了更小空间。即使触发裁剪的样本很少，这种不对称性仍然在隐式地引导优化方向——当优势函数发出强烈信号（某个样本显著好于或差于平均水平）时，算法允许对"好"的情况做更大的强化，而对"差"的情况采取更保守的惩罚，这种偏向性累积起来就形成了持续的探索驱动力，成功避免了策略熵崩溃（详见后文熵分析）。

两条线在裁剪比例上展现出相似的趋势和量级，都在 1e-5 到 3e-4 范围内，没有显著差异。这表明裁剪机制的运作状态主要由共享的算法设计和超参数（clip_ratio_low/high）决定，不受具体训练动态（响应长度、交互轮数等）的显著影响。这种鲁棒性是理想的，确保了训练过程的稳定性和可预测性。

**下界裁剪比例的几乎为零**表明策略未出现退化。下界裁剪比例（actor/pg_clipfrac_lower，衡量因策略过度降低某些 token 概率而触发下界裁剪的样本比例）在所有训练步骤中都接近于零，数值在 1e-8 到 5e-8 之间，百分比形式为 0.000001% 到 0.000005%。这个极其微小的数值（比整体裁剪比例还低 3-4 个数量级）表明几乎从未发生向下更新超出允许范围的情况。在 512 个训练样本中，平均只有 0.00005-0.00025 个样本（即统计误差级别）触发下界裁剪，实际上可以认为从未触发。

这种几乎为零的下界裁剪比例是非常积极的信号，表明策略在整个训练过程中没有出现性能退化的趋势。如果模型在某些样本上过度降低原本高质量响应的概率，就会触发下界裁剪保护，但实际数据显示这种情况几乎不存在。结合策略梯度损失的小幅正负波动（而非持续负值）和奖励的持续上升，可以确认策略更新的方向是正确的，主要是强化好的行为而非惩罚坏的行为，这与 DAPO 的设计理念（鼓励探索和向上更新）完全一致。

两条线在下界裁剪比例上完全重叠且数值几乎相同（差异小于 1e-9），说明这个指标完全由算法机制决定，与具体配置无关。这种一致性进一步验证了 DAPO 算法在防止策略退化方面的内在稳健性，无需额外的手动干预或调参。

### 策略探索性的关键分析

**策略熵的持续上升奇迹**是 DAPO 算法最重要的成就。策略熵（actor/entropy，衡量策略输出分布的随机性和多样性）从初始的约 0.16 持续增长到最终的约 0.42-0.44，累计增长接近 180%，几乎增长到初始值的 2.75-2.8 倍。这种熵值的持续上升是极其罕见和宝贵的现象，在传统的 GRPO 或 PPO 训练中几乎不可能观察到。通常情况下，强化学习训练会导致策略熵快速下降——模型在探索初期尝试各种行为，随着发现高奖励的行为模式后，策略逐渐收敛到这些确定性的行为，熵值随之崩溃到接近零。一旦熵崩溃，模型失去探索能力，陷入局部最优，即使存在更好的策略也无法发现。

DAPO 通过 Clip-Higher 策略成功解决了熵崩溃问题。不对称裁剪（clip_ratio_low=0.2, clip_ratio_high=0.28）为向上更新提供了 40% 更大的空间（0.28 vs 0.20），这种不对称性在每次策略更新中都为探索行为提供轻微的鼓励。虽然单步的影响很小（裁剪比例仅 0.01-0.03%），但经过 110 个训练步骤的累积，这种持续的探索偏向成功地维持并增强了策略的多样性。从数据上看，熵值的增长几乎贯穿整个训练过程，没有出现平台期或回落，这表明探索机制一直在有效运作，没有被利用（exploitation）压制。

绿色线的熵值增长更为显著（从 0.16 增至 0.44，增长 175%），而橙色线则相对保守（从 0.16 增至 0.38，增长 138%）。这种差异与它们在准确率和响应多样性上的表现差异完全吻合。绿色配置的高熵意味着其策略在每个决策点考虑更多样化的 token 选择，不会过早地锁定某种固定模式，这使得它能够探索更广阔的策略空间，发现更优的工具使用策略，最终达到更高的准确率（52% vs 48%）和 best@30 指标（85% vs 82%）。然而，高熵也意味着输出的一致性较低，这解释了绿色线在多数投票准确率（maj@30）上略低于橙色线——生成的 30 个响应更加多样化，不容易通过投票达成一致。

橙色配置的中等熵增长（138%）在稳定性和探索性之间取得了较好的平衡。虽然最终熵值（0.38）低于绿色线，但仍然显著高于初始值（增长 138%），且远高于传统方法（通常熵会降至 0.05 以下）。这表明橙色配置也成功避免了熵崩溃，保持了一定的探索能力，只是相比绿色配置更倾向于利用已发现的高质量策略。这种策略差异使得橙色配置在训练效率上占优（每步耗时约短 15-20%），但在最终性能上略逊一筹。

熵值与准确率的同步上升（熵从 0.16 升至 0.42，准确率从 25% 升至 52%）打破了传统认知中"探索与利用是零和博弈"的观念。通常认为提高探索性（高熵）会牺牲性能（因为输出更随机），而提高性能需要降低探索性（低熵，确定性策略）。但 ReTool 的数据显示，在合适的算法设计（Clip-Higher）和任务特性（多样化的数学问题需要多样化的工具使用策略）下，探索性和性能可以同时提升。高熵不是随机噪声，而是策略在面对不同问题时采取差异化处理的能力，这种灵活性正是泛化能力的体现。

### 梯度动态的精细分析

**梯度范数的稳定下降**表明优化过程的健康收敛。梯度范数（actor/grad_norm，衡量参数更新梯度的大小）从初始的约 0.15 逐渐下降到最终的约 0.08-0.11，整体呈现持续下降趋势，累计降幅约 30-47%。梯度范数的大小直接反映了参数更新的强度——梯度范数越大，参数变化越剧烈；梯度范数越小，参数变化越平缓。下降趋势说明模型参数在逐渐接近某个局部最优点，损失函数的梯度变小，需要的调整幅度越来越小。这是优化过程正常收敛的表现，类似于梯度下降算法在接近最优点时步长自然减小。

梯度范数的下降并非线性，而是呈现阶段性特征。初期（0-30 步）下降较快（从 0.15 降至 0.12，降幅 20%），中期（30-70 步）下降放缓（从 0.12 降至 0.10，降幅 17%），后期（70-110 步）基本稳定（在 0.08-0.11 之间波动，无明显趋势）。这种阶段性下降与训练动态的其他指标同步——初期是快速学习阶段，参数调整幅度较大；中期是探索优化阶段，调整幅度逐渐减小；后期是稳定收敛阶段，参数已经接近最优值，只需微调。

在整个训练过程中，梯度范数始终保持在 0.07-0.15 的健康范围内，既没有出现梯度消失（< 0.01，会导致训练停滞）也没有梯度爆炸（> 1.0，会导致训练发散或数值不稳定）。这表明反向传播过程运行良好，梯度能够有效地从输出层传递到输入层的各个参数，梯度裁剪（如果有）也设置得当，没有过度抑制或放大梯度。梯度范数的稳定性是大规模模型训练成功的关键——32B 参数模型的反向传播涉及数百层的梯度累积，任何数值不稳定都可能导致梯度异常，但实际数据显示整个过程非常平稳。

橙色线的梯度范数略高于绿色线（约 0.10 vs 0.09，差距约 10%），这与其更保守的策略更新和更小的 KL 散度形成对比，似乎矛盾。通常认为更保守的更新应该对应更小的梯度范数。这种反直觉的现象可能源于以下原因：梯度范数衡量的是未经裁剪的原始梯度大小，而实际的参数更新可能经过裁剪、缩放或其他变换，两者不是严格的线性关系。橙色配置可能使用了更大的梯度裁剪阈值或不同的优化器参数（如 Adam 的 β1, β2），导致原始梯度较大但实际更新较小。或者，橙色配置在某些样本上的梯度方向分散（不同样本的梯度部分抵消），虽然单个样本的梯度范数大，但批次梯度的合并范数可能更小。这种细节差异需要更深入的诊断分析才能确定，但从宏观上看，两条线的梯度范数都在健康范围内，差异对训练稳定性的影响可以忽略。

**学习率的恒定与调度**反映了训练策略的保守性。学习率（actor/lr）在两条线上都展现出基本恒定的模式，数值维持在配置的 1e-6 水平。学习率曲线呈现轻微的锯齿状波动（在 9.8e-7 到 1.02e-6 之间），这种微小的波动（幅度仅 2%）可能源于数值精度、不同 mini-batch 的轻微差异或周期性操作（如检查点保存、验证）引入的短暂扰动，但本质上学习率是固定的，没有采用学习率调度器（如 cosine annealing 或 step decay）。

使用固定且相对较小的学习率（1e-6）是合理的训练策略。首先，模型从 SFT 检查点开始 RL 训练，已经具备了基本的工具使用能力和语言理解能力，RL 阶段的目标是精细调整策略以优化奖励，而非从头学习全新的能力，因此需要小心谨慎的更新，避免破坏 SFT 阶段学到的知识。其次，小学习率配合小批次（ppo_mini_batch_size=64）和多次梯度累积（512/64=8 个 mini-batch），使得策略更新非常平稳，不会出现大幅振荡。第三，固定学习率简化了训练过程，避免了学习率调度的额外超参数调优，适合探索性实验。

从训练结果来看，固定的小学习率是成功的——准确率从 25% 提升到 52%，策略熵从 0.16 增长到 0.42，训练过程高度稳定（KL 散度极小，梯度范数健康）。这表明 1e-6 的学习率在当前配置下是合适的，既不会太大导致不稳定，也不会太小导致收敛过慢。然而，对于更长时间的训练（如 500-1000 步），可能需要引入学习率衰减来进一步稳定后期训练，避免在最优点附近振荡。当前 110 步的训练长度处于学习率衰减不是必需但可能有益的边界。

### 奖励与优势估计的综合分析

**训练奖励的波动上升轨迹**全面反映了学习进展。训练集上的平均得分（critic/score/mean，即平均奖励）从初始的约 0.06（对应约 53% 准确率，因为奖励 = 2 × 准确率 - 1）波动上升到最终的约 0.40-0.50（对应约 70-75% 准确率），累计提升约 0.34-0.44，相对改善约 567-733%。这种大幅的绝对和相对提升表明模型在训练集上的问题求解能力得到了显著增强，工具使用策略得到了有效优化。

奖励曲线呈现明显的非单调性和阶段性特征。初期（0-20 步）快速提升（从 0.06 增至 0.15，每步平均提升 0.0045），这是模型快速学习基本工具使用模式的阶段，收益递增明显。中期（20-70 步）波动上升（从 0.15 增至 0.30，每步平均提升 0.003，但伴随多次回落），这是模型探索更复杂策略并在不同策略间切换的阶段，短期性能可能下降但长期趋势向上。后期（70-110 步）加速提升（从 0.30 增至 0.40-0.50，每步平均提升 0.0025-0.005），这是模型在前期探索基础上实现策略优化突破的阶段，虽然每步提升幅度与中期相近，但更加稳定，回落次数减少。

绿色线在大部分训练过程中表现优于橙色线，领先幅度在 0.02-0.08 之间（对应准确率高 1-4 个百分点）。特别是在训练后期（80-110 步），绿色线稳定在 0.48-0.52（准确率 74-76%），而橙色线则在 0.40-0.45（准确率 70-72.5%），差距达到 0.05-0.10（准确率差 2.5-5 个百分点）。这种持续的性能优势源于绿色配置更高的探索强度（熵值 0.44 vs 0.38）和更深入的推理（响应长度 4400-4500 vs 3800-4000 tokens），虽然这些特性带来了更高的计算成本（每步耗时约长 15-20%），但在追求最佳性能的目标下是值得的。

奖励的波动性在中期最为明显，标准差约 0.05-0.08（未直接给出但可从曲线估计），而初期和后期的波动较小（约 0.02-0.04）。这种波动模式与策略熵的演化、响应长度的变化和裁剪比例的趋势完全同步，再次验证了它们是同一套训练动态的不同侧面。中期的高波动反映了模型在积极探索阶段的不确定性——尝试新的工具使用模式可能暂时降低性能，但这是发现更优策略的必经之路。后期的低波动则表明模型策略趋于成熟，性能提升更加稳定和可预测。

**奖励的极值分布**验证了奖励函数的设计和数据质量。奖励的最小值（critic/score/min）始终保持在 -1 的下界，没有任何步骤偏离这个值。这是预期的，因为奖励函数设计为二值（正确 +1，错误 -1），不会出现中间值。-1 的持续存在说明即使在训练后期，模型在每个批次中仍然至少有一个响应是完全错误的。考虑到批次包含 512 个响应（32 个问题 × 16 个响应/问题），至少有 1-2 个完全错误的响应是合理的——某些问题可能极其困难，或者某些响应的采样随机性导致了低质量输出。

奖励的最大值（critic/score/max）同样始终维持在 +1 的上界，表明模型在每个批次中都能至少正确回答部分问题。从统计上看，最大值为 +1 意味着 512 个响应中至少有一个是完全正确的，考虑到 n_resp_per_prompt=16，这等价于 32 个问题中至少有一个问题的 16 个响应中至少有一个正确，这个门槛是相当低的。实际上，随着训练的进行，正确响应的数量应该大幅增加（从平均奖励 0.06 增至 0.40-0.50 可以推断正确率从 53% 增至 70-75%），但最大值始终卡在 +1 的事实仅仅反映了奖励函数的上界，不包含更多信息。

理想情况下，如果数据标注包含部分正确的分级（如 +0.5 表示部分正确），奖励分布会更加细致，能够提供更丰富的学习信号。但当前的二值奖励设计简化了奖励计算（只需判断答案等价性），避免了复杂的启发式规则可能引入的偏差，符合 ReTool 论文的极简主义奖励哲学。从训练结果来看，二值奖励已经足够有效，模型能够在这种简单的反馈下学到复杂的工具使用策略。

**返回值与优势函数的分布特征**揭示了算法的内部运作机制。平均返回值（critic/returns/mean）与平均奖励（critic/score/mean）完全一致，曲线完全重叠，这是因为在当前设计中没有折扣因子（γ=1），返回值就是即时奖励，没有考虑未来奖励的累积。这种设计是合理的，因为每个响应的生成是独立的事件，没有跨响应的长期依赖，因此不需要引入折扣因子来平衡即时奖励和长期回报。

返回值的极值范围（critic/returns/min 和 max）并非如预期的 -1 到 +1，而是在 -3.75 到 +3.75 的更宽范围内。这种扩展范围可能源于奖励裁剪、归一化或某种变换机制。一种可能的解释是系统对原始奖励进行了标准化处理（减均值除标准差），使其变为 z-score，从而将奖励分布从 [-1, +1] 映射到更宽的范围。另一种可能是系统应用了某种奖励塑造（reward shaping）或优势估计变换，虽然配置显示没有额外的奖励项，但实现细节中可能包含隐式的变换。第三种可能是返回值实际上包含了多个时间步的累积（虽然单个响应生成是一个完整的事件，但内部可能分解为多个决策点），导致范围扩展。

优势函数（critic/advantages）的平均值在整个训练过程中接近于零（-0.05 到 +0.05 之间），这完全符合 GRPO 算法的设计原理。GRPO 通过计算每个响应相对于同一批次中其他响应的相对质量来估计优势函数，具体公式为 A(s,a) = R(s,a) - mean(R(s,:))，其中 R(s,:) 是同一问题 s 的所有响应的奖励。由于优势函数定义为相对于均值的偏差，其均值在数学上必然接近零（精确为零，但由于数值误差和采样随机性可能略有偏离）。这种相对优势估计的好处是自动进行了基线校正，不需要训练单独的价值网络（critic），大幅简化了算法和减少了计算开销。

优势函数的极值范围稳定在 -3.75 到 +3.75，与返回值的极值范围完全一致，这进一步验证了优势函数直接基于返回值计算（通过减去批次均值）。这个对称的范围表明批次中既有显著优于平均水平的优秀响应（优势 +3.75），也有明显劣于平均水平的较差响应（优势 -3.75），两者的极值大小相近，说明批次内的质量分布是相对平衡的，没有出现极端的偏斜。优势函数的极值范围在训练过程中保持稳定（没有扩大或缩小的趋势），表明批次内响应质量的异质性保持一致，模型没有出现所有响应趋同（优势范围缩小）或质量分化加剧（优势范围扩大）的情况，这是健康训练的标志。

优势函数分布的稳定性表明算法的相对质量估计机制运行正常，能够有效识别不同响应的优劣并为策略梯度提供清晰的学习信号。Token-Level Policy Gradient Loss 的应用确保了这些优势值被公平地分配到不同长度的序列上，避免了长序列因为包含更多 token 而获得不成比例的大梯度。无论响应长度如何变化（从 2500 增至 4500 tokens），优势函数的分布特征保持一致，这证明了长度归一化机制的有效性。

### 训练稳定性与收敛特征的综合评估

**整体训练轨迹的三阶段模式**清晰展现了成熟的强化学习收敛过程。从所有指标的综合分析来看，110 个训练步骤可以划分为三个特征鲜明的阶段，每个阶段都有其独特的动态特征和学习目标。

**初期探索阶段（步骤 1-20）**是快速学习的黄金时期。在这个阶段，验证集准确率从 25% 快速提升到 35%（每步提升 0.5 个百分点），训练集奖励从 0.06 增至 0.15（每步提升 0.0045），响应长度从 2500 tokens 增至 3500 tokens（每步增长 50 tokens），策略熵从 0.16 增至 0.22（每步增长 0.003）。所有性能指标都呈现加速上升的态势，曲线斜率最大，这表明模型正在快速学习基本的工具使用模式和推理策略。初期阶段的特点是高收益、低波动、快节奏——模型从 SFT 检查点携带的知识为 RL 优化提供了良好的初始化，使得早期训练能够高效地收敛到基本可行的策略。梯度范数在这个阶段相对较高（0.12-0.15），表明参数调整幅度较大，模型在积极地修正初始策略中的缺陷。

**中期优化阶段（步骤 20-70）**是策略探索的关键时期。在这个阶段，准确率增长放缓但波动加剧（从 35% 增至 40-45%，伴随多次 2-3 个百分点的回落），响应长度继续增长但增速下降（从 3500 tokens 增至峰值 4700-4800 tokens，每步增长 24-30 tokens），策略熵显著上升（从 0.22 增至 0.35，每步增长 0.0026），裁剪比例达到训练过程的峰值（0.02-0.03%），梯度范数逐渐下降（从 0.12 降至 0.10）。这个阶段的波动式改进是探索与利用之间动态平衡的体现——模型在尝试新的工具使用策略时，短期性能可能下降（如步骤 30-35、50-55 的局部回落），但这些探索为后期的突破奠定了基础。所有标准差指标（准确率、响应长度、序列长度差异）在这个阶段达到峰值，反映了策略多样性的激增。两条配置线在这个阶段开始出现分化，绿色线展现出更强的波动性和更高的熵值，橙色线则相对保守和稳定。

**后期稳定阶段（步骤 70-110）**是策略成熟的收获期。在这个阶段，准确率再次加速提升并趋于收敛（绿色线从 42% 增至 52%，橙色线从 38% 增至 48%），响应长度从峰值回落并稳定（绿色线稳定在 4400-4500 tokens，橙色线稳定在 3800-4000 tokens），策略熵继续温和增长（绿色线从 0.35 增至 0.44，橙色线从 0.32 增至 0.38），所有标准差指标回落到较低水平，梯度范数进一步下降并稳定（0.08-0.11）。这个阶段的特点是高性能、低波动、稳收敛——模型在前期探索的基础上筛选出最有效的策略，并通过持续的优化将其稳定下来。性能曲线的波动幅度显著减小（从中期的 ±3% 降至后期的 ±1%），表明模型行为变得更加一致和可预测。响应长度的回落是效率优化的体现，模型学会了在保持高准确率的同时减少不必要的冗余推理。

**两种配置的对比策略与权衡**为不同应用场景提供了宝贵的参考。橙色线配置代表效率优先的训练策略，其特征包括更短的响应长度（节省约 12%）、更快的训练速度（每步节省约 15-20%）、更高的吞吐量（约高 3%）、更低的策略熵（0.38 vs 0.44）、更保守的 KL 散度（低一个数量级）和更稳定的训练过程（波动更小）。这种配置最终达到约 48% 的验证准确率和 82% 的 best@30 指标。计算成本分析显示，完成 110 步训练橙色配置约需 770000 秒（214 小时）。这种配置适合计算资源受限、追求快速迭代或对最终性能要求不苛刻的场景，如快速原型验证、资源受限环境或成本敏感的生产部署。

绿色线配置代表性能优先的训练策略，其特征包括更长的响应长度（约多 12-15%）、更深入的探索（更高的交互轮数和策略熵）、更激进的策略更新（更高的 KL 散度）、更大的性能波动（中期波动显著）和更高的计算成本（每步耗时约多 15-20%）。这种配置最终达到约 52% 的验证准确率和 85% 的 best@30 指标，相比橙色配置在准确率上高约 4 个百分点，在 best@30 上高约 3 个百分点。计算成本分析显示，完成 110 步训练绿色配置约需 935000 秒（260 小时）。这种配置适合追求最佳性能、计算资源充足或对模型能力有高要求的场景，如竞赛性能优化、学术研究基准或高端产品部署。

从投入产出比来看，橙色配置用 82% 的计算成本达到了 92% 的性能（48%/52%），性价比更高。绿色配置额外投入 18% 的计算获得 8% 的性能提升，边际收益递减但对于追求极致性能的场景仍然值得。两种配置在最终性能上的差距（4 个百分点）小于训练过程中的最大差距（中期曾达 6-8 个百分点），这表明橙色配置在后期实现了一定程度的追赶，其保守策略虽然限制了探索广度但保证了学习效果的稳定积累。

**训练稳定性的多维验证**证明了系统设计的可靠性和鲁棒性。在超过 110 个训练步骤、累计约 850000 秒（236 小时）的训练过程中，没有观察到任何异常的性能突降、梯度爆炸、显存溢出或数值不稳定等严重问题。所有关键指标的变化都呈现平滑的趋势，没有出现剧烈跳变或不连续点。KL 散度始终维持在极小值（1e-5 到 2.5e-4），策略更新高度渐进，每步调整幅度微小但累积效果显著。梯度范数保持在健康范围（0.07-0.15），既无梯度消失也无梯度爆炸，反向传播过程稳定可靠。显存使用高度稳定（216.8-217.4 GB），波动幅度不到 0.3%，即使响应长度增长 80% 也未导致显存增长，证明了 FSDP 和梯度检查点的有效性。CPU 内存使用维持在 220-228 GB 范围，没有出现持续增长或泄漏，内存管理机制运作良好。

训练过程中的所有验证步骤都成功完成，没有因超时、崩溃或资源耗尽而中断。检查点保存（每 30 步一次）都正常执行，平均耗时约 50 秒，证明了分布式 I/O 的高效性。Wandb 日志持续上传，所有指标都完整记录，没有数据丢失或上传失败。这种全方位的稳定性是成熟训练系统的标志，用户可以放心地运行长时间训练而无需频繁人工干预或监控。

### 性能优化建议与未来改进方向

基于对训练动态的深入分析和对瓶颈的精确定位，我们可以提出以下有针对性的优化建议，帮助用户进一步提升训练效率、降低成本或改善最终性能。

**响应长度管理的精细化**是提升训练效率的首要方向。当前约 3-5% 的响应达到 16384 tokens 上限被截断，这些超长响应的生成时间（单个响应可达 70-76 分钟）主导了整个 Rollout 阶段的总耗时，形成明显的木桶效应。建议引入 DAPO 论文提出的 Overlong Reward Shaping 机制，在奖励函数中加入温和的长度惩罚项。具体实现可以采用分段线性惩罚：长度 < 8000 tokens 不惩罚，8000-12000 tokens 每多 1000 tokens 惩罚 -0.01，12000-16384 tokens 每多 1000 tokens 惩罚 -0.05。这种温和的惩罚不会强制限制长度，而是引导模型在保证推理质量的前提下生成更简洁高效的响应。预期效果是平均响应长度减少 10-15%（从 4400 降至 3700-4000 tokens），被截断响应比例减少 50%（从 3-5% 降至 1.5-2.5%），每步耗时减少 15-20%（从 8000 秒降至 6400-6800 秒），而准确率下降不超过 1-2 个百分点（从 52% 降至 50-51%）。综合来看，用微小的性能牺牲换取显著的效率提升，性价比极高。

**动态采样策略的智能化**可以在保持训练质量的同时节省计算资源。当前配置对每个问题固定生成 16 个响应（n_resp_per_prompt=16），而 DAPO 论文提出的 Dynamic Sampling 技术建议根据训练进程和奖励分布动态调整采样数量。具体方案是在训练初期（0-30 步）使用更多采样（20-24 个）以获得稳定的优势估计，帮助模型快速建立基础策略；在训练中期（30-80 步）使用标准采样（16 个）以平衡探索与效率；在训练后期（80 步以后）当策略趋于稳定时减少采样（10-12 个）以提高效率。此外，可以根据问题难度自适应调整采样数量：对于模型已经能够稳定正确回答的简单问题（如连续 3 个批次准确率 > 90%），减少采样到 8 个；对于模型仍在挣扎的困难问题（准确率 < 50%），保持或增加采样到 20-24 个。预期效果是在保持训练质量（准确率变化 < ±0.5%）的前提下，平均每步的响应数减少 15-20%（从 512 降至 410-435），对应的 Rollout 时间减少 15-20%，总训练时间减少约 10-12%（因为 Rollout 占总时间的 50-60%）。

**验证策略的动态调整**可以减少总训练时间而不损失监控能力。当前每 5 步进行一次验证，每次验证需要约 10-15 分钟。考虑到训练后期性能趋于稳定（步骤 80-110 的准确率波动仅 ±1%），可以采用动态验证频率：初期（0-30 步）每 3 步验证一次以密切监控快速学习阶段的进展和及时发现问题，中期（30-80 步）每 5 步验证一次以平衡监控需求和计算开销，后期（80 步以后）每 10 步验证一次以减少冗余评估。此外，可以实现轻量级的快速验证（只生成 10-15 个响应而非 30 个，只评估 15-20 个问题而非全部 30 个）用于高频监控，每 15-20 步进行一次完整验证以获得准确的性能基准。预期效果是验证总耗时减少 30-40%（从约 150 分钟降至 90-100 分钟），占总训练时间的比例从 1.7% 降至约 1.0%，而监控能力不受显著影响。

**批处理效率的优化**可以提升吞吐量和 GPU 利用率。当前多轮交互导致的异步等待降低了平均批处理大小，实际批处理大小可能只有理论值（512）的 50-70%。建议实现更智能的批次调度策略：当某个请求因等待代码执行而暂停时，临时将其移出活跃批次并用新的请求填充，维持接近满批次的状态；当暂停的请求收到反馈后，将其加入下一个可用批次而非等待原批次。这种动态批次重组需要对 vllm 引擎进行定制化修改，实现复杂度较高，但潜在收益显著。预期效果是平均批处理大小提升到理论值的 75-85%（从当前的 50-70% 提升），对应的 GPU 利用率提升 10-20%（从当前的 39% 提升到 43-47%），吞吐量提升 15-25%（从 600 tokens/s 提升到 690-750 tokens/s），每步 Rollout 时间减少 12-18%（从 2500 秒降至 2050-2200 秒）。由于这项优化需要深入修改推理引擎，建议在资源充足和有长期训练需求的场景下考虑实施。

**检查点策略的空间优化**可以节省磁盘空间而不影响训练安全性。当前每 30 步保存一次完整检查点，每个检查点约 192 GB（模型 64 GB + 优化器状态 128 GB），110 步训练产生约 4 个检查点，总计约 768 GB。考虑到大多数中间检查点在训练完成后不会再使用，建议采用滚动保存策略：只保留最近的 3 个检查点（如步骤 90, 60, 30），当保存新检查点时自动删除最旧的（删除步骤 30 时保存步骤 120）；同时单独保留性能最优的检查点（根据验证准确率判断）和最终检查点。此外，可以探索检查点压缩技术，如对优化器状态使用有损压缩（保留 FP16 而非 FP32 精度）或只保存模型权重而不保存优化器状态（牺牲完美恢复能力但大幅减少空间）。预期效果是磁盘占用减少 60-75%（从 768 GB 降至 192-307 GB），而训练安全性几乎不受影响（仍可恢复到最近 3 个检查点之一）。

**超参数调优的进一步探索**可能带来额外的性能提升。基于当前实验的洞察，建议重点调整以下参数：学习率（actor_lr）可以尝试略微增大到 1.5e-6 或 2e-6，在前 50 步使用更大的学习率加速初期学习，然后在 50-110 步使用 cosine 衰减到 5e-7，这种学习率调度可能在相同步数内达到更高性能或用更少步数达到相同性能；Clip-Higher 的不对称比例可以进一步加大（如 clip_ratio_low=0.15, clip_ratio_high=0.35），为探索提供更强的驱动力，可能进一步提升策略熵和最终性能；n_resp_per_prompt 可以在保持总训练批次 512 不变的前提下调整为 12（对 42.67 个问题采样）或 20（对 25.6 个问题采样），探索不同的采样粒度对性能的影响。建议使用小规模实验（如 30-50 步）快速评估这些参数变化的效果，然后选择最优配置进行完整训练。

**多模态工具集成的拓展**可以进一步提升模型的问题求解能力。当前模型只能使用代码解释器（code_interpreter），而许多数学问题可能受益于其他工具，如符号计算引擎（调用 Mathematica 或 SymPy）进行复杂的代数推导，数值优化器求解约束优化问题，或可视化工具生成图表辅助几何问题的理解。建议扩展工具集并在训练数据中包含多工具使用的示例，让模型学习针对不同类型问题选择最适合的工具组合。这种多工具策略可能将 AIME 2025 的准确率从当前的 52% 进一步提升到 60-65%，尤其是在几何、概率统计等特定领域问题上。

**长期训练的可行性评估**提示了进一步性能提升的空间。当前训练在 110 步后仍然展现出上升趋势（绿色线在步骤 100-110 仍在提升，未出现明显的平台期），这表明模型尚未完全收敛，继续训练可能带来额外收益。根据 ReTool 论文，训练到 400 步可以达到 67% 的准确率（相比当前 110 步的 52%，还有 15 个百分点的提升空间）。建议在资源允许的情况下将训练延长到 200-300 步，预期可以达到 58-63% 的准确率。同时应监控验证集性能是否出现过拟合迹象（训练集准确率持续上升但验证集准确率停滞或下降），一旦发现过拟合应及时停止训练或引入正则化技术（如增大 KL 惩罚系数、降低学习率或增加 dropout）。

## RL 训练配方参数详解

强化学习训练脚本的参数配置比 SFT 阶段更加复杂，涉及到策略优化、奖励计算和多轮交互等多个维度。理解这些参数对于充分发挥 ReTool 方法的潜力至关重要。

数据和模型路径配置定义了训练的基础资源。train_files 指向 DAPO-Math-17k 数据集，这是包含 179 万数学问题的大规模训练语料。test_files 在这个配置中指向 aime_2025，用于训练过程中的定期评估。model_path 参数指向 SFT 阶段训练完成并转换为 Hugging Face 格式的模型检查点，这个模型已经具备了基本的工具使用能力，RL 训练将在此基础上进一步优化。tool_config_path 指定 SandboxFusion 工具的配置文件路径，定义了代码执行环境的各项参数。

算法相关参数控制了强化学习的核心机制。adv_estimator 设置为 grpo（Group Relative Policy Optimization），这是 DAPO 算法的基础组件，负责通过相对优势估计来优化策略。DAPO 在 GRPO 的框架上增加了四项关键改进（Clip-Higher、Dynamic Sampling、Token-Level Loss 和 Overlong Reward Shaping），使其特别适合长思维链场景。与传统的 PPO 算法相比，GRPO 不需要训练单独的 critic 模型，而是通过同一批次中不同响应的相对质量来估计优势，大幅简化了训练流程并提高了样本效率。use_kl_in_reward 和 kl_coef 参数控制是否在奖励中加入 KL 散度惩罚项，这里都设置为 False 和 0.0，表示不使用显式的 KL 约束，完全依靠 DAPO 的裁剪机制来控制策略更新幅度。clip_ratio_low 和 clip_ratio_high 分别设置为 0.2 和 0.28，这个不对称的裁剪范围正是 DAPO 的 Clip-Higher 策略的体现——为向上的策略更新提供更大空间（0.28 > 0.2），鼓励探索高奖励模式的同时防止性能退化。

序列生成和批次配置参数决定了模型的推理方式。max_turns 设置为 8，表示允许模型最多进行 8 轮思考和工具调用的交互循环。这个设置为复杂问题的深度探索提供了充足空间，模型可以反复验证假设、调整策略。max_prompt_length 设置为 2048，max_response_length 设置为 16384，两者的差异反映了 ReTool 方法的特点：输入问题通常较短，但包含多轮交互和代码执行结果的响应序列可能非常长。train_batch_size 设置为 512 是一个相当大的批次，但实际上通过 n_resp_per_prompt=16 实现，即对每个问题生成 16 个不同的响应，然后在这些响应之间进行相对质量比较。ppo_mini_batch_size 设置为 64，表示在策略更新时将 512 个样本分成多个小批次进行梯度下降。

性能优化参数对于高效利用 GPU 资源至关重要。infer_tp 设置为 4，表示在推理阶段使用 vllm 引擎的张量并行，将模型切分到 4 张 GPU 上进行快速生成。train_sp 设置为 8，表示在训练阶段使用 Ulysses 序列并行，将长序列切分到全部 8 张 GPU 上处理。offload 设置为 True，启用参数和优化器状态的 CPU 卸载，这对于在有限显存下训练 32B 参数模型是必需的。虽然 CPU 卸载会带来一定的速度开销，但它使得在单台服务器上完成整个训练流程成为可能。

多轮交互配置体现了 ReTool 的核心特性。multi_turn.enable 启用多轮对话模式，max_user_turns 和 max_assistant_turns 都设置为 8，与 max_turns 参数对应。tool_config_path 指向 SandboxFusion 的配置文件，定义了工具调用的接口和执行环境。format 设置为 hermes，这是一种标准化的工具调用格式，确保模型生成的工具调用请求能够被 SandboxFusion 正确解析和执行。rollout 模式设置为 async，允许多个推理请求并发执行，充分利用 vllm 引擎的高吞吐能力。

采样策略参数影响响应的多样性。训练阶段通过 n_resp_per_prompt=16 对每个问题生成 16 个不同的响应，这些响应的多样性为 DAPO 算法的相对优势估计提供了丰富的比较基础。虽然当前配置使用固定的采样数量，但 DAPO 的 Dynamic Sampling 技术允许在训练过程中根据需要动态调整这个参数。验证阶段则通过 n_resp_per_prompt_val=30 生成更多响应，并使用 top_p=0.6 和 temperature=1.0 的采样参数，在保持一定随机性的同时避免生成过于离谱的答案。gpu_memory_utilization 设置为 0.9，表示 vllm 引擎可以使用 GPU 显存的 90%，为推理预留充足的 KV cache 空间。

训练控制参数决定了训练的节奏和监控方式。val_before_train 设置为 True，在训练开始前先进行一次验证，建立性能基线。log_val_generations 设置为 100，表示在验证时记录前 100 个生成样本到 wandb，便于人工检查模型的推理过程和工具使用情况。save_freq 设置为 30，每 30 个训练步骤保存一次检查点，test_freq 设置为 5，每 5 个步骤进行一次验证。total_epochs 设置为 1，因为 DAPO-Math-17k 数据集规模已经足够大，单次遍历即可获得显著的性能提升。actor_lr 设置为 1e-6，这是一个相对较小的学习率，因为模型已经在 SFT 阶段学会了基本能力，RL 阶段只需要进行精细调整。

## 参考资料

- [DAPO 论文：大规模 LLM 强化学习系统](https://arxiv.org/pdf/2503.14476)
- [ReTool 论文：多轮对话与代码沙箱提升数学推理](https://arxiv.org/pdf/2504.11536)
- [verl 官方仓库](https://github.com/volcengine/verl/)
- [SandboxFusion 官方仓库](https://github.com/bojieli/SandboxFusion)
- [Qwen2.5 模型](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct)
- [AIME 2024 数据集](https://huggingface.co/datasets/BytedTsinghua-SIA/AIME-2024)
- [DAPO-Math-17k 数据集](https://huggingface.co/datasets/BytedTsinghua-SIA/DAPO-Math-17k)

## 常见问题

### GPU 显存不足怎么办？

如果遇到 GPU 显存不足的问题，可以尝试以下几种方案：

1. 减小微批次大小（micro_batch_size_per_gpu）
2. 启用 CPU offload 选项
3. 减小序列长度（max_length）
4. 使用梯度累积来模拟更大的批次

### 训练中断如何恢复？

verl 框架支持从检查点恢复训练。在训练脚本中设置 `resume_mode` 和 `resume_from_path` 参数即可。有两种常用的恢复模式：

**方式一：指定具体的检查点（推荐）**

如果训练在第 54 步中断，可以指定恢复到第 50 步的检查点：

```bash
bash recipe/retool/run_qwen2-32b_dapo.sh \
    trainer.resume_mode=resume_path \
    trainer.resume_from_path=recipe/retool/checkpoint/qwen2.5-32b_dapo_with_tool/global_step_50
```

这种方式需要明确指定包含 `global_step_` 的检查点路径。训练将从该检查点继续，全局步数会自动设置为 50。

**方式二：自动恢复最新检查点**

如果希望系统自动找到并恢复最新的检查点，可以使用 `auto` 模式：

```bash
bash recipe/retool/run_qwen2-32b_dapo.sh \
    trainer.resume_mode=auto
```

这种方式会自动搜索 `default_local_dir` 目录下的最新检查点并恢复。如果找不到检查点，训练将从头开始。

训练脚本会自动加载模型权重、优化器状态、数据加载器状态和训练进度，确保训练无缝继续。

### 如何评估模型性能？

无论是训练完成后还是训练进行到一半，都可以评估特定的检查点。评估分为两个步骤：首先合并模型，然后运行评估。

**步骤一：合并模型检查点**

由于训练过程中使用 FSDP 将模型分片保存，评估前需要先将检查点合并为 Hugging Face 标准格式。以评估第 40 步的检查点为例：

```bash
python3 -m verl.model_merger merge \
    --backend fsdp \
    --local_dir qwen2.5-32b_dapo_with_tool/global_step_40/actor/ \
    --target_dir qwen2.5-32b_dapo_with_tool/global_step_40/actor/huggingface
```

参数说明：
- `--backend fsdp`：指定源检查点的格式为 FSDP
- `--local_dir`：FSDP 分片检查点的路径（通常是 `global_step_X/actor/` 目录）
- `--target_dir`：合并后模型的保存路径（建议使用 `/huggingface` 子目录）

合并过程会读取所有分片文件，重构完整的模型权重，并以 Hugging Face Transformers 标准格式保存。这个过程需要一定的磁盘空间来存储合并后的模型文件。

**步骤二：运行评估**

合并完成后，可以使用 verl 提供的评估脚本，输入测试数据和合并后的模型路径，脚本会自动运行推理并计算准确率等指标。评估可以在训练过程中的任意检查点上进行，便于跟踪模型在不同训练阶段的性能表现。

### 多机训练如何配置？

对于多机训练，需要在每台机器上配置相同的环境，并在训练脚本中设置正确的节点数量（nnodes）和节点排名。verl 使用 PyTorch 的分布式训练机制，需要配置主节点的地址和端口供各节点通信。


优势函数（critic/advantages）的统计分布在各步骤中保持相对一致的模式。平均优势值在 0.013-0.054 之间波动，接近于零，这符合 DAPO 继承自 GRPO 的设计——优势函数衡量的是相对于批次平均水平的好坏，因此其均值理论上应该接近零。优势函数的极值范围稳定在 -3.75 到 +3.75 之间，这个对称的范围表明批次中既有显著优于平均水平的优秀响应，也有明显劣于平均水平的较差响应，为策略梯度提供了清晰的学习信号。Token-Level Policy Gradient Loss 的应用确保了这些优势值被公平地分配到不同长度的序列上，避免了长序列因为包含更多 token 而获得不成比例的大梯度。优势函数分布的稳定性表明算法的相对质量估计机制运行正常，能够有效识别不同响应的优劣。
