from typing import TypedDict, Annotated, Literal, List, Dict, Any, Union, cast
import operator
import os
import httpx
import uuid
import json
import logging
import functools
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from pydantic import SecretStr, BaseModel
import subprocess
import ast
from pathlib import Path
import re
import difflib

# Configure logging for this module
logger = logging.getLogger(__name__)

# Load environment variables
# Always load .env located alongside this file, regardless of CWD
load_dotenv(Path(__file__).resolve().parent / ".env")

# Each run gets its own subfolder inside `output` to avoid collisions
BASE_OUTPUT_DIR = os.path.join(os.getcwd(), "output")
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

from datetime import datetime

# Timestamp-based session folder (e.g., 20250623_163601_123456)
SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, SESSION_ID)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Path for sandboxing. All file operations will be restricted to this directory.
_secure_base_dir = Path(OUTPUT_DIR).resolve()

# Copy test_sandbox if it exists for PLANNER examples
def setup_test_sandbox():
    """Copy test_sandbox directory to output directory for PLANNER examples"""
    import shutil
    current_dir = Path(__file__).parent
    test_sandbox_src = current_dir / "test_sandbox"
    test_sandbox_dest = _secure_base_dir / "test_sandbox"

    if test_sandbox_src.exists() and test_sandbox_src.is_dir():
        try:
            if test_sandbox_dest.exists():
                shutil.rmtree(test_sandbox_dest)
            shutil.copytree(test_sandbox_src, test_sandbox_dest)
            print(f"📁 Copied test_sandbox to output directory for examples")
        except Exception as e:
            print(f"⚠️  Failed to copy test_sandbox: {e}")

# Setup test environment
setup_test_sandbox()

# Informative print for server logs
print(f"🗂️  Output directory for this session: {OUTPUT_DIR}")

# --- Message Types for API ---
class MessageInput(BaseModel):
    role: str
    content: str

# Tool descriptions are now in the @tool decorators' docstrings

# --- Expert Agent Definitions ---
EXPERT_DEFINITIONS = {
    "Coordinator": {
        "name": "Coordinator",
        "description": "Analyzes requests and routes them to the most appropriate specialist agent",
        "icon": "🎯",
        "tools": []  # Coordinator doesn't use tools directly
    },
    "CodeGenerator": {
        "name": "Code Generator",
        "description": "Generates code solutions based on requirements and specifications",
        "icon": "⚡",
        "tools": ["write_file", "find_and_replace_in_file", "read_file", "list_directory", "execute_bash_command"]
    },
    "CodeReviewer": {
        "name": "Code Reviewer",
        "description": "Reviews code quality, security, and adherence to best practices",
        "icon": "🔎",
        "tools": ["read_file", "list_directory", "find_and_replace_in_file", "execute_bash_command"]
    },
    "Planner": {
        "name": "Planner",
        "description": "Analyzes complex tasks and creates detailed execution plans with file system awareness",
        "icon": "📋",
        "tools": ["read_file", "list_directory", "execute_safe_bash"]
    }
}

# --- Sandboxing Helper ---
def _get_safe_path(file_path: str) -> Path:
    """
    Resolves a user-provided path against the secure base directory
    and ensures it does not escape the sandbox.
    """
    # Normalize and resolve the path
    safe_path = (_secure_base_dir / file_path).resolve()

    # Check if the resolved path is within the secure base directory
    if not str(safe_path).startswith(str(_secure_base_dir)):
        raise ValueError(f"Path traversal attempt detected. Access to '{file_path}' is denied.")

    return safe_path

# --- Diff Helper ---
def _generate_diff(before_content: str, after_content: str, file_path: str) -> Dict[str, Any]:
    """
    Generate diff information between before and after content.

    Returns:
        Dict containing diff text, added lines, removed lines, and statistics
    """
    before_lines = before_content.splitlines(keepends=True)
    after_lines = after_content.splitlines(keepends=True)

    # Generate unified diff
    diff_lines = list(difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=""
    ))

    # Count added and removed lines
    added_lines = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
    removed_lines = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

    return {
        "diff_text": ''.join(diff_lines),
        "added_lines": added_lines,
        "removed_lines": removed_lines,
        "total_changes": added_lines + removed_lines
    }

# --- Core Development Tools ---

@tool
def read_file(
    file_path: str,
    start_line_one_indexed: int | None = None,
    end_line_one_indexed_inclusive: int | None = None
) -> str:
    """
    Read and analyze file contents. Can read the entire file or a specific line range.
    Use this to examine existing code, config files, or any text-based files.

    Args:
        file_path: Path to the file to read.
        start_line_one_indexed: Optional: The 1-indexed line number to start reading from.
        end_line_one_indexed_inclusive: Optional: The 1-indexed line number to end reading at (inclusive).

    Returns:
        String containing the file contents or the specified line range.
    """
    try:
        safe_path = _get_safe_path(file_path)
        with open(safe_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if start_line_one_indexed is not None and end_line_one_indexed_inclusive is not None:
            # Adjust for 0-based indexing
            start_idx = start_line_one_indexed - 1
            end_idx = end_line_one_indexed_inclusive
            
            # Clamp values to be within bounds
            start_idx = max(0, start_idx)
            end_idx = min(len(lines), end_idx)
            
            if start_idx >= end_idx:
                return f"Error: Invalid line range for {file_path}. Start line must be before end line."

            content = "".join(lines[start_idx:end_idx])
            return f"File contents of {file_path} (lines {start_line_one_indexed}-{end_line_one_indexed_inclusive}):\n\n{content}"
        else:
            content = "".join(lines)
            return f"File contents of {file_path} (entire file):\n\n{content}"
            
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"

@tool
def write_file(file_path: str, content: str) -> str:
    """
    Create a new file with specified content in the output directory. Use this for creating new code files, documentation, or any text files. Files are automatically organized in timestamped session directories.

    Args:
        file_path: Name/path of the file to create (will be placed in output directory)
        content: Complete content to write to the file

    Returns:
        A JSON string with the result of the file operation.
    """
    try:
        safe_path = _get_safe_path(file_path)

        # Check if file exists before writing
        file_exists = safe_path.exists()
        before_content = ""

        if file_exists:
            # Read existing content for diff
            try:
                with open(safe_path, 'r', encoding='utf-8') as f:
                    before_content = f.read()
            except Exception:
                before_content = ""

        # Create parent directories if they don't exist
        safe_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the new content
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Verify the file was written correctly
        try:
            with open(safe_path, 'r', encoding='utf-8') as f:
                actual_content = f.read()
        except Exception:
            actual_content = ""

        if file_exists:
            # Generate diff for existing file replacement
            diff_info = _generate_diff(before_content, actual_content, file_path)
            event_type = "edited_file_full"
            success_message = f"Successfully replaced content in {file_path}"
            if diff_info["total_changes"] > 0:
                success_message += f" (+{diff_info['added_lines']} -{diff_info['removed_lines']} lines)"
            else:
                success_message += " (no changes detected)"
            
            result_data = {
                "message": success_message,
                "file_path": file_path,
                "operation": event_type,
                "before_content": before_content,
                "after_content": actual_content,
                "diff": diff_info,
                "success": diff_info["total_changes"] > 0 or before_content != actual_content
            }
        else:
            # New file creation
            event_type = "created_file"
            success_message = f"Successfully created {file_path}"
            if len(actual_content.splitlines()) > 0:
                success_message += f" ({len(actual_content.splitlines())} lines)"
            
            result_data = {
                "message": success_message,
                "file_path": file_path,
                "operation": event_type,
                "content": actual_content,
                "success": len(actual_content) > 0
            }
        return json.dumps(result_data)

    except Exception as e:
        return json.dumps({"error": f"Error writing to file {file_path}: {str(e)}", "success": False})

@tool
def find_and_replace_in_file(file_path: str, find_text: str, replace_text: str, use_regex: bool = False) -> str:
    """
    Modify existing files by finding and replacing text. This is the PREFERRED method for editing existing files rather than rewriting them. Uses literal text matching by default (safe for code with special characters like parentheses). Set use_regex=True only when you need regex patterns. Use this to add comments, fix bugs, or make incremental changes.

    Args:
        file_path: Path to the file to modify
        find_text: Exact text to find (literal matching by default)
        replace_text: Text to replace with
        use_regex: Optional: set to True for regex pattern matching (default: False)

    Returns:
        A JSON string with the result of the file operation.
    """
    try:
        safe_path = _get_safe_path(file_path)

        # Read the original file content
        with open(safe_path, 'r', encoding='utf-8') as f:
            before_content = f.read()

        # Perform replacement
        if use_regex:
            # Use regex mode
            new_content = re.sub(find_text, replace_text, before_content)
            replacements = len(re.findall(find_text, before_content))
        else:
            # Use literal string replacement (default)
            new_content = before_content.replace(find_text, replace_text)
            replacements = before_content.count(find_text)

        # Write back to file
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # Verify the file was written correctly
        try:
            with open(safe_path, 'r', encoding='utf-8') as f:
                actual_content = f.read()
        except Exception:
            actual_content = new_content

        # Generate diff information
        diff_info = _generate_diff(before_content, actual_content, file_path)

        success_message = f"Successfully made {replacements} replacements in {file_path}"
        if diff_info["total_changes"] > 0:
            success_message += f" (+{diff_info['added_lines']} -{diff_info['removed_lines']} lines)"
        else:
            success_message += " (no changes detected)"
            
        result_data = {
            "message": success_message,
            "file_path": file_path,
            "operation": "edited_file_diff",
            "before_content": before_content,
            "after_content": actual_content,
            "diff": diff_info,
            "success": diff_info["total_changes"] > 0
        }
        return json.dumps(result_data)

    except Exception as e:
        return json.dumps({"error": f"Error in find and replace for {file_path}: {str(e)}", "success": False})

@tool
def list_directory(directory_path: str = ".") -> str:
    """
    Explore directory contents to understand project structure. Lists all files and subdirectories with size information. Essential for understanding what files exist before reading or modifying them.
    
    Args:
        directory_path: Path to directory to list (defaults to output directory)
        
    Returns:
        Directory listing
    """
    try:
        safe_path = _get_safe_path(directory_path)
        
        if not safe_path.exists() or not safe_path.is_dir():
            return f"Directory {directory_path} does not exist or is not a directory."
        
        items = []
        for item in sorted(os.listdir(safe_path)):
            item_path = os.path.join(safe_path, item)
            if os.path.isdir(item_path):
                items.append(f"📁 {item}/")
            else:
                size = os.path.getsize(item_path)
                items.append(f"📄 {item} ({size} bytes)")
        
        return f"Contents of {directory_path}:\n" + "\n".join(items) if items else f"Directory {directory_path} is empty"
    except Exception as e:
        return f"Error listing directory {directory_path}: {str(e)}"

@tool
def execute_bash_command(command: str, working_directory: str = ".") -> str:
    """
    Execute system commands for testing, building, or running code. Use this to run Python scripts, install packages, run tests, compile code, or perform any command-line operations. Includes timeout protection.
    
    Args:
        command: The bash command to execute
        working_directory: Directory to run the command in (defaults to output directory)
        
    Returns:
        Command output and status
    """
    try:
        # Ensure the working directory is sandboxed
        safe_working_dir = _get_safe_path(working_directory)
        
        if not safe_working_dir.is_dir():
            return f"Error: Working directory '{working_directory}' is not a valid directory."
            
        result = subprocess.run(
            command,
            shell=True,
            cwd=safe_working_dir,
            capture_output=True,
            text=True,
            timeout=180
        )
        
        output = f"Command: {command}\n"
        output += f"Exit Code: {result.returncode}\n"
        output += f"Working Directory: {working_directory}\n\n"
        
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
            
        return output
    except subprocess.TimeoutExpired:
        return f"Command timed out: {command}"
    except Exception as e:
        return f"Error executing command '{command}': {str(e)}"

# --- Agent State ---
class MultiAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_expert: str
    debug_info: List[Dict[str, Any]]
    tool_failures: Dict[str, int]  # Track tool failure counts to prevent infinite loops
    tool_call_count: int  # Track total tool calls
    tool_call_history: List[Dict[str, Any]]  # Track tool call history for deduplication
    recent_files: List[str]  # Track recently created/modified files
    file_operation_events: List[Dict[str, Any]]  # Track file operation events for frontend display
    terminal_events: List[Dict[str, Any]]  # Track terminal events for frontend display

# --- Expert Agents ---

@functools.lru_cache(maxsize=5)
def create_llm_client(model_name: str):
    """Create a configured LLM client based on the provider specified in .env file."""
    # Read model from environment variable
    
    http_client = httpx.Client(
        verify=False,
        timeout=30.0,
        headers={
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Multi-Agent System"
        }
    )
    
    # Force all models to use OpenRouter
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=SecretStr(key) if (key := os.getenv("OPENROUTER_API_KEY")) else None,
        model=model_name,
        http_client=http_client,
        timeout=30.0,
    )

def coordinator_node(state: MultiAgentState):
    """
    Routes user queries to the appropriate expert based on intelligent content analysis.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Extract the user's query
    if isinstance(last_message, HumanMessage):
        user_query = last_message.content
    else:
        user_query = str(last_message.content)
    
    logger.info(f"🎯 Coordinator analyzing query: '{user_query[:100]}...'")
    
    # Create routing prompt
    routing_prompt = f"""You are an expert Coordinator AI. Your task is to analyze a user's request and route it to the most qualified specialized agent.

Available experts:
- **CodeGenerator**: Best for creating, writing, implementing, and generating code solutions
- **CodeReviewer**: Best for reviewing, analyzing, checking, and validating existing code
- **Planner**: Best for analyzing complex tasks, creating execution plans, gathering information, and breaking down multi-step projects

Based on the user's request, you must respond with ONLY the name of the most appropriate expert.
Your response must be either: CodeGenerator, CodeReviewer, or Planner

Examples:
- "Write a Python function" → CodeGenerator
- "Create a web scraper" → CodeGenerator
- "Review this code" → CodeReviewer
- "Check for bugs in my function" → CodeReviewer
- "Analyze the code quality" → CodeReviewer
- "Create a plan for this project" → Planner
- "Analyze the current system and suggest improvements" → Planner
- "Break down this complex task into steps" → Planner
- "What files are in this directory and what do they do?" → Planner"""
    
    # Create messages for routing
    routing_messages = [
        {"role": "system", "content": routing_prompt},
        {"role": "user", "content": f"Route this request: {user_query}"}
    ]
    
    try:
        model_name = os.getenv("LLM_MODEL", "openai/gpt-4o")
        llm = create_llm_client(model_name)
    
        # Output complete prompt
        logger.info("🔍 COORDINATOR PROMPT:")
        for i, msg in enumerate(routing_messages):
            logger.info(f"  Message {i+1} ({msg['role']}): {msg['content']}")
        logger.info("-------------------------------- END OF COORDINATOR PROMPT --------------------------------")
        
        response = llm.invoke(routing_messages)
        expert_choice = str(response.content).strip() if response.content else "CodeGenerator"
        
        logger.info(f"🎯 Coordinator routing to: {expert_choice}")
        
        # Validate expert choice
        valid_experts = ["CodeGenerator", "CodeReviewer", "Planner"]
        if expert_choice not in valid_experts:
            logger.warning(f"⚠️ Invalid expert choice '{expert_choice}', defaulting to CodeGenerator")
            expert_choice = "CodeGenerator"
            
        # Add the full prompt to the debug info for transparency
        debug_info = {
            "step": "routing",
            "expert": expert_choice,
            "reasoning": f"Routed '{user_query[:50]}...' to {expert_choice}",
            "timestamp": datetime.now().isoformat(),
            "prompt": routing_messages,
        }
        
        # Update state by returning only the changed fields
        return {
            "current_expert": expert_choice,
            "debug_info": [debug_info]
        }
        
    except Exception as e:
        logger.error(f"❌ Error in coordinator routing: {str(e)}")
        # Fallback to CodeGenerator and return only changed fields
        debug_info = {
            "step": "routing_error",
            "expert": "CodeGenerator",
            "reasoning": f"Error occurred, defaulting to CodeGenerator: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "prompt": routing_messages if 'routing_messages' in locals() else [{"role": "system", "content": "Error before prompt creation"}],
        }
        return {
            "current_expert": "CodeGenerator",
            "debug_info": [debug_info]
        }
        
def code_generator_node(state: MultiAgentState):
    """Code Generator specializes in generating code solutions and implementations."""
    logger.info("⚡ Code Generator starting task processing")
    
    system_prompt = """You are a Code Generator AI assistant. You specialize in:
    - Writing and generating code files
    - Implementing features based on specifications  
    - Creating complete solutions from requirements
    - Modifying and improving existing code

    IMPORTANT PRINCIPLES:
    - **CRITICAL: When you need to make multiple changes to a file (e.g., adding comments to multiple test cases), perform all edits in a single turn by calling the `find_and_replace_in_file` tool multiple times for each change. Do not make just one change and wait for the result. Complete all required edits at once.**
    - Prefer modifying existing files over rewriting them completely
    - The conversation history contains file contents from previous operations
    - Test your code after creating or modifying it
    - Be thorough and complete your tasks properly
    
    You can use tools as many times as needed to complete the task properly. Focus on delivering high-quality, working solutions."""
    
    model_name = os.getenv("LLM_MODEL", "openai/gpt-4o")
    model = create_llm_client(model_name)
    tools = [write_file, find_and_replace_in_file, read_file, list_directory, execute_bash_command]
    model_with_tools = model.bind_tools(tools)
    
    try:
        is_anthropic = "anthropic" in model_name.lower() or "claude" in model_name.lower()
        
        # The message list is now much simpler
        messages_for_expert = [SystemMessage(content=system_prompt)] + state["messages"]
        
        # Output complete prompt
        logger.info("🔍 CODE GENERATOR PROMPT:")
        for i, msg in enumerate(messages_for_expert):
            if hasattr(msg, 'content'):
                content = str(msg.content)
                logger.info(f"  Message {i+1} ({type(msg).__name__}): {content[:500]}{'...' if len(content) > 500 else ''}")
        logger.info("-------------------------------- END OF CODE GENERATOR PROMPT --------------------------------")

        # Ensure Anthropic compatibility (no empty assistant content)
        safe_messages = _ensure_nonempty_assistant(messages_for_expert) if is_anthropic else messages_for_expert
        response = model_with_tools.invoke(safe_messages)
        
        response_content = str(response.content)
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "node": "code_generator",
            "has_tool_calls": isinstance(response, AIMessage) and bool(response.tool_calls),
            "response_preview": response_content[:100] + "..." if len(response_content) > 100 else response_content,
            "response_full": response_content,
            "prompt": [msg.dict() for msg in messages_for_expert]
        }
        
        return {
            "messages": [response],
            "debug_info": [debug_info]
        }
        
    except Exception as e:
        error_msg = AIMessage(content=f"Code Generator encountered an error: {str(e)}")
        return {
            "messages": [error_msg],
            "debug_info": [{"error": str(e), "node": "code_generator"}]
        }

def code_reviewer_node(state: MultiAgentState):
    """Code reviewer that handles code review and quality assurance."""
    
    # Check if there are recent files to provide context
    recent_files_info = ""
    if "recent_files" in state and state["recent_files"]:
        recent_files_info = f"\n\nCONTEXT: Recently created/modified files in this session: {', '.join(state['recent_files'])}"
    
    system_prompt = f"""You are a Code Reviewer AI assistant. You specialize in:
    - Code review and quality assurance
    - Security checks and best practices
    - Bug detection and performance analysis
    - Code formatting and standards validation
    - Improving code quality and maintainability
    
    IMPORTANT PRINCIPLES:
    - **CRITICAL: When you need to make multiple changes to a file (e.g., adding comments to multiple test cases), perform all edits in a single turn by calling the `find_and_replace_in_file` tool multiple times for each change. Do not make just one change and wait for the result. Complete all required edits at once.**
    - Be proactive in finding and analyzing code
    - The conversation history contains file contents from previous operations
    - Test code after making changes to ensure it still works
    - Provide comprehensive analysis with actionable recommendations
    - Focus on delivering thorough code review and improvements
    
    You can use tools as many times as needed to provide thorough code review and improvements.{recent_files_info}"""
    
    model_name = os.getenv("LLM_MODEL", "openai/gpt-4o")
    model = create_llm_client(model_name)
    tools = [read_file, list_directory, find_and_replace_in_file, execute_bash_command]
    model_with_tools = model.bind_tools(tools)
    
    try:
        is_anthropic = "anthropic" in model_name.lower() or "claude" in model_name.lower()

        # The message list is now much simpler
        messages_for_expert = [SystemMessage(content=system_prompt)] + state["messages"]
        
        # Output complete prompt
        logger.info("🔍 CODE REVIEWER PROMPT:")
        for i, msg in enumerate(messages_for_expert):
            if hasattr(msg, 'content'):
                content = str(msg.content)
                logger.info(f"  Message {i+1} ({type(msg).__name__}): {content[:500]}{'...' if len(content) > 500 else ''}")
        logger.info("-------------------------------- END OF CODE REVIEWER PROMPT --------------------------------")
        
        # Ensure Anthropic compatibility (no empty assistant content)
        safe_messages = _ensure_nonempty_assistant(messages_for_expert) if is_anthropic else messages_for_expert
        response = model_with_tools.invoke(safe_messages)
        
        response_content = str(response.content)
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "node": "code_reviewer",
            "has_tool_calls": isinstance(response, AIMessage) and bool(response.tool_calls),
            "response_preview": response_content[:100] + "..." if len(response_content) > 100 else response_content,
            "response_full": response_content,
            "prompt": [msg.dict() for msg in messages_for_expert]
        }
        
        return {
            "messages": [response],
            "debug_info": [debug_info]
        }
        
    except Exception as e:
        error_msg = AIMessage(content=f"Code Reviewer encountered an error: {str(e)}")
        return {
            "messages": [error_msg],
            "debug_info": [{"error": str(e), "node": "code_reviewer"}]
        }

def planner_node(state: MultiAgentState):
    """Planner node that analyzes tasks and creates detailed execution plans."""
    logger.info("📋 PLANNER starting task analysis")

    # Import PLANNER tools and functions
    try:
        from planner_node import (
            read_file as planner_read_file,
            list_directory as planner_list_directory,
            execute_safe_bash,
            get_planner_system_prompt
        )
    except ImportError:
        error_msg = AIMessage(content="PLANNER node is not available. Please ensure planner_node.py is in the same directory.")
        return {
            "messages": [error_msg],
            "debug_info": [{"error": "Import error", "node": "planner"}]
        }

    # Get system prompt (default to comprehensive planning)
    system_prompt = get_planner_system_prompt("comprehensive")

    model_name = os.getenv("LLM_MODEL", "openai/gpt-4o")
    model = create_llm_client(model_name)
    tools = [planner_read_file, planner_list_directory, execute_safe_bash]
    model_with_tools = model.bind_tools(tools)

    try:
        is_anthropic = "anthropic" in model_name.lower() or "claude" in model_name.lower()

        # Prepare messages for planner
        messages_for_planner = [SystemMessage(content=system_prompt)] + state["messages"]

        # Output complete prompt
        logger.info("🔍 PLANNER PROMPT:")
        for i, msg in enumerate(messages_for_planner):
            if hasattr(msg, 'content'):
                content = str(msg.content)
                logger.info(f"  Message {i+1} ({type(msg).__name__}): {content[:500]}{'...' if len(content) > 500 else ''}")
        logger.info("-------------------------------- END OF PLANNER PROMPT --------------------------------")

        # Ensure Anthropic compatibility (no empty assistant content)
        safe_messages = _ensure_nonempty_assistant(messages_for_planner) if is_anthropic else messages_for_planner
        response = model_with_tools.invoke(safe_messages)

        response_content = str(response.content)
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "node": "planner",
            "has_tool_calls": isinstance(response, AIMessage) and bool(response.tool_calls),
            "response_preview": response_content[:100] + "..." if len(response_content) > 100 else response_content,
            "response_full": response_content,
            "prompt": [msg.dict() for msg in messages_for_planner]
        }

        return {
            "messages": [response],
            "debug_info": [debug_info]
        }

    except Exception as e:
        error_msg = AIMessage(content=f"PLANNER encountered an error: {str(e)}")
        return {
            "messages": [error_msg],
            "debug_info": [{"error": str(e), "node": "planner"}]
        }

def tool_executor_node(state: MultiAgentState):
    """Executes tool calls and returns results."""
    if not state["messages"]:
        return state
    
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) or not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return state

    logger.info(f"🔧 Tool executor processing {len(last_message.tool_calls)} tool calls")

    # Initialize state fields if they don't exist
    state.setdefault("tool_call_count", 0)
    state.setdefault("tool_call_history", [])
    state.setdefault("tool_failures", {})
    
    # These will hold events generated ONLY during this execution run
    new_file_operation_events = []
    new_terminal_events = []

    # Check total tool call limit
    MAX_TOTAL_TOOL_CALLS = 15  # Prevent infinite loops
    if state["tool_call_count"] >= MAX_TOTAL_TOOL_CALLS:
        logger.warning(f"⚠️ Reached maximum tool calls limit ({MAX_TOTAL_TOOL_CALLS})")
        return {
            "messages": [AIMessage(content=f"I've reached the maximum number of tool calls ({MAX_TOTAL_TOOL_CALLS}) for this session. Please start a new conversation if you need more operations.")]
        }

    # Process all tool calls and collect results
    tool_results = []
    all_tool_call_details = []  # For comprehensive logging
    
    for i, tool_call in enumerate(last_message.tool_calls):
        tool_name = tool_call.get('name', 'unknown')
        tool_args = tool_call.get('args', {})
        tool_id = tool_call.get('id', f'tool_{i}')
        
        # Log detailed tool call information
        logger.info(f"🔧 Tool Call {i+1}/{len(last_message.tool_calls)}:")
        logger.info(f"  Tool: {tool_name}")
        logger.info(f"  ID: {tool_id}")
        logger.info(f"  Arguments: {json.dumps(tool_args, indent=2)}")
        
        all_tool_call_details.append({
            "tool_name": tool_name,
            "tool_id": tool_id,
            "tool_args": tool_args,
            "call_index": i + 1,
            "total_calls": len(last_message.tool_calls)
        })

        # Create tool call signature for deduplication
        tool_signature = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
        
        # Check failure count for this specific tool+args combination
        failure_key = tool_signature
        failure_count = state["tool_failures"].get(failure_key, 0)
        
        if failure_count >= 3:
            logger.warning(f"⚠️ Skipping failed tool: {tool_name} (failed {failure_count} times)")
            result_content = f"Tool {tool_name} has failed too many times with these arguments and has been disabled."
        else:
            # Execute the tool
            try:
                # Get the actual tool function
                available_tools = {
                    "write_file": write_file,
                    "read_file": read_file,
                    "find_and_replace_in_file": find_and_replace_in_file,
                    "list_directory": list_directory,
                    "execute_bash_command": execute_bash_command
                }

                # Add PLANNER tools if available
                try:
                    from planner_node import (
                        read_file as planner_read_file,
                        list_directory as planner_list_directory,
                        execute_safe_bash
                    )
                    available_tools.update({
                        "execute_safe_bash": execute_safe_bash
                    })
                    # Note: PLANNER uses same names for read_file and list_directory
                    # but with different implementations, so we keep the original ones
                except ImportError:
                    logger.warning("PLANNER tools not available for tool execution")
                
                if tool_name in available_tools:
                    # No longer need to pre-read files here, the tool handles it
                    tool_function = available_tools[tool_name]
                    result_content = tool_function.invoke(tool_args)
                    logger.info(f"✅ Tool {tool_name} executed successfully")
                    
                    # Try to parse the result as JSON for file/terminal operations
                    try:
                        result_data = json.loads(result_content)
                        is_structured_result = isinstance(result_data, dict) and "success" in result_data
                    except (json.JSONDecodeError, TypeError):
                        is_structured_result = False

                    if is_structured_result:
                        # This is a structured result from a file or terminal tool
                        # Add tool_call_id for frontend tracking
                        result_data["tool_call_id"] = tool_id
                        
                        if result_data.get("operation"): # File operation
                             new_file_operation_events.append({ "type": "file_operation", **result_data })
                        elif result_data.get("command"): # Terminal operation
                            new_terminal_events.append({ "type": "terminal", **result_data })
                        
                        # The message for the LLM should be the summary message
                        result_content_for_llm = result_data.get("message", "Operation successful.")
                    else:
                        # This is a simple string result from other tools (e.g., list_directory)
                        result_content_for_llm = result_content

                else:
                    result_content_for_llm = f"Unknown tool: {tool_name}"
                    logger.error(f"❌ Unknown tool: {tool_name}")
                    
            except Exception as e:
                logger.error(f"❌ Tool {tool_name} failed with error: {str(e)}")
                result_content_for_llm = f"Tool {tool_name} failed: {str(e)}"
                
                # Increment failure count
                state["tool_failures"][failure_key] = failure_count + 1

        # Create tool result message
        tool_message = ToolMessage(
            content=result_content_for_llm,
            tool_call_id=tool_id
        )
        tool_results.append(tool_message)
        
        # Track this tool call
        state["tool_call_history"].append({
            "signature": tool_signature,
            "tool_name": tool_name,
            "timestamp": datetime.now().isoformat(),
            "success": "failed" not in result_content_for_llm.lower()
        })
        
        # Increment total tool call count
        state["tool_call_count"] += 1

    # Log summary of all tool calls processed
    logger.info(f"🔧 Completed processing {len(last_message.tool_calls)} tool calls:")
    for detail in all_tool_call_details:
        logger.info(f"  {detail['call_index']}/{detail['total_calls']}: {detail['tool_name']} -> {'✅' if any('failed' not in msg.content.lower() for msg in tool_results if hasattr(msg, 'tool_call_id') and msg.tool_call_id == detail['tool_id']) else '❌'}")

    return {
        "messages": tool_results,
        "tool_call_count": state["tool_call_count"],
        "tool_call_history": state["tool_call_history"],
        "tool_failures": state["tool_failures"],
        "recent_files": state.get("recent_files", []),
        "file_operation_events": new_file_operation_events,
        "terminal_events": new_terminal_events,
    }

# --- Graph Routing Logic ---

def route_to_expert(state: MultiAgentState) -> str:
    """Routes to the appropriate expert based on coordinator decision."""
    expert = state.get("current_expert", "CodeGenerator")
    expert_map = {
        "CodeGenerator": "code_generator",
        "CodeReviewer": "code_reviewer",
        "Planner": "planner"
    }
    return expert_map.get(expert, "code_generator")

def should_continue(state: MultiAgentState) -> Literal["execute_tools", "__end__"]:
    """Determines if tools need to be executed."""
    if not state["messages"]:
        return "__end__"
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "execute_tools"
    else:
        return "__end__"

# --- Build the Graph ---

def create_multi_agent_graph():
    """Creates and returns the multi-agent workflow graph."""
    workflow = StateGraph(MultiAgentState)

    # Add nodes
    workflow.add_node("coordinator", coordinator_node)
    workflow.add_node("code_generator", code_generator_node)
    workflow.add_node("code_reviewer", code_reviewer_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("tool_executor", tool_executor_node)

    # Set entry point
    workflow.set_entry_point("coordinator")

    # Route from coordinator to appropriate expert
    workflow.add_conditional_edges(
        "coordinator",
        route_to_expert,
        {
            "code_generator": "code_generator",
            "code_reviewer": "code_reviewer",
            "planner": "planner"
        }
    )

    # Each expert can either call tools or end
    for expert in ["code_generator", "code_reviewer", "planner"]:
        workflow.add_conditional_edges(
            expert,
            should_continue,
            {"execute_tools": "tool_executor", "__end__": END}
        )

    # After executing tools, route back to the correct expert
    workflow.add_conditional_edges(
        "tool_executor",
        route_to_expert,
        {
            "code_generator": "code_generator",
            "code_reviewer": "code_reviewer",
            "planner": "planner"
        }
    )

    return workflow.compile()

# --- API Interface ---

def run_multi_agent_query_stream(messages: List[Dict[str, Any]]):
    """
    Streams messages from the multi-agent system in real-time.
    This is the single entry point for running queries.
    """
    query_text = messages[-1].get('content', '')[:100] if messages else "Unknown query"
    logger.info(f"🚀 Starting multi-agent query stream processing: '{query_text}...'")
    
    # Convert dicts from session history into LangChain message objects
    langchain_messages = []
    for msg in messages:
        role = msg.get("type", "")
        content = msg.get("content", "")
        
        if role == "human":
            langchain_messages.append(HumanMessage(content=content))
        elif role == "ai":
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                langchain_messages.append(AIMessage(content=content, tool_calls=tool_calls))
            else:
                langchain_messages.append(AIMessage(content=content))
        elif role == "tool":
            tool_call_id = msg.get("tool_call_id")
            if tool_call_id:
                langchain_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
    
    state: MultiAgentState = {
        "messages": langchain_messages,
        "current_expert": "",
        "debug_info": [],
        "tool_failures": {},
        "tool_call_count": 0,
        "tool_call_history": [],
        "recent_files": [],
        "file_operation_events": [],
        "terminal_events": []
    }
    
    # helper for unique ids
    def _new_id() -> str:
        return f"msg-{uuid.uuid4().hex}"

    message_counter = 0
    
    # Step 1: Coordinator routing
    logger.info("🎯 Step 1: Coordinator routing")
    coordinator_result = coordinator_node(state)
    
    if "current_expert" in coordinator_result:
        expert_used = coordinator_result["current_expert"]
        state["current_expert"] = expert_used
        
        # Extract coordinator prompt for frontend display
        coordinator_prompt = None
        if "debug_info" in coordinator_result:
            state["debug_info"].extend(coordinator_result["debug_info"])
            # Get the prompt from coordinator's debug_info
            if coordinator_result["debug_info"] and "prompt" in coordinator_result["debug_info"][0]:
                coordinator_prompt = coordinator_result["debug_info"][0]["prompt"]
        
        expert_icon = EXPERT_DEFINITIONS.get(expert_used, {}).get("icon", "🤖")
        
        message_counter += 1
        yield {
            "type": "message",
            "message": {
                "id": _new_id(),
                "type": "routing",
                "content": f"🎯 Routing to {expert_used}",
                "expert": "Coordinator",
                "expert_icon": "🎯",
                "timestamp": datetime.now().isoformat(),
                "prompt": coordinator_prompt
            }
        }
    else:
        expert_used = "CodeGenerator"
        expert_icon = EXPERT_DEFINITIONS.get(expert_used, {}).get("icon", "🤖")
    
    # Step 2: Execute expert node
    logger.info(f"⚡ Step 2: Executing {expert_used}")
    
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        logger.info(f"🔄 Iteration {iteration}")
        
        # Execute the appropriate expert
        if expert_used == "CodeGenerator":
            expert_result = code_generator_node(state)
        elif expert_used == "CodeReviewer":
            expert_result = code_reviewer_node(state)
        else:  # Planner
            expert_result = planner_node(state)
        
        # Update state with expert result
        if "messages" in expert_result:
            state["messages"] = state["messages"] + expert_result["messages"]
            
            # Extract prompt snapshot for this LLM call (for frontend display)
            prompt_snapshot = None
            if "debug_info" in expert_result and expert_result["debug_info"]:
                prompt_snapshot = expert_result["debug_info"][0].get("prompt")

            # Check the last message for tool calls or text response
            last_msg = expert_result["messages"][-1]
            if isinstance(last_msg, AIMessage):
                # If AI wants to call tools
                if last_msg.tool_calls:
                    # Execute tools first
                    logger.info("🔧 Executing tools")
                    tool_result = tool_executor_node(state)

                    # Update state with tool results
                    if "messages" in tool_result:
                        state["messages"] = state["messages"] + tool_result["messages"]

                        # Create combined tool call events for each tool
                        for i, tool_call in enumerate(last_msg.tool_calls):
                            tool_name = tool_call["name"]
                            tool_args = tool_call["args"]
                            tool_id = tool_call["id"]

                            # Find the corresponding tool result
                            tool_result_content = ""
                            for tool_msg in tool_result["messages"]:
                                if isinstance(tool_msg, ToolMessage) and tool_msg.tool_call_id == tool_id:
                                    tool_result_content = tool_msg.content
                                    break

                            # Determine if this is a file operation or terminal tool
                            if tool_name in ["write_file", "find_and_replace_in_file"]:
                                # Find the corresponding file event from the new events
                                file_event = None
                                file_events_list = cast(List[Dict[str, Any]], tool_result.get("file_operation_events", []))
                                for ev in file_events_list:
                                    if ev.get("tool_call_id") == tool_id:
                                        file_event = ev
                                        break

                                if file_event:
                                    message_counter += 1
                                    # Create enhanced file operation event with prompt and args
                                    enhanced_event = dict(file_event)
                                    enhanced_event["prompt"] = prompt_snapshot
                                    enhanced_event["tool_args"] = tool_args
                                    enhanced_event["timestamp"] = datetime.now().isoformat()
                                    yield enhanced_event

                            elif tool_name in ["execute_bash_command", "execute_safe_bash"]:
                                # Find the corresponding terminal event from the new events
                                terminal_event = None
                                terminal_events_list = cast(List[Dict[str, Any]], tool_result.get("terminal_events", []))
                                for ev in terminal_events_list:
                                    if ev.get("tool_call_id") == tool_id:
                                        terminal_event = ev
                                        break

                                if terminal_event:
                                    message_counter += 1
                                    # Create enhanced terminal event with prompt and args
                                    enhanced_event = dict(terminal_event)
                                    enhanced_event["prompt"] = prompt_snapshot
                                    enhanced_event["tool_args"] = tool_args
                                    enhanced_event["timestamp"] = datetime.now().isoformat()
                                    yield enhanced_event

                            else:
                                # For other tools, create a generic tool call event
                                message_counter += 1
                                yield {
                                    "type": "tool_call",
                                    "tool_name": tool_name,
                                    "command": f"{tool_name}({', '.join(f'{k}={v}' for k, v in tool_args.items())})",
                                    "result": tool_result_content,
                                    "success": "error" not in str(tool_result_content).lower(),
                                    "timestamp": datetime.now().isoformat(),
                                    "prompt": prompt_snapshot,
                                    "tool_args": tool_args
                                }
                    
                    # Update other state fields safely
                    for key in ["tool_failures", "tool_call_count", "tool_call_history", "recent_files"]:
                        if key in tool_result:
                            state[key] = tool_result[key]
                    
                    # Manually update the state's event history with the new events
                    if "file_operation_events" in tool_result:
                        events_to_add = cast(List[Dict[str, Any]], tool_result["file_operation_events"])
                        state.get("file_operation_events", []).extend(events_to_add)
                    if "terminal_events" in tool_result:
                        events_to_add = cast(List[Dict[str, Any]], tool_result["terminal_events"])
                        state.get("terminal_events", []).extend(events_to_add)
                    
                    # Continue to next iteration for AI to process tool results
                    continue
                
                # If AI has text response (no tool calls), we're done
                elif str(last_msg.content).strip():
                    message_counter += 1
                    yield {
                        "type": "message",
                        "message": {
                            "id": _new_id(),
                            "type": "agent",
                            "content": str(last_msg.content).strip(),
                            "expert": expert_used,
                            "expert_icon": expert_icon,
                            "timestamp": datetime.now().isoformat(),
                            "prompt": prompt_snapshot
                        }
                    }
                    break  # Task complete
        
        # If no messages or no tool calls, we're done
        break
    
    # Send completion event
    logger.info(f"✅ Multi-agent query stream completed successfully, expert used: {expert_used}")
    yield {
        "type": "complete",
        "expert_used": expert_used,
        "timestamp": datetime.now().isoformat()
    }

# --- Command Line Interface ---

if __name__ == "__main__":
    print("🚀 Multi-Agent Expert System CLI Test")
    print("=" * 60)
    
    # Suppress SSL warnings
    import warnings
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    
    # Test query
    query = "Write a binary search algorithm in Python and save it to a file named 'binary_search.py'."
    
    print(f"\n🔍 Query: {query}")
    print("-" * 40)
        
    query_messages = [{"type": "human", "content": query}]
    
    # The function returns a generator; we must iterate through its events.
    error = None

    for event in run_multi_agent_query_stream(query_messages):
        if event.get("type") == "complete":
            print(f"✅ Task completed by {event.get('expert_used', 'Unknown')}")
        elif event.get("type") == "error":
            error = event.get("error")

    if error:
        print(f"❌ Error: {error}")
    else:
        print("🤖 Task completed successfully!")
        
        print("=" * 60) 

    # Check if file was created
    output_file = os.path.join(OUTPUT_DIR, "binary_search.py")
    if os.path.exists(output_file):
        print(f"✅ Verification: File '{output_file}' was created.")
        with open(output_file, 'r') as f:
            print("--- File Content ---")
            print(f.read(200) + "...")
            print("--------------------")
    else:
        print(f"❌ Verification: File '{output_file}' was NOT created.") 

# NEW: helper to ensure Anthropic compatibility --------------------------------

def _ensure_nonempty_assistant(msgs: list[BaseMessage]) -> list[BaseMessage]:
    """Return a copy of msgs where any assistant/AIMessage with empty content
    is given a single placeholder character. This is only used when sending
    to Anthropic models; it does **NOT** modify the objects held in session,
    so frontend still receives the original content (possibly empty).
    """
    fixed: list[BaseMessage] = []
    for m in msgs:
        if isinstance(m, AIMessage) and not str(m.content).strip():
            fixed.append(AIMessage(content=".", tool_calls=getattr(m, "tool_calls", None), id=getattr(m, "id", None)))
        else:
            fixed.append(m)
    return fixed

# ------------------------------------------------------------------------------ 