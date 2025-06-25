from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Generator, Optional, AsyncGenerator
import uvicorn
import logging
import json
import asyncio
import uuid
from datetime import datetime
from multi_agent_system import run_multi_agent_query_stream, EXPERT_DEFINITIONS, MessageInput
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to INFO level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Silence overly verbose third-party loggers
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)  # Disable OpenAI verbose logs
logging.getLogger("openai._base_client").setLevel(logging.WARNING)  # Disable OpenAI base client DEBUG logs
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # Reduce uvicorn access logs

# Keep our own loggers at INFO level
logging.getLogger("api_server").setLevel(logging.INFO)
logging.getLogger("multi_agent_system").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent Expert System API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev server ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session Management
class ChatSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        # messages fed back to model (BaseMessage list)
        self.messages: List[BaseMessage] = []
        # prompts keyed by message id for auditing / frontend display
        self.prompts: Dict[str, List[Dict[str, Any]]] = {}
        # tool call ID mapping for consistency
        self.tool_call_ids: Dict[str, str] = {}
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
    
    def get_messages(self) -> List[Dict[str, Any]]:
        # Only return clean messages (no prompt) for next model call
        return [msg.dict() for msg in self.messages]

# In-memory session storage
sessions: Dict[str, ChatSession] = {}

def get_or_create_session(session_id: Optional[str] = None) -> ChatSession:
    if session_id and session_id in sessions:
        return sessions[session_id]
    new_session_id = str(uuid.uuid4())
    session = ChatSession(new_session_id)
    sessions[new_session_id] = session
    logger.info(f"Created new session: {new_session_id}")
    return session

# Request/Response Models
class StreamQueryRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    model: Optional[str] = None  # Allow frontend to configure model

class ModelConfigRequest(BaseModel):
    model: str

class ModelListResponse(BaseModel):
    models: List[Dict[str, str]]
    default_model: str

# Available models configuration
def get_available_models():
    """Load available models list from environment variables"""
    # Read models list from environment variable
    models_str = os.getenv("AVAILABLE_MODELS", "openai/gpt-4o,openai/gpt-4o-mini,anthropic/claude-sonnet-4")
    model_ids = [model.strip() for model in models_str.split(",")]
    
    # Build models list
    models = []
    for model_id in model_ids:
        # Read model name from MODEL_NAME_<model_id> environment variable
        name_key = f"MODEL_NAME_{model_id}".replace("/", "/")
        model_name = os.getenv(name_key, model_id.replace("/", " ").title())
        
        # Read provider from MODEL_PROVIDER_<model_id> environment variable  
        provider_key = f"MODEL_PROVIDER_{model_id}".replace("/", "/")
        provider = os.getenv(provider_key, model_id.split("/")[0].title() if "/" in model_id else "Unknown")
        
        models.append({
            "id": model_id,
            "name": model_name,
            "provider": provider
        })
    
    return models

DEFAULT_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o")

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Multi-Agent Expert System API"}

@app.get("/models")
async def get_available_models_endpoint():
    """Get list of available models for frontend configuration"""
    return ModelListResponse(
        models=get_available_models(),
        default_model=DEFAULT_MODEL
    )

@app.post("/chat/stream")
async def chat_stream_endpoint(request: StreamQueryRequest):
    """
    The single endpoint for all chat interactions.
    Streams execution steps and uses session-based history.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Set model if specified by frontend
    if request.model:
        os.environ["LLM_MODEL"] = request.model
        logger.info(f"Using model: {request.model}")
    else:
        # Use default model
        current_model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
        logger.info(f"Using default model: {current_model}")

    session = get_or_create_session(request.session_id)
    # Save human message to session history
    session.messages.append(HumanMessage(content=request.message))
    
    logger.info(f"Session {session.session_id}: Received query '{request.message}' (History: {len(session.messages)} msgs)")
    
    def _save_event_to_session(ev: Dict[str, Any]):
        """Convert SSE event into BaseMessage and append to session."""
        if ev.get("type") != "message":
            return
        m = ev.get("message", {})
        m_type = m.get("type")
        if m_type == "agent":
            session.messages.append(AIMessage(content=m.get("content", "")))
        elif m_type == "tool_call":
            # Represent as AIMessage with tool_calls
            prompt = m.get("prompt")
            tool_call_id = str(uuid.uuid4())  # Generate a consistent ID
            # Save original content to session (empty string for tool calls)
            session.messages.append(
                AIMessage(content="", tool_calls=[{
                    "id": tool_call_id,
                    "name": m.get("tool_name"),
                    "args": m.get("tool_args", {})
                }])
            )
            if prompt:
                session.prompts[m["id"]] = prompt
            # Store the tool call ID for later use
            session.tool_call_ids[m.get("tool_name")] = tool_call_id
        elif m_type == "tool_result":
            # Use the stored tool call ID
            tool_call_id = session.tool_call_ids.get(m.get("tool_name"), str(uuid.uuid4()))
            session.messages.append(
                ToolMessage(content=m.get("content", ""), tool_call_id=tool_call_id)
            )
        
        # Save prompt for agent messages
        if m_type == "agent" and m.get("prompt"):
            session.prompts[m["id"]] = m["prompt"]

    async def stream_generator() -> AsyncGenerator[str, None]:
        queue = asyncio.Queue()

        def producer():
            """Runs the sync agent code and puts events into the queue."""
            try:
                # The agent system is now the source of truth for message history
                for event in run_multi_agent_query_stream(session.get_messages()):
                    queue.put_nowait(event)
            except Exception as e:
                # Put exception in queue to be raised in the main thread
                queue.put_nowait(e)
            finally:
                # Use a sentinel value to signal completion
                queue.put_nowait(None)
        
        # Run the synchronous generator in a separate thread
        loop = asyncio.get_event_loop()
        producer_task = loop.run_in_executor(None, producer)

        try:
            while True:
                # Wait for an event from the producer thread
                event = await queue.get()

                # Check for sentinel value or exception
                if event is None:
                    break
                if isinstance(event, Exception):
                    raise event

                event["session_id"] = session.session_id
                event_json = json.dumps(event)
                logger.info(f"📤 Sending event: {event.get('type', 'unknown')} - {event_json[:100]}...")
                _save_event_to_session(event)
                yield f"data: {event_json}\n\n"
        
        except Exception as e:
            logger.error(f"Error during stream for session {session.session_id}: {e}", exc_info=True)
            error_event = {"type": "error", "error": str(e), "session_id": session.session_id}
            yield f"data: {json.dumps(error_event)}\n\n"
        
        finally:
            # Ensure producer task is cleaned up
            if not producer_task.done():
                producer_task.cancel()
            logger.info(f"Session {session.session_id} stream completed.")
            # Send a final "end" event to the client
            end_event = {"type": "end", "session_id": session.session_id}
            yield f"data: {json.dumps(end_event)}\n\n"

    return StreamingResponse(
        stream_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "Multi-Agent Expert System API"
    }

@app.get("/experts")
async def get_experts():
    return {"experts": EXPERT_DEFINITIONS}

@app.get("/file/view")
async def view_file(file_path: str):
    """
    View file content
    """
    try:
        from pathlib import Path

        # Security check: search for the file in allowed locations
        search_dirs = [
            Path.cwd(),
            Path.cwd() / "output",
            Path.cwd() / "test_sandbox"
        ]
        
        found_path: Optional[Path] = None
        
        # To handle file paths from different OS, normalize them
        normalized_file_path = Path(file_path)

        # 1. Check for absolute path first
        if normalized_file_path.is_absolute() and normalized_file_path.exists():
            found_path = normalized_file_path
        
        # 2. If not absolute, search in the standard directories
        if not found_path:
            for directory in search_dirs:
                candidate = directory / normalized_file_path
                if candidate.exists() and candidate.is_file():
                    found_path = candidate
                    break
        
        # 3. If still not found, search recursively inside 'output' for session folders
        if not found_path:
            output_dir = Path.cwd() / "output"
            if output_dir.exists():
                # Use rglob to find the file in any subdirectory of output
                candidates = list(output_dir.rglob(normalized_file_path.name))
                if candidates:
                    found_path = candidates[0]  # Use the first match

        if not found_path:
            raise HTTPException(status_code=404, detail=f"File not found in any allowed directory: {file_path}")

        file_path_obj = found_path.resolve()
        
        # Check if the final resolved path is within allowed directories
        allowed_dirs_resolved = [d.resolve() for d in search_dirs]
        is_allowed = any(
            str(file_path_obj).startswith(str(allowed_dir))
            for allowed_dir in allowed_dirs_resolved
        )

        if not is_allowed:
            raise HTTPException(status_code=403, detail="Access to this file is not allowed")

        if not file_path_obj.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        # Read file content
        try:
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path_obj, 'r', encoding='latin-1') as f:
                content = f.read()

        # Detect file type for syntax highlighting
        file_extension = file_path_obj.suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.xml': 'xml',
            '.sh': 'bash',
            '.sql': 'sql',
            '.txt': 'text'
        }
        language = language_map.get(file_extension, 'text')

        return {
            "file_path": str(file_path_obj),
            "content": content,
            "language": language,
            "size": len(content),
            "lines": len(content.splitlines())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting Multi-Agent Expert System API Server...")
    print("🔗 API documentation at: http://localhost:8001/docs")
    print("📡 API server running on: http://localhost:8001")
    print("💡 Start React frontend separately with: cd react-frontend && npm run dev")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8001, 
        reload=False,
        log_level="info"
    ) 