"""
PLANNER Node Implementation for Multi-Agent System

This module implements a specialized PLANNER node that can:
1. Read files using read_file tool
2. List directories using list_directory tool  
3. Execute safe bash commands (whitelist controlled)
4. Generate comprehensive plans for complex tasks
5. Break down tasks into manageable subtasks
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
import operator
import os
import subprocess
import logging
import json
import re
from pathlib import Path
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

# Configure logging
logger = logging.getLogger(__name__)

# --- PLANNER Node Configuration ---
PLANNER_DEFINITION = {
    "name": "Planner",
    "description": "Analyzes complex tasks and creates detailed execution plans with file system awareness",
    "icon": "📋",
    "tools": ["read_file", "list_directory", "execute_safe_bash"]
}

# Whitelist of safe bash commands for PLANNER
SAFE_BASH_COMMANDS = {
    # File and directory operations (read-only)
    "ls", "ll", "dir", "find", "locate", "which", "whereis",
    "cat", "head", "tail", "less", "more", "file", "stat",
    "pwd", "whoami", "id", "groups", "env", "printenv",
    
    # System information (read-only)
    "ps", "top", "htop", "free", "df", "du", "lscpu", "lsblk",
    "uname", "hostname", "uptime", "date", "cal", "history",
    
    # Network information (read-only)
    "ping", "nslookup", "dig", "host", "netstat", "ss", "lsof",
    
    # Text processing (read-only)
    "grep", "egrep", "fgrep", "awk", "sed", "sort", "uniq", 
    "wc", "cut", "tr", "tee", "diff", "cmp", "comm",
    
    # Archive operations (read-only)
    "tar", "zip", "unzip", "gzip", "gunzip", "zcat",
    
    # Development tools (read-only)
    "git", "python", "python3", "node", "npm", "pip", "pip3",
    "java", "javac", "gcc", "g++", "make", "cmake",
    
    # Package managers (info only)
    "apt", "yum", "dnf", "brew", "conda", "docker"
}

# Dangerous command patterns to block
DANGEROUS_PATTERNS = [
    r'\brm\b', r'\bmv\b', r'\bcp\b', r'\bdd\b', r'\bchmod\b', r'\bchown\b',
    r'\bsu\b', r'\bsudo\b', r'\bkill\b', r'\bkillall\b', r'\bpkill\b',
    r'\breboot\b', r'\bshutdown\b', r'\bhalt\b', r'\binit\b',
    r'\bmount\b', r'\bumount\b', r'\bfdisk\b', r'\bparted\b',
    r'\b>\b', r'\b>>\b', r'\b<\b', r'\b\|\b', r'\b&\b', r'\b;\b',
    r'\bexec\b', r'\beval\b', r'\bsource\b', r'\b\.\b'
]

# --- Sandboxing Helper (reused from main system) ---
def _get_safe_path(file_path: str, base_dir: Optional[Path] = None) -> Path:
    """
    Resolves a user-provided path against the secure base directory
    and ensures it does not escape the sandbox.
    """
    if base_dir is None:
        base_dir = Path.cwd()
    
    # Normalize and resolve the path
    safe_path = (base_dir / file_path).resolve()
    
    # Check if the resolved path is within the secure base directory
    if not str(safe_path).startswith(str(base_dir.resolve())):
        raise ValueError(f"Path traversal attempt detected. Access to '{file_path}' is denied.")
    
    return safe_path

# --- PLANNER Tools ---

@tool
def read_file(file_path: str) -> str:
    """
    Read and analyze the contents of any file for planning purposes.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        String containing the file contents
    """
    try:
        safe_path = _get_safe_path(file_path)
        if not safe_path.exists():
            return f"File not found: {file_path}"
        
        if not safe_path.is_file():
            return f"Path is not a file: {file_path}"
            
        with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Limit content size for planning purposes
        if len(content) > 10000:
            content = content[:10000] + "\n... [Content truncated for planning analysis]"
            
        return f"File contents of {file_path}:\n\n{content}"
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"

@tool
def list_directory(directory_path: str = ".") -> str:
    """
    List directory contents for planning and analysis purposes.
    
    Args:
        directory_path: Path to directory to list (defaults to current directory)
        
    Returns:
        Directory listing with file information
    """
    try:
        safe_path = _get_safe_path(directory_path)
        
        if not safe_path.exists():
            return f"Directory not found: {directory_path}"
            
        if not safe_path.is_dir():
            return f"Path is not a directory: {directory_path}"
        
        items = []
        for item in sorted(safe_path.iterdir()):
            if item.is_dir():
                items.append(f"📁 {item.name}/")
            else:
                try:
                    size = item.stat().st_size
                    items.append(f"📄 {item.name} ({size} bytes)")
                except:
                    items.append(f"📄 {item.name} (size unknown)")
        
        return f"Contents of {directory_path}:\n" + "\n".join(items) if items else f"Directory {directory_path} is empty"
    except Exception as e:
        return f"Error listing directory {directory_path}: {str(e)}"

def _is_command_safe(command: str) -> tuple[bool, str]:
    """
    Check if a bash command is safe to execute based on whitelist and blacklist.
    
    Args:
        command: The bash command to check
        
    Returns:
        Tuple of (is_safe, reason)
    """
    command = command.strip()
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Command contains dangerous pattern: {pattern}"
    
    # Extract the main command (first word)
    main_command = command.split()[0] if command.split() else ""
    
    # Check if main command is in whitelist
    if main_command not in SAFE_BASH_COMMANDS:
        return False, f"Command '{main_command}' is not in the safe commands whitelist"
    
    # Additional checks for specific commands
    if main_command in ["git"] and any(dangerous in command.lower() for dangerous in ["push", "commit", "add", "rm", "reset"]):
        return False, "Git write operations are not allowed"
    
    if main_command in ["python", "python3", "node"] and "-c" in command:
        return False, "Code execution with -c flag is not allowed"
    
    if main_command in ["docker"] and any(dangerous in command.lower() for dangerous in ["run", "exec", "start", "stop", "rm"]):
        return False, "Docker container operations are not allowed"
    
    return True, "Command is safe"

@tool
def execute_safe_bash(command: str, working_directory: str = ".") -> str:
    """
    Execute safe bash commands for information gathering and analysis.
    Only whitelisted read-only commands are allowed.
    
    Args:
        command: The bash command to execute (must be in whitelist)
        working_directory: Directory to run the command in
        
    Returns:
        Command output and status
    """
    try:
        # Validate command safety
        is_safe, reason = _is_command_safe(command)
        if not is_safe:
            return f"Command rejected: {reason}\nCommand: {command}"
        
        # Ensure working directory is safe
        safe_working_dir = _get_safe_path(working_directory)
        
        if not safe_working_dir.is_dir():
            return f"Error: Working directory '{working_directory}' is not a valid directory."
        
        # Execute command with timeout
        result = subprocess.run(
            command,
            shell=True,
            cwd=safe_working_dir,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout for safety
        )
        
        output = f"Command: {command}\n"
        output += f"Exit Code: {result.returncode}\n"
        output += f"Working Directory: {working_directory}\n\n"
        
        if result.stdout:
            # Limit output size
            stdout = result.stdout
            if len(stdout) > 5000:
                stdout = stdout[:5000] + "\n... [Output truncated]"
            output += f"STDOUT:\n{stdout}\n"
            
        if result.stderr:
            stderr = result.stderr
            if len(stderr) > 2000:
                stderr = stderr[:2000] + "\n... [Error output truncated]"
            output += f"STDERR:\n{stderr}\n"
            
        return output
        
    except subprocess.TimeoutExpired:
        return f"Command timed out (30s limit): {command}"
    except Exception as e:
        return f"Error executing command '{command}': {str(e)}"

# --- PLANNER System Prompts ---

PLANNER_SYSTEM_PROMPTS = {
    "comprehensive": """You are a Comprehensive Planning AI assistant. You specialize in:

🎯 **Core Capabilities:**
- Analyzing complex, multi-step tasks and breaking them down into manageable components
- Creating detailed execution plans with clear dependencies and timelines
- Gathering information through file system exploration and safe command execution
- Identifying potential risks, bottlenecks, and alternative approaches
- Providing structured, actionable plans that others can follow

📋 **Planning Methodology:**
1. **Discovery Phase**: Use read_file, list_directory, and execute_safe_bash to understand the current state
2. **Analysis Phase**: Break down the main goal into logical sub-goals and identify dependencies
3. **Planning Phase**: Create a step-by-step execution plan with clear milestones
4. **Risk Assessment**: Identify potential issues and provide mitigation strategies
5. **Resource Planning**: Determine what tools, files, and information will be needed

🔧 **Available Tools:**
- `read_file`: Examine file contents for planning context
- `list_directory`: Explore directory structures and available resources
- `execute_safe_bash`: Run safe, read-only commands for system information

⚠️ **Important Guidelines:**
- Always start by exploring the current environment to understand context
- Create plans that are specific, measurable, and actionable
- Consider dependencies between tasks and plan accordingly
- Provide clear success criteria for each step
- Include fallback options when possible
- Focus on information gathering and planning - you don't execute the plan yourself

Your goal is to create comprehensive, well-structured plans that enable successful task completion.""",

    "technical": """You are a Technical Planning AI assistant specialized in software development and system administration tasks.

🔧 **Technical Focus Areas:**
- Software architecture and development planning
- System configuration and deployment strategies
- Code analysis and refactoring plans
- Testing and quality assurance strategies
- Performance optimization and monitoring plans
- Security assessment and improvement planning

📊 **Technical Planning Process:**
1. **Environment Assessment**: Analyze current codebase, infrastructure, and tools
2. **Requirements Analysis**: Understand technical requirements and constraints
3. **Architecture Planning**: Design technical solutions and system interactions
4. **Implementation Strategy**: Create detailed technical implementation steps
5. **Testing Strategy**: Plan comprehensive testing approaches
6. **Deployment Planning**: Design safe deployment and rollback procedures

🛠️ **Technical Tools Usage:**
- Use `read_file` to analyze code, configuration files, and documentation
- Use `list_directory` to understand project structure and organization
- Use `execute_safe_bash` to gather system information, check dependencies, and analyze environments

💡 **Technical Best Practices:**
- Follow industry standards and best practices
- Consider scalability, maintainability, and security in all plans
- Plan for monitoring, logging, and debugging capabilities
- Include code review and quality assurance steps
- Consider backward compatibility and migration strategies
- Plan for documentation and knowledge transfer

Create detailed technical plans that experienced developers and system administrators can follow.""",

    "research": """You are a Research Planning AI assistant focused on information gathering and analysis tasks.

🔍 **Research Specializations:**
- Information discovery and data collection strategies
- Analysis methodology and approach planning
- Research workflow optimization
- Data organization and documentation planning
- Comparative analysis and evaluation frameworks
- Knowledge synthesis and reporting strategies

📚 **Research Planning Framework:**
1. **Scope Definition**: Clearly define research objectives and boundaries
2. **Information Mapping**: Identify available data sources and information gaps
3. **Collection Strategy**: Plan systematic information gathering approaches
4. **Analysis Framework**: Design methods for processing and analyzing information
5. **Validation Process**: Plan verification and cross-referencing strategies
6. **Documentation Plan**: Structure for organizing and presenting findings

🔎 **Research Tools Application:**
- Use `read_file` to examine existing documents, data files, and research materials
- Use `list_directory` to discover available resources and organize information
- Use `execute_safe_bash` to gather system information and process data files

📋 **Research Methodology:**
- Start with broad exploration, then narrow focus based on findings
- Plan for systematic documentation of all discoveries
- Include multiple verification methods for important findings
- Design reproducible research processes
- Plan for regular progress reviews and strategy adjustments
- Consider multiple perspectives and potential biases

Your role is to create thorough research plans that ensure comprehensive information gathering and analysis.""",

    "project": """You are a Project Planning AI assistant specialized in project management and coordination.

📊 **Project Management Focus:**
- Project scope definition and requirement gathering
- Task breakdown and dependency mapping
- Resource allocation and timeline planning
- Risk assessment and mitigation strategies
- Communication and coordination planning
- Progress tracking and milestone definition

🎯 **Project Planning Methodology:**
1. **Project Discovery**: Understand project goals, constraints, and stakeholders
2. **Scope Planning**: Define deliverables, boundaries, and success criteria
3. **Work Breakdown**: Decompose project into manageable tasks and subtasks
4. **Dependency Analysis**: Identify task relationships and critical path
5. **Resource Planning**: Determine required resources, skills, and tools
6. **Risk Management**: Identify potential issues and mitigation strategies
7. **Timeline Development**: Create realistic schedules with buffer time
8. **Communication Plan**: Define reporting, meetings, and coordination processes

📋 **Project Planning Tools:**
- Use `read_file` to review project documents, requirements, and specifications
- Use `list_directory` to understand project structure and available resources
- Use `execute_safe_bash` to gather environment information and assess capabilities

🚀 **Project Success Factors:**
- Clear, measurable objectives and deliverables
- Realistic timelines with appropriate buffers
- Well-defined roles and responsibilities
- Regular checkpoints and progress reviews
- Proactive risk management and contingency planning
- Effective communication and stakeholder management

Create detailed project plans that provide clear roadmaps for successful project execution."""
}

def get_planner_system_prompt(prompt_type: str = "comprehensive") -> str:
    """
    Get a system prompt for the PLANNER node.

    Args:
        prompt_type: Type of planning prompt (comprehensive, technical, research, project)

    Returns:
        System prompt string
    """
    return PLANNER_SYSTEM_PROMPTS.get(prompt_type, PLANNER_SYSTEM_PROMPTS["comprehensive"])

# --- PLANNER Node Implementation ---

def planner_node(state: Dict[str, Any], prompt_type: str = "comprehensive"):
    """
    PLANNER node that analyzes tasks and creates detailed execution plans.

    Args:
        state: Current state of the multi-agent system
        prompt_type: Type of planning approach to use

    Returns:
        Updated state with planner response
    """
    logger.info("📋 PLANNER node starting task analysis")

    # Get system prompt based on type
    system_prompt = get_planner_system_prompt(prompt_type)

    # Create LLM client (reuse from main system)
    model_name = os.getenv("LLM_MODEL", "openai/gpt-4o")

    try:
        from multi_agent_system import create_llm_client
        model = create_llm_client(model_name)
    except ImportError:
        # Fallback if not available
        import httpx
        http_client = httpx.Client(
            verify=False,
            timeout=30.0,
            headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "PLANNER Node"
            }
        )

        model = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=SecretStr(key) if (key := os.getenv("OPENROUTER_API_KEY")) else None,
            model=model_name,
            http_client=http_client,
            timeout=30.0,
        )

    # Bind tools to model
    tools = [read_file, list_directory, execute_safe_bash]
    model_with_tools = model.bind_tools(tools)

    try:
        # Prepare messages for the planner
        messages = state.get("messages", [])
        messages_for_planner = [SystemMessage(content=system_prompt)] + messages

        # Log the planning prompt
        logger.info("🔍 PLANNER PROMPT:")
        for i, msg in enumerate(messages_for_planner):
            if hasattr(msg, 'content'):
                content = str(msg.content)
                logger.info(f"  Message {i+1} ({type(msg).__name__}): {content[:200]}{'...' if len(content) > 200 else ''}")
        logger.info("-------------------------------- END OF PLANNER PROMPT --------------------------------")

        # Get response from planner
        response = model_with_tools.invoke(messages_for_planner)

        response_content = str(response.content)
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "node": "planner",
            "prompt_type": prompt_type,
            "has_tool_calls": isinstance(response, AIMessage) and bool(response.tool_calls),
            "response_preview": response_content[:100] + "..." if len(response_content) > 100 else response_content,
            "response_full": response_content
        }

        return {
            "messages": [response],
            "debug_info": [debug_info]
        }

    except Exception as e:
        error_msg = AIMessage(content=f"PLANNER encountered an error: {str(e)}")
        return {
            "messages": [error_msg],
            "debug_info": [{"error": str(e), "node": "planner", "prompt_type": prompt_type}]
        }
