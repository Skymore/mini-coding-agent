# Mini Coding Agent

A modern multi-agent coding system built with LangGraph, designed to assist with software development tasks through intelligent agent collaboration.

## 🎯 Project Purpose & Learning Objectives

This **educational showcase** is designed to help developers understand key aspects of AI agent architectures and workflows, providing a practical foundation before tackling more complex systems. Specifically, this project highlights:

### 1. **Agent Specialization**

* Specialized roles assigned to different AI agents.
* Controlled tool access tailored per agent type.
* Domain-specific system prompts guiding agent behavior.

### 2. **Intelligent Task Routing**

* Decision-making powered by LLM for optimal task allocation.
* Contextual analysis to select appropriate expert agents.
* Effective fallback strategies to handle edge cases gracefully.

### 3. **Tool Integration and Execution**

* Integration of real-world development tools within agent workflows.
* Operations such as file system manipulation and command execution.
* Robust tool result processing with comprehensive error handling.

### 4. **Session Management and Context Preservation**

* Stateful conversation management with full history tracking.
* Effective serialization and deserialization of conversation data.
* Preservation and utilization of context across multiple interactions.

### 5. **Real-time Streaming and Feedback**

* Implementation of server-sent events (SSE) for real-time updates.
* Progressive and dynamic UI feedback during agent operations.
* Enhanced transparency through immediate reporting of agent actions and decisions.

## 🌟 Features

### 🧠 Specialized Code Agents
- **⚡ CodeGenerator**: Writes code, implements features, creates files
- **🔎 CodeReviewer**: Reviews code quality, finds bugs, suggests improvements
- **🎯 Coordinator**: Intelligently routes queries to the right specialist
- **📋 Planner**: Comprehensive task analysis, planning, and safe information gathering

### 🛠️ Development Tools
CodeReviewer and CodeGenerator agents have access to real development tools:
- `write_file()` - Create and write code files
- `read_file()` - Read and analyze existing code
- `find_and_replace_in_file()` - Modify code with precision
- `list_directory()` - Explore project structure
- `execute_bash_command()` - Run commands and tests

### 🎨 Real-time Web Interface
- **Live Chat**: Watch agents work in real-time with markdown formatting
- **Enhanced Message Display**: Rich rendering of code blocks, diffs, and terminal outputs
- **Prompt Inspection**: See exactly what each agent is thinking
- **Tool Execution**: Observe every tool call and result with dedicated UI components
- **Session History**: Complete conversation preservation

### 🔍 Full Transparency
- View the exact prompts sent to each AI agent
- See tool arguments and execution results
- Track the decision-making process step by step
- Debug agent behavior with complete visibility

### 🛡️ Security & Path Isolation
- **Path Restriction**: All file operations are restricted to session-specific directories
- **Relative Path Display**: Frontend only sees relative paths, protecting server details
- **Input Validation**: Path traversal attempts are blocked and logged

## 🏗️ Architecture & Technology Stack

### Core Technology Stack

**Backend:**
- **Orchestration**: `LangGraph` for building stateful, multi-agent applications.
- **Web Framework**: `FastAPI` for high-performance, async APIs.
- **LLM Integration**: `LangChain` & `langchain-openai` for seamless model interaction.
- **Dependencies**: Managed with `Poetry`.

**Frontend:**
- **Framework**: `React 18` with `TypeScript` for a robust, type-safe UI.
- **Build Tool**: `Vite` for an extremely fast and modern development experience.
- **UI Components**: A combination of `shadcn/ui` patterns, `Radix UI` primitives for accessibility, and `Lucide` for icons.
- **Styling**: `Tailwind CSS` for utility-first styling.
- **Animation**: `Framer Motion` for smooth and delightful animations.
- **Code Display**: Syntax highlighting with `react-syntax-highlighter` and diff visualization
- **Markdown**: Full GitHub-flavored markdown support with `react-markdown`

**Communication:**
- **Real-time Streaming**: `Server-Sent Events (SSE)` to stream agent responses live from the backend to the frontend, using `@microsoft/fetch-event-source` on the client.
- **Async Architecture**: The Python backend is fully asynchronous to handle concurrent agent operations without blocking.

### System Architecture Diagram

```
┌──────────────────┐      ┌───────────────────┐      ┌────────────────────┐
│  React Frontend  │◄────►│  FastAPI Backend  │◄────►│  LangGraph Engine  │
│                  │      │                   │      │                    │
│ • User Interface │      │ • API Routes      │      │ • Agent Orchestr   │
│ • Real-time Msgs │      │ • SSE Streaming   │      │ • State Mgmt       │
│ • Model Selection│      │ • Session Mgmt    │      │ • Tool Calling     │
└──────────────────┘      └───────────────────┘      └────────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐      ┌───────────────────┐      ┌────────────────────┐
│ User Interaction │      │  Message Process  │      │   Agent Collab     │
│                  │      │                   │      │                    │
│ • Code Requests  │      │ • Route Analysis  │      │ • Code Generator   │
│ • File Upload    │      │ • Stream Response │      │ • Code Reviewer    │
│ • Real-time Feed │      │ • Error Handling  │      │ • Coordinator      │
└──────────────────┘      └───────────────────┘      └────────────────────┘
```

### Supported AI Models & Pricing (2025)

This system provides unified model access through the **OpenRouter API**, which supports over 400 models from more than 50 providers. This offers automatic failover and flexible, pay-per-use pricing.

#### Model Selection Recommendations

- **For Daily Development**: `Claude Sonnet 4` or `Gemini 2.5 Pro` or `GPT-4.1`
- **For Rapid Prototyping**: `Claude Haiku 3.5` or `GPT-4.1 Mini`

#### 🔥 Latest & Recommended Models

A curated list of top-performing models available in the system:

| Model | Provider | Context | Strengths | Cost/1M tokens (In/Out) |
|---|---|---|---|---|
| **GPT-4.1** | OpenAI | 1M | Advanced reasoning, exceptional coding | $2.00 / $8.00 |
| **Claude Opus 4** | Anthropic | 200K | World-class coding, complex tasks | $15.00 / $75.00 |
| **Claude Sonnet 4**| Anthropic | 200K | Balanced intelligence, speed, and cost | $3.00 / $15.00 |
| **Gemini 2.5 Flash**| Google | 1M+ | Ultra-fast, multimodal, cost-effective | $0.15 / $0.60 |
| **Gemini 2.5 Pro**| Google | 1M+ | Ultra-fast, multimodal, cost-effective | $1.25($2.5, prompts > 200k tokens) / $10($15, prompts > 200k tokens) |
| **GPT-4.1 Mini** | OpenAI | 1M | GPT-4o performance, half the latency | $0.40 / $1.60 |

#### Default Configuration
The system comes pre-configured with these models, which can be changed in your `.env` file:
```bash
# Default models available in the UI dropdown
AVAILABLE_MODELS=openai/gpt-4o,openai/gpt-4o-mini,anthropic/claude-sonnet-4,google/gemini-2.5-pro,google/gemini-2.5-flash

# Default model used for new chat sessions
LLM_MODEL=openai/gpt-4o-mini
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+ (for React frontend)
- Poetry (for dependency management) OR pip
- OpenRouter API key (free tier available)

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd mini-coding-agent
   ```

2. **Set up environment variables:**
   ```bash
   # Create your environment file from the example
   cp .env.example .env
   ```
   Then, edit the new `.env` file to add your `OPENROUTER_API_KEY`.

3. **Install dependencies:**
    - **Using Poetry (Recommended):**
      ```bash
      # Install both Python and frontend dependencies
      poetry install
      cd react-frontend && npm install && cd ..
      ```
    - **Using Pip:**
      ```bash
      pip install -r requirements.txt
      cd react-frontend && npm install && cd ..
      ```

### Running the System

#### 🚀 Option 1: One-Command Start (Recommended)
This command will check dependencies, start both servers, and open the app in your browser.
```bash
poetry run python start_system.py
```

- **API Server**: http://localhost:8001
- **React Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8001/docs

#### 🔧 Option 2: Manual Start
**Start Backend API (in one terminal):**
```bash
poetry run python api_server.py
```

**Start Frontend (in a new terminal):**
```bash
cd react-frontend
npm run dev
```
Then visit: **http://localhost:5173** to start coding with AI agents!

## 🐛 Key Challenges & Solutions

Building a robust multi-agent system involves more than just wiring up an LLM. Here are some of the key technical hurdles we encountered and the solutions we implemented:

### 1. The Infinite Loop Problem
- **Problem**: In early versions, agents would get stuck in infinite loops, repeatedly calling the same tool with the same arguments, burning through API credits.
- **Solution**: We implemented a stateful `MultiAgentState` that tracks `tool_call_history` and `tool_failures`. The core fix was giving the agent a reliable conversation history so it could "see" its own previous steps and avoid repetition.

### 2. Multi-Provider LLM Compatibility Hell
- **Problem**: The system initially worked with OpenAI models, but failed spectacularly with Anthropic's Claude due to different API requirements for tool use.
- **Solution**: We adopted a much cleaner approach by creating a single, robust helper function (`_ensure_nonempty_assistant`) that acts as a "purifier" right before the API call to an Anthropic model. This centralized the fix and made the agent logic provider-agnostic.

### 3. State Management & Agent Amnesia
- **Problem**: Agents would "forget" what they had just done. The frontend was initially responsible for managing history, which is a common anti-pattern.
- **Solution**: We made the **backend the single source of truth** by implementing a `ChatSession` class on the server to hold the complete, lossless conversation history. The frontend is now a "dumb" renderer.

### 4. Fake vs. Real-Time Streaming
- **Problem**: The UI felt unresponsive because all of the agent's steps would appear at once at the very end.
- **Solution**: We created a custom generator function (`run_multi_agent_query_stream`) that `yield`s an event immediately after each step. In the FastAPI endpoint, we run this in a separate thread and use an `asyncio.Queue` to stream results, ensuring a non-blocking, truly real-time experience.

### 5. Security - Preventing Path Traversal
- **Problem**: An agent could be prompted to read or write files outside its designated working directory.
- **Solution**: We implemented a strict sandboxing mechanism (`_get_safe_path`) that resolves any user-provided path and critically checks if it remains within a secure base directory, raising a `ValueError` if it doesn't.

### 6. Performance - LLM Client Instantiation
- **Problem**: The system was creating a new `ChatOpenAI` client instance for every single LLM call.
- **Solution**: We leveraged Python's `functools.lru_cache` decorator on the `create_llm_client` function to reuse clients, significantly reducing instantiation overhead.

## 🛠️ Customization

### Adding New Agents
1. Define your expert in `EXPERT_DEFINITIONS` in `multi_agent_system.py`.
2. Create an agent node function (e.g., follow the `code_generator_node` pattern).
3. Add routing logic for it in the `coordinator_node`.
4. Register the new node in the `create_multi_agent_graph` function.

### Adding New Tools
1. Create tool with `@tool` decorator
2. Add to appropriate agent's tool list
3. Update tool executor mapping
4. Test with relevant queries

### Modifying System Prompts
Edit the system prompts in each agent function to change behavior:
- Make agents more/less verbose
- Add specific coding standards
- Include additional context or constraints

## 🐛 Debugging

The system provides complete transparency:
- **Prompt inspection**: See exactly what each agent receives
- **Tool execution logs**: Watch every tool call and result
- **Agent decisions**: Understand routing and task handling
- **Error tracking**: Full error messages and stack traces

## 📊 Output Structure

All code is written to the `output/` directory with timestamped sessions:
```
output/
└── 20240623_143052_123456/  # Session timestamp
    ├── binary_search.py     # Generated code
    ├── test_binary_search.py # Test files
    └── ...                  # Other files
```

## 🆘 Troubleshooting

### Common Issues

**"Missing API Key"**
- Create `.env` file with `OPENROUTER_API_KEY=your_key`
- Get free key from [OpenRouter](https://openrouter.ai/)

**"Poetry not found"**
- Install Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
- Or use pip: `pip install poetry`

**"Agents not working"**
- Check API server is running on port 8001
- Verify model is accessible (try different model in .env)
- Check browser console for errors

**"Tools not executing"**
- Check file permissions in output directory
- Verify Python environment has required packages
- Check tool execution logs in browser

**"Frontend not loading"**
- Ensure both servers are running (API:8001, Frontend:5173)
- Check npm dependencies: `cd react-frontend && npm install`
- Clear browser cache and refresh

### Port Information
- **API Server**: http://localhost:8001
- **React Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8001/docs

## 🎯 Next Steps

After understanding this system, you can:
1. **Scale up**: Add more specialized agents (Testing, Documentation, etc.)
2. **Add complexity**: Implement more sophisticated tool chains
3. **Integrate**: Connect to real development environments
4. **Extend**: Add code execution, testing frameworks, CI/CD integration

This project provides the foundation for understanding how production coding agents like GitHub Copilot, Cursor, and others work under the hood!

## 🔮 Future Improvements

### Enhanced Security & Sandboxing
Currently, the system uses basic path restriction for security. For production use, consider implementing container-based sandboxing:

#### Recommended Libraries (2024-2025)
- **`llm-sandbox`**: Lightweight, portable sandbox for LLM-generated code
  - Supports Docker, Kubernetes, Podman backends
  - Multi-language support (Python, JavaScript, Java, C++, Go)
  - Built-in resource limits and network isolation
  - Seamless LangChain/LangGraph integration

- **`AgentRun`**: Fast and secure Python code execution
  - Docker-based isolation with RestrictedPython checks
  - Automatic dependency management and caching
  - REST API ready for self-hosting
  - 97% test coverage, production-ready

- **`Together Code Interpreter`**: Commercial-grade solution
  - Firecracker-based micro-VMs for maximum security
  - Designed specifically for LLM agent workflows
  - Scalable to 100+ concurrent executions
  - $0.03/session pricing model

#### Implementation Strategy
```python
# Future integration example with llm-sandbox
from llm_sandbox import SandboxSession

@tool
def execute_code_safely(code: str, language: str = "python") -> str:
    """Execute code in a secure containerized environment."""
    with SandboxSession(lang=language) as session:
        result = session.run(code)
        return result.stdout if result.exit_code == 0 else result.stderr
```

### Performance Optimizations
- **LLM Client Caching**: ✅ Implemented - reduces connection overhead
- **Async SSE Streaming**: ✅ Implemented - prevents server blocking
- **Tool Call Deduplication**: Removed for better user experience
- **Container Warm-up**: Future - pre-warmed containers for faster execution

### Additional Agent Types
- **🧪 TestGenerator**: Automatically write unit tests for generated code.
- **📚 DocumentationAgent**: Generate comprehensive code documentation.
- **🔧 DevOpsAgent**: Handle deployment and infrastructure tasks.
- **🐛 DebugAgent**: Specialized in finding and fixing bugs.

## 🤝 Contributing

This is an educational project. Feel free to fork, experiment, and share your modifications and learnings.

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details. 
