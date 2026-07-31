# AWorld GUI Agent for OSWorld Benchmark

This repository contains a high-performance GUI agent built on the [AWorld Framework](https://github.com/inclusionAI/AWorld), specifically designed to tackle complex desktop automation tasks within the [OSWorld-verified](https://os-world.github.io/) benchmark. Our agent achieves a **58.04% pass@1 score** on the `osworld-verified` leaderboard (`max_step=50`).

The core logic for our agent's perception and reasoning is adapted from the great work of the [AgentS2 project](https://github.com/simular-ai/Agent-S). We have built upon their foundation by introducing a suite of new executable tools that enhance the agent's ability to interact with the OS environment, leading to significant improvements in the stability and robustness of the Computer Use Agent (CUA).

## 🚀 Performance Highlights

Our agent demonstrates leading performance on the OSWorld-verified benchmark (`max_step=50`), using `openai/o3` as the base model with `temperature=1.0`.

### OSWorld-Verified Leaderboard Comparison

| Agent                  | Score (pass@1)  | Success/Total | chrome      | gimp  | libreoffice_calc | libreoffice_impress | libreoffice_writer | multi_apps  | os    | thunderbird | vlc         | vs_code |
| ---------------------- | --------------- | ------------- | ----------- | ----- | ---------------- | ------------------- | ------------------ | ----------- | ----- | ----------- | ----------- | ------- |
| **aworldAgent (ours)** | **58.04%**| **209.55/361**| 22.96/46    | 19/26 | 33/47            | 28.39/47            | 13/23              | 40.41/93    | 16/24 | 11/15       | 9.79/17     | 16/23   |
| Agentic-Lybic-Maestro  | 57.1%           | 205.47/360    | 27.96/46    | 22/26 | 24/47            | 27.96/47            | 16/23              | 32.71/92    | 16/24 | 11/15       | 10.84/17    | 17/23   |
| CoACT-1                | 56.4%           | 203.55/361    | 20.96/46    | 16/26 | 32/47            | 21.96/47            | 17/23              | 39.40/93    | 17/24 | 10/15       | 11.23/17    | 18/23   |
| agent s2.5 w/ o3       | 54.2%           | 200.02/369    | 23.96/46    | 20/26 | 26/47            | 25.99/47            | 11/23              | 39.93/101   | 18/24 | 11/15       | 7.14/17     | 17/23   |

## ⚡️ Quick Start

Follow these steps to set up the environment and reproduce our results.

1.  **Set Up OSWorld Environment**:
    *   First, ensure you have a fully functional OSWorld environment. Please follow the official [OSWorld setup guide](https://github.com/x-spi/osworld) meticulously.

2.  **Install AWorld Framework**:
    *   Install the specific version of `aworld` used in our experiments.
    ```bash
    git clone https://github.com/inclusionAI/AWorld.git
    cd AWorld
    git checkout osworld_benchmark
    python setup.py install
    ```

3.  **Deploy Agent Code**:
    *   Copy the `aworldAgent` folder and the `run_multienv_aworldAgent.py` script into the root directory of your OSWorld project.

4.  **Run the Evaluation Script**:
    *   Our results were achieved using `openai/o3` for reasoning and `bytedance/ui-tars-1.5-7b` for visual grounding, both accessed via OpenRouter.
    *   Activate your conda environment and run the evaluation script. **Remember to replace placeholders like `YOUR_OPENROUTER_API_KEY` and `/path/to/your/vm/Ubuntu.vmx` with your actual credentials and paths.**

    ```bash
    # Activate your OSWorld conda environment (e.g., osworld_env)
    conda activate osworld_env

    # Run the evaluation with the recommended settings
    python run_multienv_aworldAgent.py \
        --headless \
        --ground_url YOUR_BASE_URL \
        --ground_api_key YOUR_API_KEY \
        --ground_model bytedance/ui-tars-1.5-7b \
        --ground_provider open_router \
        --model_url YOUR_BASE_URL \
        --model_api_key YOUR_API_KEY \
        --model_temperature 1.0 \
        --provider_name aws \
        --max_steps 50 \
        --model_provider open_router \
        --model openai/o3 \
        --grounding_width 1920 \
        --grounding_height 1080 \
        --test_all_meta_path evaluation_examples/test_all.json \
        --result_dir ./results \
        --observation_type screenshot \
        --num_envs 1 \
        --region us-east-1 \
        --client_password osworld-public-evaluation 
    ```

## 📂 File Structure

```
osworld/
├── aworldAgent/ # Core code for our agent
│ ├── agent.py # Main agent logic for reasoning and action generation
│ ├── grounding.py # Grounding module for visual perception of UI elements
│ ├── prompt.py # Contains all prompts used by the agent
│ ├── utils.py # Shared utility functions
│ └── workflow.py # Defines the core execution loop and workflow
├── run_multienv_aworldAgent.py # Main script to run the evaluation
├── evaluation_examples/ # Task definitions for OSWorld
├── desktop_env/ # Environment code for OSWorld
├── requirements.txt # Dependencies for OSWorld
└── ... # Other OSWorld project files
```

## ⚙️ Parameter Descriptions

The `run_multienv_aworldAgent.py` script is configured via command-line arguments. Key parameters are explained below:

| Argument              | Type  | Description                                                         | Example                               |
| --------------------- | ----- | ------------------------------------------------------------------- | ------------------------------------- |
| `--model`             | str   | The primary language model for task planning and action generation. | `"openai/o3"`                         |
| `--model_provider`    | str   | The provider of the LLM service.                                    | `"open_router"`                       |
| `--model_api_key`     | str   | API key for the LLM service.                                        | `"your-openrouter-api-key"`                      |
| `--ground_model`      | str   | The specific name of the grounding model.                           | `"bytedance/ui-tars-1.5-7b"`          |
| `--ground_provider`   | str   | The provider for the visual grounding model.                        | `"open_router"`                       |
| `--path_to_vm`        | str   | The local file path to your VMware virtual machine `.vmx` file.     | `"/path/to/your/vm/Ubuntu.vmx"`       |
| `--provider_name`     | str   | The virtualization provider.                                        | `"vmware"`                            |
| `--client_password`   | str   | The VNC password for the client VM.                                 | `"YOUR_VM_PASSWORD"`                  |
| `--max_steps`         | int   | The maximum number of steps the agent can take per task.            | `50`                                  |
| `--num_envs`          | int   | The number of parallel VM environments to run for evaluation.       | `1`                                   |

## 📊 Output Files

The evaluation process generates the following outputs:

-   **Log Files**: Stored in the `logs/` directory, containing detailed runtime information for debugging.
-   **Results Directory**: Located at the path specified by `--result_dir` (defaults to `./results`), with the following structure:
    -   `results/[action_space]/[observation_type]/[model]/[domain]/[example_id]/`
    -   `traj.jsonl`: A complete log of the agent's thought process and action sequence.
    -   `result.txt`: Contains the final score for the task (0.0 for failure, 1.0 for success).
    -   `recording.mp4`: A screen recording of the agent's execution process.

## 💡 Key Features

1.  **State-of-the-Art Performance**: Achieved the top rank on the OSWorld-verified benchmark.
2.  **Enhanced Agent Stability**: By integrating new executable tools, we have significantly improved the agent's robustness and ability to interact with the OS, building upon the AgentS2 foundation.
3.  **AWorld Framework Integration**: Leverages the modularity and scalability of the AWorld framework.
4.  **Reproducible**: Provides a clear, single-command script to facilitate result reproduction by the community.

## Acknowledgements

This work would not have been possible without building upon the foundations of several incredible open-source projects.

-   **AWorld Framework**: We thank the developers of the [AWorld Framework](https://github.com/inclusionAI/AWorld) for providing a powerful and flexible platform for agent development.
  
-   **AgentS2**: We extend our sincere gratitude to the creators of the [AgentS2 (Agent-S) project](https://github.com/simular-ai/Agent-S). The core agent logic in our implementation is adapted and enhanced from their codebase. We built upon their work by adding a suite of executable tools to improve the agent's interaction with the OS environment, which significantly boosted the stability and capability of our CUA Agent.

-   **OSWorld Benchmark**: We are grateful to the creators of the [OSWorld Benchmark](https://os-world.github.io/) for developing a challenging and comprehensive testbed for GUI agents.