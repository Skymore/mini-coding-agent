#!/usr/bin/env python3
"""
PLANNER Node Examples

Simple examples demonstrating PLANNER node capabilities.
"""

import os
import sys
from pathlib import Path
import dotenv

dotenv.load_dotenv()
sys.path.append(str(Path(__file__).parent))

def example_planner_analysis():
    """PLANNER: Project Analysis Example"""
    return """
    Analyze the test_sandbox project and create an improvement plan:

    The test_sandbox directory has been prepared in your working directory.

    Please:
    1. Explore the test_sandbox directory structure
    2. Read key files like README.md, requirements.txt, and source code
    3. Identify main components and architecture
    4. Suggest improvements for code organization, testing, and documentation

    Please start by listing the contents of the test_sandbox directory.
    """

def example_planner_system_exploration():
    """PLANNER: System Exploration Example"""
    return """
    Help me understand the test_sandbox codebase:

    The test_sandbox directory is ready in your working directory.

    Please analyze the project:
    1. List all files and directories in test_sandbox
    2. Read configuration files like config.yaml and requirements.txt
    3. Analyze the main source code in src/ directory
    4. Examine the test structure in tests/
    5. Create a comprehensive project overview

    Please start by exploring the test_sandbox directory structure.
    """

def example_planner_feature_planning():
    """PLANNER: Feature Planning Example"""
    return """
    Plan adding a new API module to the test_sandbox project:

    The test_sandbox directory is available in your working directory.

    Please plan the new feature:
    1. Analyze the current project structure in test_sandbox
    2. Examine existing models and utilities in src/
    3. Design a new REST API module that integrates with existing code
    4. Plan the API endpoints, request/response models
    5. Create testing strategy for the new API
    6. Update documentation to include API usage

    Please start by examining the test_sandbox project structure.
    """

def example_codegen_new_feature():
    """CODEGEN: Create New Feature Example"""
    return """
    Create a new authentication module for the test_sandbox project:

    Please implement:
    1. Create a new file src/auth.py with user authentication functions
    2. Add login, logout, and token validation functions
    3. Include proper error handling and security measures
    4. Create corresponding test file tests/test_auth.py
    5. Update the main.py to integrate the auth module

    Use the existing project structure and follow the coding patterns you see in the codebase.
    """

def example_codegen_bug_fix():
    """CODEGEN: Bug Fix Example"""
    return """
    Fix and improve the test_sandbox project:

    Please:
    1. Read the existing source code in src/
    2. Identify any potential bugs or improvements
    3. Fix import issues in src/main.py (EmailStr import)
    4. Add missing error handling in utility functions
    5. Create a simple CLI interface improvement

    Focus on making the code more robust and production-ready.
    """

def example_reviewer_code_quality():
    """REVIEWER: Code Quality Review Example"""
    return """
    Review the code quality of the test_sandbox project:

    Please:
    1. Examine all Python files in src/ directory
    2. Check for code quality issues, security vulnerabilities
    3. Review test coverage and test quality in tests/
    4. Suggest improvements for maintainability
    5. Check adherence to Python best practices

    Provide a detailed code review report with specific recommendations.
    """

def example_reviewer_security_audit():
    """REVIEWER: Security Audit Example"""
    return """
    Perform a security audit of the test_sandbox project:

    Please:
    1. Review all source code for security vulnerabilities
    2. Check configuration files for security issues
    3. Examine input validation and error handling
    4. Review dependencies in requirements.txt for known vulnerabilities
    5. Suggest security improvements and best practices

    Focus on identifying potential security risks and providing mitigation strategies.
    """



def run_example(query, name):
    """Run Example"""
    print(f"\n🚀 {name}")
    print("=" * 50)
    print(f"Query: {query.strip()[:100]}...")
    print("-" * 50)

    try:
        from multi_agent_system import run_multi_agent_query_stream

        messages = [{"type": "human", "content": query}]

        for event in run_multi_agent_query_stream(messages):
            if event.get("type") == "message":
                msg = event.get("message", {})
                msg_type = msg.get("type", "unknown")
                content = msg.get("content", "")

                if msg_type == "routing":
                    print(f"🎯 Routing: {content}")
                elif msg_type == "agent":
                    expert = msg.get("expert", "Unknown")
                    print(f"\n📋 {expert}:")
                    # Show first 300 chars
                    print(content[:300] + "..." if len(content) > 300 else content)
                elif msg_type == "tool_call":
                    tool_name = msg.get("tool_name", "unknown")
                    print(f"\n🔧 Tool: {tool_name}")
                elif msg_type == "tool_result":
                    print(f"✅ Result: {content[:200]}..." if len(content) > 200 else content)

            elif event.get("type") == "complete":
                expert = event.get("expert_used", "Unknown")
                print(f"\n✅ Completed by: {expert}")
                break

    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main Function"""
    print("🎯 Multi-Agent System Examples")
    print("=" * 60)

    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  OPENROUTER_API_KEY not set")
        return 1

    examples = [
        # PLANNER Examples
        ("PLANNER: Project Analysis", example_planner_analysis),
        ("PLANNER: System Exploration", example_planner_system_exploration),
        ("PLANNER: Feature Planning", example_planner_feature_planning),

        # CODEGEN Examples
        ("CODEGEN: New Feature", example_codegen_new_feature),
        ("CODEGEN: Bug Fix", example_codegen_bug_fix),

        # REVIEWER Examples
        ("REVIEWER: Code Quality", example_reviewer_code_quality),
        ("REVIEWER: Security Audit", example_reviewer_security_audit),
    ]

    print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i:2d}. {name}")

    print(f"\nSelect (1-{len(examples)}) or 'all':")
    try:
        choice = input("> ").strip().lower()

        if choice == 'all':
            for name, func in examples:
                query = func()
                run_example(query, name)
                print("\n" + "="*80 + "\n")
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            idx = int(choice) - 1
            name, func = examples[idx]
            query = func()
            run_example(query, name)
        else:
            print("Invalid choice")
            return 1

    except KeyboardInterrupt:
        print("\nInterrupted")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

    print("\n🎉 Examples completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
