# User Memory Evaluation Framework

A comprehensive evaluation framework for testing AI agents' memory capabilities across three progressive levels of complexity. This framework uses realistic business conversation scenarios to assess whether agents can effectively store, retrieve, and utilize information from user interactions.

## Overview

The framework evaluates agent memory systems through three distinct layers:

### Layer 1: Basic Recall & Direct Retrieval
Tests the agent's ability to accurately store and retrieve explicit, unambiguous information from a single conversation. Examples include account numbers, confirmation codes, and appointment details.

### Layer 2: Contextual Reasoning & Disambiguation  
Evaluates the agent's capability to handle ambiguous requests by retrieving ALL relevant information from multiple conversations and recognizing when clarification is needed. The agent must understand context and avoid making assumptions.

### Layer 3: Cross-Session Synthesis & Proactive Assistance
Assesses whether the agent can synthesize information across multiple conversations over time, identify critical connections, and provide proactive assistance without being explicitly asked.

## Features

- **60 Realistic Test Cases**: 20 test cases per layer, each containing 50+ rounds of authentic business conversations
- **LLM-as-Judge Evaluation**: Uses AI to evaluate semantic understanding rather than exact string matching
- **Comprehensive Scenarios**: Covers banking, insurance, healthcare, travel, retail, and more
- **Flexible Framework**: Supports interactive, batch, and programmatic evaluation modes
- **Detailed Reporting**: Generates comprehensive evaluation reports with scores and insights

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure evaluator API (Kimi or OpenAI):
```bash
cp env.example .env
# Edit .env with your API credentials
```

## Usage

### Interactive Mode

Run the interactive evaluation interface:

```bash
python main.py --mode interactive
```

This provides a menu-driven interface to:
- Browse and view test cases
- Run individual evaluations
- Submit agent responses manually
- Generate evaluation reports

### Demo Mode

See example evaluations with sample responses:

```bash
python main.py --mode demo
```

### Batch Mode

Evaluate multiple test cases programmatically:

```bash
python main.py --mode batch --responses agent_responses.json
```

The JSON file should map test IDs to agent responses:
```json
{
  "layer1_01_bank_account": "Your checking account number is 4429853327.",
  "layer1_02_insurance_claim": "Your claim number is CLM-2024-894327..."
}
```

### Programmatic Usage

```python
from framework import UserMemoryEvaluationFramework

# Initialize framework
framework = UserMemoryEvaluationFramework()

# List test cases
test_cases = framework.list_test_cases(category="layer1")

# Get conversation histories for a test
histories = framework.get_conversation_histories("layer1_01_bank_account")

# Get user question
question = framework.get_user_question("layer1_01_bank_account")

# Submit agent response for evaluation
result = framework.submit_and_evaluate(
    test_id="layer1_01_bank_account",
    agent_response="Your checking account number is 4429853327.",
    extracted_memory=None  # Optional
)

# Check results
print(f"Reward: {result.reward:.3f}")  # Continuous score from 0.0 to 1.0
print(f"Passed: {result.reward >= 0.6}")  # Pass if reward >= 0.6
print(f"Reasoning: {result.reasoning}")
```

## Test Case Structure

Each test case contains:

- **test_id**: Unique identifier
- **category**: layer1, layer2, or layer3
- **title**: Descriptive title
- **conversation_histories**: One or more realistic conversations (50+ rounds each)
- **user_question**: The question posed to the agent
- **evaluation_criteria**: What the agent should retrieve/understand
- **expected_behavior**: Ideal agent response

### Example Test Case Scenarios

**Layer 1 Examples:**
- Bank account setup with account numbers
- Insurance claim with confirmation details  
- Medical appointment scheduling
- Airline reservations with seat assignments
- Internet service installation

**Layer 2 Examples:**
- Multiple vehicles requiring disambiguation
- Several credit cards with different benefits
- Multiple properties or insurance policies
- Family members with separate accounts

**Layer 3 Examples:**
- Passport expiring before booked international travel
- Insurance coverage for planned medical procedure
- Tax documents needed from various past conversations
- Home warranty coverage for reported issue

## Evaluation Metrics

The framework evaluates based on:

1. **Information Retrieval**: Did the agent find the required information?
2. **Completeness**: For ambiguous queries, did it retrieve ALL relevant information?
3. **Accuracy**: Is the retrieved information correct?
4. **Context Understanding**: Does the agent understand the situation?
5. **Proactive Assistance**: Does it identify unstated but relevant connections?

## Configuration

Edit `config.py` or `.env` file:

```python
# Evaluator LLM Settings
KIMI_API_KEY=your_key_here
DEFAULT_EVALUATOR=kimi  # or openai
MAX_RETRIES=3
REQUEST_TIMEOUT=60
```

## Extending the Framework

### Adding New Test Cases

Create YAML files in the appropriate category folder:

```yaml
test_id: layer1_new_case
category: layer1
title: New Test Case Title
conversation_histories:
  - conversation_id: conv_001
    timestamp: "2024-11-20 10:00:00"
    messages:
      - role: user
        content: "User message"
      - role: assistant
        content: "Assistant response"
      # ... 50+ rounds
user_question: "What information should I retrieve?"
evaluation_criteria:
  description: "What to evaluate"
  required_information:
    - "Key piece of information"
  success_indicators:
    - "Signs of success"
expected_behavior: "Ideal response"
```

### Custom Evaluators

Extend the `LLMEvaluator` class:

```python
class CustomEvaluator(LLMEvaluator):
    def evaluate(self, test_case, agent_response, extracted_memory=None):
        # Custom evaluation logic
        return EvaluationResult(...)
```

## Requirements

- Python 3.8+
- API key for Kimi or OpenAI
- 8GB+ RAM for loading conversation histories

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Areas for improvement:
- Additional test cases for specific industries
- Support for more evaluator LLMs
- Multi-language test cases
- Performance optimizations for large-scale evaluations

## Citation

If you use this framework in your research, please cite:

```
User Memory Evaluation Framework
A comprehensive testing suite for AI agent memory systems
https://github.com/your-repo/user-memory-evaluation
```
