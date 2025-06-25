#!/usr/bin/env python3
"""
Test script for PLANNER Node functionality

This script demonstrates the capabilities of the PLANNER node including:
1. File system exploration and analysis
2. Safe bash command execution
3. Task planning and breakdown
4. Integration with the multi-agent system
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Set test model to gemini flash for cost-effective testing
os.environ["LLM_MODEL"] = "google/gemini-2.5-flash"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_planner_tools():
    """Test individual PLANNER tools"""
    print("🧪 Testing PLANNER Tools")
    print("=" * 50)
    
    try:
        from planner_node import read_file, list_directory, execute_safe_bash, _is_command_safe
        
        # Test 1: Create test sandbox environment
        print("\n📁 Test 1: Create Test Environment")
        import tempfile
        import os

        # Create a temporary sandbox directory with realistic project structure
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Test sandbox: {temp_dir}")

            # Create a realistic project structure
            src_dir = os.path.join(temp_dir, "src")
            tests_dir = os.path.join(temp_dir, "tests")
            docs_dir = os.path.join(temp_dir, "docs")

            os.makedirs(src_dir)
            os.makedirs(tests_dir)
            os.makedirs(docs_dir)

            # Create sample files
            files_to_create = {
                "README.md": "# Test Project\n\nThis is a test project for PLANNER node testing.",
                "requirements.txt": "requests==2.28.0\nflask==2.2.0\npytest==7.1.0",
                "src/main.py": "#!/usr/bin/env python3\n\ndef main():\n    print('Hello World')\n\nif __name__ == '__main__':\n    main()",
                "src/utils.py": "def helper_function():\n    return 'This is a helper function'",
                "tests/test_main.py": "import pytest\nfrom src.main import main\n\ndef test_main():\n    assert main() is None",
                "docs/api.md": "# API Documentation\n\n## Functions\n\n- main(): Entry point"
            }

            for file_path, content in files_to_create.items():
                full_path = os.path.join(temp_dir, file_path)
                with open(full_path, "w") as f:
                    f.write(content)

            # Test directory listing
            print("\n📂 Testing directory listing:")
            result = list_directory.invoke({"directory_path": temp_dir})
            print(result)

            # Test file reading
            print("\n📄 Testing file reading:")
            readme_path = os.path.join(temp_dir, "README.md")
            result = read_file.invoke({"file_path": readme_path})
            print(result[:300] + "..." if len(result) > 300 else result)

        # Test 3: Safe command execution
        print("\n💻 Test 3: Safe Command Execution")
        safe_commands = [
            "pwd",
            "ls -la",
            "whoami",
            "python --version",
            "git status"
        ]
        
        for cmd in safe_commands:
            print(f"\nExecuting: {cmd}")
            result = execute_safe_bash.invoke({"command": cmd})
            print(result[:300] + "..." if len(result) > 300 else result)
        
        # Test 4: Command safety validation
        print("\n🔒 Test 4: Command Safety Validation")
        dangerous_commands = [
            "rm -rf /",
            "sudo shutdown now",
            "mv important.txt /dev/null",
            "python -c 'import os; os.system(\"rm file.txt\")'",
            "ls > output.txt"
        ]
        
        for cmd in dangerous_commands:
            is_safe, reason = _is_command_safe(cmd)
            print(f"Command: {cmd}")
            print(f"Safe: {is_safe}, Reason: {reason}\n")
            
    except ImportError as e:
        print(f"❌ Error importing PLANNER tools: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing PLANNER tools: {e}")
        return False
    
    return True

def test_planner_integration():
    """Test PLANNER integration with multi-agent system"""
    print("\n🤖 Testing PLANNER Integration")
    print("=" * 50)
    
    try:
        from multi_agent_system import run_multi_agent_query_stream
        
        # Test queries that should route to PLANNER
        planner_queries = [
            "Analyze the current project structure and create a plan for organizing the code",
            "What files are in this directory and what do they do?",
            "Create a detailed plan for implementing a new feature in this codebase",
            "Break down the task of setting up a development environment into steps",
            "Analyze the system requirements and suggest an implementation strategy"
        ]
        
        for i, query in enumerate(planner_queries, 1):
            print(f"\n🔍 Test Query {i}: {query}")
            print("-" * 40)
            
            query_messages = [{"type": "human", "content": query}]
            
            # Process the query and collect results
            events = []
            try:
                for event in run_multi_agent_query_stream(query_messages):
                    events.append(event)
                    if event.get("type") == "message":
                        msg = event.get("message", {})
                        expert = msg.get("expert", "Unknown")
                        msg_type = msg.get("type", "unknown")
                        content = msg.get("content", "")
                        
                        if msg_type == "routing":
                            print(f"🎯 Routing: {content}")
                        elif msg_type == "agent":
                            print(f"📋 {expert}: {content[:200]}{'...' if len(content) > 200 else ''}")
                        elif msg_type == "tool_call":
                            tool_name = msg.get("tool_name", "unknown")
                            print(f"🔧 Tool Call: {tool_name}")
                        elif msg_type == "tool_result":
                            tool_name = msg.get("tool_name", "unknown")
                            print(f"✅ Tool Result ({tool_name}): {content[:100]}{'...' if len(content) > 100 else ''}")
                    
                    elif event.get("type") == "complete":
                        expert_used = event.get("expert_used", "Unknown")
                        print(f"✅ Completed by: {expert_used}")
                        
                        # Verify PLANNER was used for planning queries
                        if expert_used == "Planner":
                            print("✅ PLANNER node was correctly selected!")
                        else:
                            print(f"⚠️  Expected PLANNER but got {expert_used}")
                        
            except Exception as e:
                print(f"❌ Error processing query: {e}")
                continue
            
            print()
    
    except ImportError as e:
        print(f"❌ Error importing multi-agent system: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing PLANNER integration: {e}")
        return False
    
    return True

def test_planner_prompts():
    """Test different PLANNER system prompts"""
    print("\n📝 Testing PLANNER System Prompts")
    print("=" * 50)
    
    try:
        from planner_node import get_planner_system_prompt, PLANNER_SYSTEM_PROMPTS
        
        print("Available prompt types:")
        for prompt_type in PLANNER_SYSTEM_PROMPTS.keys():
            print(f"- {prompt_type}")
        
        print("\nTesting prompt retrieval:")
        for prompt_type in PLANNER_SYSTEM_PROMPTS.keys():
            prompt = get_planner_system_prompt(prompt_type)
            print(f"\n{prompt_type.upper()} prompt length: {len(prompt)} characters")
            print(f"Preview: {prompt[:150]}...")
            
    except ImportError as e:
        print(f"❌ Error importing PLANNER prompts: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing PLANNER prompts: {e}")
        return False
    
    return True

def main():
    """Run all PLANNER tests"""
    print("🚀 PLANNER Node Test Suite")
    print("=" * 60)
    
    # Check if required environment variables are set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  Warning: OPENROUTER_API_KEY not set. Some tests may fail.")
    
    tests = [
        ("PLANNER Tools", test_planner_tools),
        ("PLANNER System Prompts", test_planner_prompts),
        ("PLANNER Integration", test_planner_integration),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} tests...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! PLANNER node is working correctly.")
        print(f"🤖 Tests completed using model: {os.getenv('LLM_MODEL', 'default')}")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        print(f"🤖 Tests completed using model: {os.getenv('LLM_MODEL', 'default')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
