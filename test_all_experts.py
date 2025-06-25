#!/usr/bin/env python3
"""
Comprehensive Test Suite for All Experts and Tools

Tests all experts (Coordinator, CodeGenerator, CodeReviewer, Planner) and their tools
using the gemini-2.5-flash model for cost-effective testing.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import dotenv

dotenv.load_dotenv()
sys.path.append(str(Path(__file__).parent))

# Set test model to gemini flash (cheapest available)
os.environ["LLM_MODEL"] = "google/gemini-2.5-flash"

def setup_test_environment():
    """Setup test environment with sandbox"""
    current_dir = Path(__file__).parent
    test_sandbox_src = current_dir / "test_sandbox"
    
    if not test_sandbox_src.exists():
        print("❌ test_sandbox directory not found!")
        return None
    
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp(prefix="multi_agent_test_")
    test_sandbox_dest = Path(temp_dir) / "test_sandbox"
    
    try:
        shutil.copytree(test_sandbox_src, test_sandbox_dest)
        print(f"📁 Test environment setup at: {temp_dir}")
        return temp_dir
    except Exception as e:
        print(f"❌ Failed to setup test environment: {e}")
        return None

def run_test_query(query, test_name, expected_expert=None):
    """Run a test query and validate results"""
    print(f"\n🧪 Testing: {test_name}")
    print("=" * 60)
    print(f"Query: {query[:100]}...")
    print(f"Expected Expert: {expected_expert or 'Any'}")
    print("-" * 60)
    
    try:
        from multi_agent_system import run_multi_agent_query_stream
        
        messages = [{"type": "human", "content": query}]
        expert_used = None
        tools_used = []
        success = False
        
        for event in run_multi_agent_query_stream(messages):
            if event.get("type") == "message":
                msg = event.get("message", {})
                msg_type = msg.get("type", "unknown")
                content = msg.get("content", "")
                
                if msg_type == "routing":
                    expert_used = msg.get("content", "").split()[-1] if "Routing to" in content else None
                    print(f"🎯 Routing: {content}")
                    
                elif msg_type == "tool_call":
                    tool_name = msg.get("tool_name", "unknown")
                    tools_used.append(tool_name)
                    print(f"🔧 Tool: {tool_name}")
                    
                elif msg_type == "agent":
                    expert = msg.get("expert", "Unknown")
                    print(f"📋 {expert}: {content[:200]}...")
                    
            elif event.get("type") == "complete":
                expert_used = event.get("expert_used", "Unknown")
                success = True
                break
        
        # Validate results
        result = {
            "success": success,
            "expert_used": expert_used,
            "tools_used": tools_used,
            "expected_expert": expected_expert
        }
        
        if expected_expert and expert_used != expected_expert:
            print(f"⚠️  Expected {expected_expert}, got {expert_used}")
        else:
            print(f"✅ Test completed successfully")
            
        print(f"📊 Expert: {expert_used}, Tools: {tools_used}")
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return {"success": False, "error": str(e)}

def test_coordinator():
    """Test Coordinator routing logic"""
    print("\n🎯 Testing Coordinator Routing")
    print("=" * 60)
    
    test_cases = [
        ("Create a new Python function", "CodeGenerator"),
        ("Review this code for bugs", "CodeReviewer"), 
        ("Plan a project structure", "Planner"),
        ("Analyze and create improvement plan", "Planner"),
        ("Generate a REST API", "CodeGenerator"),
        ("Check code quality", "CodeReviewer"),
    ]
    
    results = []
    for query, expected_expert in test_cases:
        result = run_test_query(query, f"Route to {expected_expert}", expected_expert)
        results.append(result)
    
    return results

def test_planner_tools():
    """Test PLANNER expert and its tools"""
    print("\n📋 Testing PLANNER Expert and Tools")
    print("=" * 60)
    
    test_cases = [
        ("List all files in test_sandbox directory", "Planner"),
        ("Read the README.md file in test_sandbox", "Planner"),
        ("Check Python version using safe bash command", "Planner"),
        ("Analyze test_sandbox project structure and create improvement plan", "Planner"),
    ]
    
    results = []
    for query, expected_expert in test_cases:
        result = run_test_query(query, f"PLANNER: {query[:50]}...", expected_expert)
        results.append(result)
    
    return results

def test_codegen_tools():
    """Test CodeGenerator expert and its tools"""
    print("\n⚡ Testing CodeGenerator Expert and Tools")
    print("=" * 60)
    
    test_cases = [
        ("Create a new file hello.py with a simple function", "CodeGenerator"),
        ("Read the test_sandbox/src/main.py file and improve it", "CodeGenerator"),
        ("Create a new utility function in test_sandbox/src/utils.py", "CodeGenerator"),
        ("Write a simple test file for the new utility", "CodeGenerator"),
    ]
    
    results = []
    for query, expected_expert in test_cases:
        result = run_test_query(query, f"CODEGEN: {query[:50]}...", expected_expert)
        results.append(result)
    
    return results

def test_reviewer_tools():
    """Test CodeReviewer expert and its tools"""
    print("\n🔎 Testing CodeReviewer Expert and Tools")
    print("=" * 60)
    
    test_cases = [
        ("Review the code quality in test_sandbox/src/", "CodeReviewer"),
        ("Check for security issues in test_sandbox project", "CodeReviewer"),
        ("Analyze test coverage in test_sandbox/tests/", "CodeReviewer"),
        ("Review Python best practices in the codebase", "CodeReviewer"),
    ]
    
    results = []
    for query, expected_expert in test_cases:
        result = run_test_query(query, f"REVIEWER: {query[:50]}...", expected_expert)
        results.append(result)
    
    return results

def main():
    """Run comprehensive test suite"""
    print("🚀 Multi-Agent System Comprehensive Test Suite")
    print("=" * 80)
    print(f"🤖 Using Model: {os.getenv('LLM_MODEL', 'default')}")
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set")
        return 1
    
    # Setup test environment
    test_env = setup_test_environment()
    if not test_env:
        return 1
    
    try:
        # Run all tests
        all_results = []
        
        all_results.extend(test_coordinator())
        all_results.extend(test_planner_tools())
        all_results.extend(test_codegen_tools())
        all_results.extend(test_reviewer_tools())
        
        # Summary
        print("\n📊 Test Results Summary")
        print("=" * 80)
        
        total_tests = len(all_results)
        successful_tests = sum(1 for r in all_results if r.get("success", False))
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {successful_tests/total_tests*100:.1f}%")
        
        # Expert usage summary
        expert_usage = {}
        for result in all_results:
            expert = result.get("expert_used", "Unknown")
            expert_usage[expert] = expert_usage.get(expert, 0) + 1
        
        print("\n🎯 Expert Usage:")
        for expert, count in expert_usage.items():
            print(f"  {expert}: {count} times")
        
        # Tool usage summary
        all_tools = []
        for result in all_results:
            all_tools.extend(result.get("tools_used", []))
        
        tool_usage = {}
        for tool in all_tools:
            tool_usage[tool] = tool_usage.get(tool, 0) + 1
        
        print("\n🔧 Tool Usage:")
        for tool, count in sorted(tool_usage.items()):
            print(f"  {tool}: {count} times")
        
        return 0 if successful_tests == total_tests else 1
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return 1
    
    finally:
        # Cleanup
        if test_env and Path(test_env).exists():
            shutil.rmtree(test_env)
            print(f"🧹 Cleaned up test environment")

if __name__ == "__main__":
    sys.exit(main())
