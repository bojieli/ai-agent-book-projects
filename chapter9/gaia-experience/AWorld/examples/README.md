# AWorld Examples

This directory contains a wide range of examples demonstrating the capabilities of the AWorld framework. 
The examples cover single-agent and multi-agent scenarios. Each subdirectory focuses on a specific paradigm or 
application area, making it easy for developers to explore and extend.

## Directory Overview

- **common/**  
  Shared tools, utilities, and components used by other examples.

- **multi_agents/**  
  Multi-agent system examples demonstrating three core paradigms:  
  - **collaborative/**: Agents working together (e.g., debate, travel planning)  
  - **coordination/**: Orchestrated agent teams (e.g., master-worker, deep research)  
  - **workflow/**: Multi-agent workflow automation (e.g., search and summary)  
  See `multi_agents/README.md` for details.

- **web/**  
  Aworld web for visual interaction.

  **Run agent in build-in WebUI**

  - **Configure Environment**: Navigate to `examples/web/agent_deploy/` and you'll find 3 demo agents: `single_agent`, `team_agent`, and `deep_research`. Copy `.env.template` to `.env` in your chosen agent directory, then update the configuration values with your own settings.
  - **Launch WebUI**: Start the web server by running: `cd examples/web/ && aworld web`

## Application Overview

- **browser_use/**  
  Agents specialized in web browser, capable of browsing, interacting with, and extracting information from web pages.

- **BFCL/**  
  Demonstrates Basic Function Call Learning using a virtual file system and MCP tools. Useful for generating training data and testing function call synthesis.

- **gaia/**  
  Advanced agent runner and server examples, including integration with MCP collections and OpenWebUI.

- **gym_demo/**  
  Example of using an agent to interact with OpenAI Gym environments, such as CartPole, to showcase reinforcement learning and environment control.

- **phone_use/**  
  Examples of agents for Android device, including app operation, UI analysis, and task execution.

- **text_to_audio/**  
  Example of text-to-audio conversion using MCP servers and agents.


## Usage

Create .env file in the examples' dir, the file content is the environment variables required for runtime, 
such as LLM_MODEL_NAME, LLM_API_KEY, LLM_BASE_URL, LLM_TEMPERATURE = 0.0 etc.

- Each subdirectory contains its own entry point (usually `run.py`) and may include additional configuration or requirements files.
- Before running any example, ensure you have installed all required dependencies and set the necessary environment variables (e.g., LLM provider credentials, API keys).
- For detailed instructions, refer to the README or comments within each subdirectory.

---

If you need more detailed usage instructions or want to add new examples, refer to the documentation and code samples in each subdirectory. 