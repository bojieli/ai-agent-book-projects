# Building and Running Agents

In AWorld's design, both Workflows and Multi-Agent Systems (MAS) are complex systems built around Agents as the core
component. Using the most common llm_agent as an example, this tutorial provides detailed guidance on:

1. How to quickly build an Agent
2. How to customize an Agent
   This document is divided into two parts to explain AWorld's design philosophy.

## Part 1: Quick Agent Setup

### Declaring an Agent

```python
from aworld.agents.llm_agent import Agent

# Assign a name to your agent
agent = Agent(name="my_agent")
```

### Configuring LLM

#### Method 1: Using Environment Variables

```python
import os

## Set up LLM service using environment variables
os.environ["LLM_PROVIDER"] = "openai"  # Choose from: openai, anthropic, azure_openai
os.environ["LLM_MODEL_NAME"] = "gpt-4"
os.environ["LLM_API_KEY"] = "your-api-key"
os.environ["LLM_BASE_URL"] = "https://api.openai.com/v1"  # Optional for OpenAI
```

#### Method 2: Using AgentConfig

```python
import os
from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig

agent_config = AgentConfig(
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_model_name=os.getenv("LLM_MODEL_NAME"),
    llm_base_url=os.getenv("LLM_BASE_URL"),
    llm_api_key=os.getenv("LLM_API_KEY"),
)

agent = Agent(name="my_agent", conf=agent_config)
```

#### Method 3: Using Shared ModelConfig

When multiple agents use the same LLM service, you can specify a shared ModelConfig:

```python
import os
from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig, ModelConfig

# Create a shared model configuration
model_config = ModelConfig(
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_model_name=os.getenv("LLM_MODEL_NAME"),
    llm_base_url=os.getenv("LLM_BASE_URL"),
    llm_api_key=os.getenv("LLM_API_KEY"),
)

# Use the shared model config in agent configuration
agent_config = AgentConfig(
    llm_config=model_config,
)

agent = Agent(name="my_agent", conf=agent_config)
```

### Configuring Prompts

```python
from aworld.agents.llm_agent import Agent
import os
from aworld.config.conf import AgentConfig, ModelConfig

model_config = ModelConfig(
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_model_name=os.getenv("LLM_MODEL_NAME"),
    llm_base_url=os.getenv("LLM_BASE_URL"),
    llm_api_key=os.getenv("LLM_API_KEY"),
)

agent_config = AgentConfig(
    llm_config=model_config,
)

# Define your system prompt
system_prompt = """You are a helpful AI assistant that can assist users with various tasks.
You should be polite, accurate, and provide clear explanations."""

agent = Agent(
    name="my_agent",
    conf=agent_config,
    system_prompt=system_prompt
)
```

### Configuring Tools

#### Local Tools

```python
from aworld.agents.llm_agent import Agent
import os
from aworld.config.conf import AgentConfig, ModelConfig
from aworld.core.tool.func_to_tool import be_tool

model_config = ModelConfig(
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_model_name=os.getenv("LLM_MODEL_NAME"),
    llm_base_url=os.getenv("LLM_BASE_URL"),
    llm_api_key=os.getenv("LLM_API_KEY"),
)

agent_config = AgentConfig(
    llm_config=model_config,
)

system_prompt = """You are a helpful agent with access to various tools."""


# Define a local tool using the @be_tool decorator

@be_tool(tool_name='greeting_tool', tool_desc="A simple greeting tool that returns a hello message")
def greeting_tool() -> str:
    return "Hello, world!"


agent = Agent(
    name="my_agent",
    conf=agent_config,
    system_prompt=system_prompt,
    tool_names=['greeting_tool']
)
```

#### MCP (Model Context Protocol) Tools

```python
from aworld.agents.llm_agent import Agent
import os
from aworld.config.conf import AgentConfig, ModelConfig

model_config = ModelConfig(
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_model_name=os.getenv("LLM_MODEL_NAME"),
    llm_base_url=os.getenv("LLM_BASE_URL"),
    llm_api_key=os.getenv("LLM_API_KEY"),
)

agent_config = AgentConfig(
    llm_config=model_config,
)

system_prompt = """You are a helpful agent with access to file system operations."""

# Configure MCP servers

mcp_config = {
    "mcpServers": {
        "GorillaFileSystem": {
            "type": "stdio",
            "command": "python",
            "args": ["examples/BFCL/mcp_tools/gorilla_file_system.py"],
        },
    }
}

agent = Agent(
    name="my_agent",
    conf=agent_config,
    system_prompt=system_prompt,
    mcp_servers=list(mcp_config.get("mcpServers", {}).keys()),
    mcp_config=mcp_config
)
```

#### Agent as Tool

```python
from aworld.agents.llm_agent import Agent
import os
from aworld.config.conf import AgentConfig, ModelConfig

model_config = ModelConfig(
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_model_name=os.getenv("LLM_MODEL_NAME"),
    llm_base_url=os.getenv("LLM_BASE_URL"),
    llm_api_key=os.getenv("LLM_API_KEY"),
)

agent_config = AgentConfig(
    llm_config=model_config,
)

system_prompt = """You are a helpful agent that can delegate tasks to other specialized agents."""

# Create a specialized tool agent
tool_agent = Agent(name="tool_agent", conf=agent_config)

# Create the main agent that can use the tool agent
agent = Agent(
    name="my_agent",
    conf=agent_config,
    system_prompt=system_prompt,
    agent_names=['tool_agent']
)
```

## Part 2: Customizing Agents

### Customizing Agent Input

Override the `init_observation()` function to customize how your agent processes initial observations:

```python
async def init_observation(self, observation: Observation) -> Observation:
    # You can add extended information from other agents or third-party storage
    # For example, enrich the observation with additional context
    observation.metadata = {"timestamp": time.time(), "source": "custom"}
    return observation
```

### Customizing Model Input

Override the `async_messages_transform()` function to customize how messages are transformed before being sent to the
model:

```python
async def async_messages_transform(self,
                                   image_urls: List[str] = None,
                                   observation: Observation = None,
                                   message: Message = None,
                                   **kwargs) -> List[Dict[str, Any]]:
    """
    Transform input data into the format expected by the LLM.
    
    Args:
         image_urls: List of images encoded using base64
         observation: Observation from the environment
         message: Event received by the Agent
    """
    messages = []

    # Add system context
    if hasattr(self, 'system_prompt'):
        messages.append({"role": "system", "content": self.system_prompt})

    # Add user message
    if message and message.content:
        messages.append({"role": "user", "content": message.content})

    # Add images if present
    if image_urls:
        for img_url in image_urls:
            messages.append({
                "role": "user",
                "content": [{"type": "image_url", "image_url": {"url": img_url}}]
            })

    return messages
```

### Customizing Model Logic
Override the `invoke_model()` function to implement custom model logic:
```python
async def invoke_model(self,
                       messages: List[Dict[str, str]] = [],
                       message: Message = None,
                       **kwargs) -> ModelResponse:
    """Custom model invocation logic.
       You can use neural networks, rule-based systems, or any other business logic.
    """

      # Example: Use a custom model or business logic
      if self.use_custom_logic:
          # Your custom logic here
          response_content = self.custom_model.predict(messages)
      else:
          # Use the default LLM
          response_content = await self.llm_client.chat_completion(messages)
      
      return ModelResponse(
          id=f"response_{int(time.time())}",
          model=self.model_name,
          content=response_content,
          tool_calls=None  # Set if tool calls are present
      )
```

### Customizing Model Output
Create a custom `ModelOutputParser` class and specify it using the `model_output_parser` parameter:
```python
from aworld.models.model_output_parser import ModelOutputParser


class CustomOutputParser(ModelOutputParser[ModelResponse, AgentResult]):
    async def parse(self, resp: ModelResponse, **kwargs) -> AgentResult:
        """Custom parsing logic based on your model's API response format."""

         # Extract relevant information from the model response
         content = resp.content
         tool_calls = resp.tool_calls
         
         # Create your custom AgentResult
         result = AgentResult(
             content=content,
             tool_calls=tool_calls,
             metadata={"parsed_at": time.time()}
         )
         
         return result

# Use the custom parser

agent = Agent(
    name="my_agent",
    conf=agent_config,
    model_output_parser=CustomOutputParser()
)
```
### Customizing Agent Response
Override the `async_post_run()` function to customize how your agent responds:
```python
from aworld.core.message import Message

class CustomMessage(Message):
      def __init__(self, content: str, custom_field: str = None):
            super().__init__(content=content)
            self.custom_field = custom_field
      
async def async_post_run(self,
                        policy_result: List[ActionModel],
                        policy_input: Observation,
                        message: Message = None) -> Message:
      """
      Customize the agent's response after processing.
      """
      
      # Process the policy result and create a custom response
      response_content = f"Processed {len(policy_result)} actions"
      custom_field = "custom_value"
      
       return CustomMessage(
           content=response_content,
           custom_field=custom_field
       )
```

### Custom Response Parsing
If the framework doesn't support your response structure, you can create a custom response parser:
```python
from aworld.runners import HandlerFactory
from aworld.runners.default_handler import DefaultHandler

# Define a custom handler name
custom_name = "custom_handler"


@HandlerFactory.register(name=custom_name)
class CustomHandler(DefaultHandler):
    def is_valid_message(self, message: Message):
        """Check if this handler should process the message."""
        return message.category == custom_name


async def _do_handle(self, message: Message) -> AsyncGenerator[Message, None]:
    """Custom message processing logic."""
    if not self.is_valid_message(message):
        return

    # Implement your custom message processing logic here
    processed_message = self.process_custom_message(message)
    yield processed_message


# Use the custom handler
agent = Agent(
    name="my_agent",
    conf=agent_config,
    event_handler_name=custom_name
)
```
**Important Note:** The `custom_name` variable value must remain consistent across your handler registration and agent
configuration.