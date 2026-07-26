# Experiment 4.3: Execution Tools MCP Server

## Objective

Implement a comprehensive MCP server that provides execution tools with built-in safety mechanisms, demonstrating real-world best practices for AI agent tool execution.

## Experiment Overview

This experiment explores three critical aspects of execution tools:

1. **Safety Mechanisms**: LLM-based approval for dangerous operations
2. **Result Processing**: Automatic summarization of complex outputs
3. **Verification**: Automatic validation of tool execution results

## Architecture

### Safety Layer

The safety layer implements a multi-level protection system:

**LLM-Based Approval**: Before executing irreversible operations (file overwrite, system commands, external API calls), the system consults a secondary LLM to evaluate the risk. The approval process analyzes the operation for potential data loss, security risks, and resource consumption concerns. This mirrors real-world approval workflows where critical operations require managerial sign-off or risk control review.

**Result Summarization**: When execution tools (code interpreter or virtual terminal) produce output exceeding 10,000 characters, the system automatically invokes an LLM to distill the essential information. Outputs under this threshold are returned as-is to preserve full detail for smaller results. This summarization focuses on key results, errors, warnings, and actionable insights, enabling the primary agent to process information more efficiently without being overwhelmed by raw data.

**Automatic Verification**: Operations that produce verifiable outputs undergo automated validation. Code files are checked for syntax errors, terminal commands are evaluated for successful execution, and API responses are validated against expected schemas. Verification results feed back into the agent's context, allowing it to self-correct without manual intervention.

### Tool Implementation

#### File System Tools

The file system tools provide safe, verified file operations. The write operation supports automatic syntax checking for code files in Python, JavaScript, and TypeScript, preventing the creation of invalid source files. The edit operation generates diff previews before applying changes, allowing the agent to understand the impact of modifications. Both operations enforce workspace boundaries, preventing accidental file access outside designated directories.

#### Generic Execution Tools

The code interpreter executes Python code in a controlled environment with namespace restrictions. It captures both standard output and error streams, detects dangerous function calls like system commands or eval statements, and provides detailed error analysis when execution fails. The virtual terminal executes shell commands with configurable timeouts, monitors for destructive operations, and automatically summarizes verbose output to highlight relevant information.

#### External Integration Tools

The Google Calendar integration adds events with validation of datetime formats and logical consistency checks. The GitHub integration creates pull requests with branch verification and approval workflows. Both tools demonstrate patterns for safely interacting with external systems while maintaining visibility and control.

## Setup

### Prerequisites

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy environment template:
```bash
cp env.example .env
```

2. Configure your LLM provider:

```bash
PROVIDER=kimi
KIMI_API_KEY=your-key
```

**Supported Providers:**
- **SiliconFlow**: `SILICONFLOW_API_KEY` - Uses Qwen/Qwen3-235B-A22B-Thinking-2507
- **Doubao**: `DOUBAO_API_KEY` - Uses doubao-seed-1-6-thinking-250715
- **Kimi/Moonshot**: `KIMI_API_KEY` - Uses kimi-k3 (default)
- **OpenRouter**: `OPENROUTER_API_KEY` - Uses google/gemini-3.5-flash

3. (Optional) Configure external services:
```bash
# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials.json

# GitHub
GITHUB_TOKEN=your-github-token
```

### Safety Settings

```bash
# Enable/disable safety features
REQUIRE_APPROVAL_FOR_DANGEROUS_OPS=true
AUTO_SUMMARIZE_COMPLEX_OUTPUT=true
AUTO_VERIFY_CODE=true
MAX_OUTPUT_LENGTH=1000
```

## Running the Experiment

### Quick Start

```bash
python quickstart.py
```

This demonstrates all major features with minimal setup.

### Individual Tool Tests

```bash
# Test file operations
python test_file_tools.py

# Test code execution
python test_execution_tools.py

# Test external integrations (requires credentials)
python test_external_tools.py
```

### Comprehensive Examples

```bash
python examples.py
```

### Running as MCP Server

```bash
python server.py
```

The server will start in stdio mode, ready to accept MCP protocol connections.

## Experiment Results

### Safety Mechanism Evaluation

Test the approval system by attempting dangerous operations:

1. File overwrite of important files
2. Terminal commands with destructive patterns
3. Code execution with system calls

Observe how the LLM evaluates risk and makes approval decisions.

### Summarization Effectiveness

Generate complex outputs and measure summarization quality:

1. Execute commands that produce verbose output (>10,000 characters)
2. Run code that generates extensive logs
3. Verify that outputs under 10,000 characters are returned unchanged
4. Compare original vs. summarized information density for large outputs

### Verification Accuracy

Test automatic verification across different scenarios:

1. Valid code with correct syntax
2. Code with syntax errors
3. Code with runtime errors
4. Terminal commands that succeed/fail

## Key Observations

### Safety Trade-offs

The approval mechanism introduces latency as each dangerous operation requires an additional LLM call. However, this overhead prevents catastrophic failures and provides audit trails for critical actions. The system can be tuned by adjusting `REQUIRE_APPROVAL_FOR_DANGEROUS_OPS` based on trust level and use case requirements.

### Summarization Benefits

Automatic summarization significantly reduces token consumption when dealing with verbose tool outputs exceeding 10,000 characters. The LLM effectively extracts actionable information while preserving critical details. For terminal errors spanning hundreds of lines, summarization typically captures the root cause in a concise format. Outputs under the threshold are returned as-is, ensuring no information loss for moderately-sized results.

### Verification Limitations

While syntax verification catches many issues before execution, it cannot predict runtime failures or logical errors. The system works best when combined with error analysis that provides suggestions for fixing failed operations. For Python, compile-time syntax checking is highly accurate; for other languages, LLM-based validation serves as a reasonable approximation.

## Discussion Questions

1. How does LLM-based approval compare to rule-based safety checks?
2. What are the trade-offs between automation and human oversight?
3. How can verification be extended to more complex validation scenarios?
4. What metrics should be used to evaluate summarization quality?
5. How should the system handle edge cases where approval is needed but the LLM is unavailable?

## Extensions

### Suggested Improvements

1. **Caching**: Cache approval decisions for identical operations
2. **Rollback**: Implement undo functionality for file operations
3. **Sandboxing**: Use containers for true code isolation
4. **Multi-step Planning**: Break complex operations into verified steps
5. **Learning**: Train models on historical approval patterns

### Additional Tools

Consider implementing:
- Database query tools with schema validation
- API calling tools with rate limiting
- File backup/restore functionality
- Distributed execution across multiple machines

## Conclusion

This experiment demonstrates that production-ready execution tools require multiple layers of safety, verification, and result processing. The combination of LLM-based approval, automatic summarization, and verification creates a robust system suitable for real-world autonomous agent deployments. The architecture patterns shown here can be adapted to virtually any tool category where safety and reliability are paramount.
