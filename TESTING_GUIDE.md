# Multi-Agent System Testing Guide

## Overview

This guide covers comprehensive testing for all experts and tools in the multi-agent system using cost-effective models.

## Test Files

### 1. `test_all_experts.py`
Comprehensive test suite covering all experts and their routing logic.

**Features:**
- Tests all 4 experts: Coordinator, CodeGenerator, CodeReviewer, Planner
- Validates routing decisions
- Tests expert-specific capabilities
- Uses `google/gemini-2.5-flash` for cost-effective testing

**Usage:**
```bash
poetry run python test_all_experts.py
```

### 2. `test_all_tools.py`
Comprehensive tool testing suite covering all available tools.

**Features:**
- Tests general tools: `read_file`, `write_file`, `list_directory`, `find_and_replace_in_file`, `execute_bash_command`
- Tests PLANNER tools: `execute_safe_bash`
- Security testing for dangerous commands
- Integration testing with multi-agent system

**Usage:**
```bash
poetry run python test_all_tools.py
```

### 3. `test_planner_node.py`
Focused testing for PLANNER node functionality.

**Features:**
- PLANNER-specific tool tests
- System prompt validation
- Integration tests
- Safety and security tests

**Usage:**
```bash
poetry run python test_planner_node.py
```

### 4. `planner_examples.py`
Extended examples covering all experts with real scenarios.

**Features:**
- 7 comprehensive examples covering all experts
- Real-world use cases
- Interactive selection
- Automatic test_sandbox setup

**Examples:**
1. **PLANNER: Project Analysis** - Analyze project structure and create improvement plan
2. **PLANNER: System Exploration** - Understand codebase architecture
3. **PLANNER: Feature Planning** - Plan new feature implementation
4. **CODEGEN: New Feature** - Create authentication module
5. **CODEGEN: Bug Fix** - Fix and improve existing code
6. **REVIEWER: Code Quality** - Review code quality and best practices
7. **REVIEWER: Security Audit** - Perform security vulnerability assessment

**Usage:**
```bash
poetry run python planner_examples.py
```

## Expert Coverage

### 🎯 Coordinator
- **Role**: Routes queries to appropriate experts
- **Tools**: None (routing only)
- **Tests**: Routing logic validation

### ⚡ CodeGenerator
- **Role**: Creates and implements code solutions
- **Tools**: `write_file`, `find_and_replace_in_file`, `read_file`, `list_directory`, `execute_bash_command`
- **Tests**: File creation, code generation, bug fixes

### 🔎 CodeReviewer
- **Role**: Reviews code quality and security
- **Tools**: `read_file`, `list_directory`, `find_and_replace_in_file`, `execute_bash_command`
- **Tests**: Code analysis, security audits, quality reviews

### 📋 Planner
- **Role**: Analyzes tasks and creates execution plans
- **Tools**: `read_file`, `list_directory`, `execute_safe_bash`
- **Tests**: Project analysis, system exploration, feature planning

## Tool Coverage

### General Tools
- **`read_file`**: Read and analyze file contents
- **`write_file`**: Create new files with content
- **`list_directory`**: Explore directory structures
- **`find_and_replace_in_file`**: Modify existing files precisely
- **`execute_bash_command`**: Run system commands

### PLANNER Tools
- **`execute_safe_bash`**: Execute whitelisted safe commands only

## Security Testing

### Command Whitelisting
Tests that dangerous commands are properly rejected:
- `rm -rf /`
- `sudo shutdown now`
- `mv important.txt /dev/null`
- `python -c 'import os; os.system("rm file.txt")'`
- `ls > output.txt`

### Path Validation
Tests that directory traversal attempts are blocked.

### Timeout Protection
Validates that long-running commands are terminated.

## Cost-Effective Testing

All tests use `google/gemini-2.5-flash` model for:
- ✅ Lower cost per token
- ✅ Fast response times
- ✅ Sufficient capability for testing
- ✅ Reliable routing and tool usage

## Test Environment

### Automatic Setup
- `test_sandbox` directory automatically copied to output directory
- Realistic project structure for testing
- Safe sandboxed environment

### Test Sandbox Structure
```
test_sandbox/
├── README.md              # Project documentation
├── requirements.txt       # Dependencies
├── config.yaml           # Configuration
├── src/                   # Source code
│   ├── __init__.py
│   ├── main.py           # Main application
│   ├── models.py         # Data models
│   └── utils.py          # Utilities
├── tests/                # Test files
│   ├── __init__.py
│   ├── test_main.py
│   └── test_utils.py
├── docs/                 # Documentation
│   ├── api.md
│   └── setup.md
└── scripts/              # Build scripts
    └── deploy.sh
```

## Running All Tests

### Quick Test Suite
```bash
# Run all tests in sequence
poetry run python test_planner_node.py
poetry run python test_all_tools.py
poetry run python test_all_experts.py
```

### Interactive Examples
```bash
# Run interactive examples
poetry run python planner_examples.py
```

### Environment Setup
```bash
# Required environment variable
export OPENROUTER_API_KEY="your-api-key"

# Optional: Override test model
export LLM_MODEL="google/gemini-2.5-flash"
```

## Expected Results

### Success Metrics
- **Expert Routing**: 100% correct routing to intended experts
- **Tool Execution**: All tools execute successfully
- **Security**: All dangerous commands properly rejected
- **Integration**: Seamless expert-tool interaction

### Performance
- **Response Time**: < 30 seconds per test
- **Cost**: Minimal token usage with gemini-flash
- **Reliability**: Consistent results across runs

## Troubleshooting

### Common Issues
1. **API Key Missing**: Set `OPENROUTER_API_KEY` environment variable
2. **Model Not Found**: Verify model name in OpenRouter
3. **Permission Errors**: Check file permissions in test environment
4. **Tool Failures**: Review tool parameter formats

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

*This testing guide ensures comprehensive coverage of all multi-agent system components with cost-effective and reliable testing strategies.*
