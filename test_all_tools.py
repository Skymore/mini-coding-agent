#!/usr/bin/env python3
"""
Comprehensive Tool Testing Suite

Tests all tools available in the multi-agent system:
1. General tools: read_file, write_file, list_directory, find_and_replace_in_file, execute_bash_command
2. PLANNER tools: execute_safe_bash
3. Tool safety and security features
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

# Set test model to gemini flash for cost-effective testing
os.environ["LLM_MODEL"] = "google/gemini-2.5-pro"

def test_general_tools():
    """Test general tools available to CodeGenerator and CodeReviewer"""
    print("🔧 Testing General Tools")
    print("=" * 50)
    
    results = {}
    
    try:
        from multi_agent_system import read_file, write_file, list_directory, find_and_replace_in_file, execute_bash_command
        
        # Create temporary test environment
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test write_file
            print("\n📝 Testing write_file...")
            test_content = "# Test File\nprint('Hello, World!')\n"
            result = write_file.invoke({"file_path": "test_script.py", "content": test_content})
            results["write_file"] = "successfully" in result.lower()
            print(f"Result: {result[:100]}...")
            
            # Test read_file
            print("\n📖 Testing read_file...")
            result = read_file.invoke({"file_path": "test_script.py"})
            results["read_file"] = "Hello, World!" in result
            print(f"Result: {result[:100]}...")
            
            # Test list_directory
            print("\n📁 Testing list_directory...")
            result = list_directory.invoke({"directory_path": "."})
            results["list_directory"] = "test_script.py" in result
            print(f"Result: {result[:100]}...")
            
            # Test find_and_replace_in_file
            print("\n🔄 Testing find_and_replace_in_file...")
            result = find_and_replace_in_file.invoke({
                "file_path": "test_script.py",
                "find_text": "Hello, World!",
                "replace_text": "Hello, Testing!"
            })
            results["find_and_replace_in_file"] = "successfully" in result.lower()
            print(f"Result: {result[:100]}...")
            
            # Test execute_bash_command
            print("\n💻 Testing execute_bash_command...")
            result = execute_bash_command.invoke({"command": "echo 'Test command'"})
            results["execute_bash_command"] = "Test command" in result
            print(f"Result: {result[:100]}...")
            
    except Exception as e:
        print(f"❌ Error testing general tools: {e}")
        return {}
    
    return results

def test_planner_tools():
    """Test PLANNER-specific tools"""
    print("\n📋 Testing PLANNER Tools")
    print("=" * 50)

    results = {}

    try:
        from planner_node import read_file, list_directory, execute_safe_bash

        # Test with files in current working directory (sandbox)
        # Create test file in current directory
        test_file_name = "planner_test.txt"
        with open(test_file_name, "w") as f:
            f.write("PLANNER test content\nLine 2\nLine 3")

        try:
            # Test PLANNER read_file
            print("\n📖 Testing PLANNER read_file...")
            result = read_file.invoke({"file_path": test_file_name})
            results["planner_read_file"] = "PLANNER test content" in result
            print(f"Result: {result[:100]}...")

            # Test PLANNER list_directory
            print("\n📁 Testing PLANNER list_directory...")
            result = list_directory.invoke({"directory_path": "."})
            results["planner_list_directory"] = test_file_name in result
            print(f"Result: {result[:100]}...")

        finally:
            # Cleanup test file
            if os.path.exists(test_file_name):
                os.remove(test_file_name)
            
            # Test execute_safe_bash
            print("\n💻 Testing execute_safe_bash...")
            result = execute_safe_bash.invoke({"command": "pwd"})
            results["execute_safe_bash"] = "Command:" in result and "Exit Code:" in result
            print(f"Result: {result[:100]}...")
            
            # Test safe bash security
            print("\n🔒 Testing execute_safe_bash security...")
            result = execute_safe_bash.invoke({"command": "rm -rf /"})
            results["safe_bash_security"] = "rejected" in result.lower() or "denied" in result.lower()
            print(f"Result: {result[:100]}...")
            
    except Exception as e:
        print(f"❌ Error testing PLANNER tools: {e}")
        return {}
    
    return results

def test_tool_security():
    """Test tool security features"""
    print("\n🔒 Testing Tool Security")
    print("=" * 50)
    
    results = {}
    
    try:
        from planner_node import execute_safe_bash
        
        # Test dangerous commands
        dangerous_commands = [
            "rm -rf /",
            "sudo shutdown now",
            "mv important.txt /dev/null",
            "python -c 'import os; os.system(\"rm file.txt\")'",
            "ls > output.txt"
        ]
        
        security_passed = 0
        for cmd in dangerous_commands:
            print(f"\n🚫 Testing dangerous command: {cmd}")
            result = execute_safe_bash.invoke({"command": cmd})
            if "rejected" in result.lower() or "denied" in result.lower():
                security_passed += 1
                print("✅ Command properly rejected")
            else:
                print("❌ Command was not rejected!")
            
        results["security_tests"] = security_passed == len(dangerous_commands)
        
    except Exception as e:
        print(f"❌ Error testing security: {e}")
        return {}
    
    return results

def test_tool_integration():
    """Test tool integration with multi-agent system"""
    print("\n🔗 Testing Tool Integration")
    print("=" * 50)
    
    results = {}
    
    try:
        from multi_agent_system import run_multi_agent_query_stream
        
        # Note: Integration tests may fail if the LLM doesn't choose to use tools
        # This is expected behavior as LLMs make autonomous decisions
        print("Note: Integration tests verify agent behavior, which may vary")
        
        # Test queries that should use specific tools
        test_cases = [
            ("Create a simple hello.py file with a print statement that says 'Hello World'", ["write_file"]),
            ("List all files and directories in the current directory", ["list_directory"]),
            ("Read the content of the test_script.py file", ["read_file"]),
            ("Use pwd command to check the current working directory", ["execute_safe_bash"]),
        ]
        
        for query, expected_tools in test_cases:
            print(f"\n🧪 Testing: {query}")
            tools_used = []
            
            messages = [{"type": "human", "content": query}]
            event_count = 0
            for event in run_multi_agent_query_stream(messages):
                event_count += 1
                
                if event.get("type") == "message":
                    msg = event.get("message", {})
                    if msg.get("type") == "tool_call":
                        tool_name = msg.get("tool_name", "unknown")
                        tools_used.append(tool_name)
                        print(f"🔧 Used tool: {tool_name}")
                    elif msg.get("type") == "ai":
                        # Show AI response for debugging
                        content = msg.get("content", "")[:100]
                        print(f"💬 AI response: {content}...")
                elif event.get("type") == "tool_call":
                    # This is the correct structure for tool calls
                    tool_name = event.get("tool_name", "unknown")
                    tools_used.append(tool_name)
                    print(f"🔧 Used tool: {tool_name}")
                elif event.get("type") == "complete":
                    break
            
            if event_count == 0:
                print("⚠️  No events received from agent!")
            
            # Check if expected tools were used
            tools_matched = any(tool in tools_used for tool in expected_tools)
            results[f"integration_{query[:20]}"] = tools_matched
            print(f"Expected tools: {expected_tools}, Used: {tools_used}")
            
            # Note: LLMs may not always use tools as expected, especially for simple tasks
            # This is normal behavior and doesn't indicate a system failure
            
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        return {}
    
    return results

def main():
    """Run comprehensive tool testing"""
    print("🚀 Comprehensive Tool Testing Suite")
    print("=" * 80)
    print(f"🤖 Using Model: {os.getenv('LLM_MODEL', 'default')}")
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set")
        return 1
    
    all_results = {}
    
    # Run all tool tests
    print("\n" + "="*80)
    all_results.update(test_general_tools())
    
    print("\n" + "="*80)
    all_results.update(test_planner_tools())
    
    print("\n" + "="*80)
    all_results.update(test_tool_security())
    
    print("\n" + "="*80)
    all_results.update(test_tool_integration())
    
    # Summary
    print("\n📊 Tool Test Results Summary")
    print("=" * 80)
    
    for test_name, passed in all_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    total_tests = len(all_results)
    passed_tests = sum(all_results.values())
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    print(f"🤖 Model Used: {os.getenv('LLM_MODEL', 'default')}")
    
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())
