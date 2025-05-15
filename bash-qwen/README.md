# Code Agent with Dashscope Integration

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

A Python-based interactive code agent that integrates with Dashscope's LLM API to generate, execute, and debug code in real-time with safety checks.

## Features

- **Interactive Code Execution**: Run generated Python or Shell code with user confirmation
- **Automatic Error Diagnosis**: AI-powered error analysis and code fixing (up to 5 retries)
- **Safety Scanners**: Warning system for dangerous commands (e.g., `rm -rf`, `sudo`)
- **Sandboxed Execution**: Safe Python code execution environment
- **Colorized Output**: Clear terminal feedback with color-coded messages

## Prerequisites

- Python 3.7+
- Dashscope API key (set as environment variable `DASHSCOPE_API_KEY`)
- Valid Dashscope Application ID

## Installation

1. Clone the repository:
```bash
git clone https://github.com/cao-zhiming/czm-kit.git
cd czm-kit
```

2. Install dependencies:
```bash
pip install dashscope colorama
```

## Usage

1. Set your Dashscope API key as environment variable:
```bash
export DASHSCOPE_API_KEY='your-api-key-here'
```

2. Run the interactive agent:
```bash
python bash-qwen.py
```

3. In the interactive session:
- Enter your natural language prompt
- For each code block generated:
  - `[E]xecute` - Run the code
  - `[S]kip` - Move to next block
  - `[Q]uit` - Exit the program
- The system will automatically diagnose errors and suggest fixes

## Example Session

```text
=== Bash-Qwen ===
https://github.com/cao-zhiming/czm-kit

Prompt(or enter quit): Write a Python function to calculate factorial of 5

Generated PYTHON Code:
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

result = factorial(5)

[E]xecute [S]kip [Q]uit: e

=== Execution result ===
执行成功（无输出）

AI: The function has been executed successfully. The result is stored in the 'result' variable.
```

## Safety Features

The agent includes multiple safety mechanisms:
- Highlights dangerous commands before execution
- Sandboxes Python code execution
- Timeout protection for shell commands (15 seconds)
- Requires explicit user confirmation before execution

## Configuration

Edit the `APP_ID` in the source code to use your Dashscope application:
```python
APP_ID = "b35fb890210d4372b6a323193597de6d"  # Replace with your APP_ID
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.