#!/usr/bin/env python3
"""
Multi-Agent Expert System Launcher
Provides options to run the system in different modes.
"""

import sys
import subprocess
import argparse
import time
from pathlib import Path
import os

# CLI demo removed - only web interface supported

def run_api_server():
    """Start the API server in the background."""
    print("📡 Starting API Server on port 8001...")
    try:
        # Pass current environment to the subprocess
        env = os.environ.copy()
        process = subprocess.Popen([sys.executable, "api_server.py"], env=env)
        return process
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        return None

def run_react_frontend():
    """Start the React frontend development server."""
    frontend_dir = Path("react-frontend")
    if not frontend_dir.exists():
        print("❌ React frontend directory not found!")
        return None
    
    print("🌐 Starting React Frontend on port 5173...")
    try:
        # Pass current environment to the subprocess
        env = os.environ.copy()
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            env=env
        )
        return process
    except Exception as e:
        print(f"❌ Error starting React frontend: {e}")
        return None

def run_web_system():
    """Start both API server and React frontend."""
    print("🚀 Starting Full Web System...")
    print("📡 API Server: http://localhost:8001")
    print("🌐 Frontend: http://localhost:5173")
    print("🔗 API Docs: http://localhost:8001/docs")
    print("⏹️  Press Ctrl+C to stop all servers")
    
    # Start API server
    api_process = run_api_server()
    if not api_process:
        return False
    
    # Wait a moment for API server to start
    time.sleep(2)
    
    # Start React frontend
    frontend_process = run_react_frontend()
    if not frontend_process:
        api_process.terminate()
        return False
    
    try:
        # Wait for user to stop
        while True:
            time.sleep(1)
            # Check if processes are still running
            if api_process.poll() is not None:
                print("❌ API server stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend server stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n👋 Stopping servers...")
        
    finally:
        # Clean up processes
        if api_process:
            api_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        
        # Wait for processes to finish
        if api_process:
            api_process.wait()
        if frontend_process:
            frontend_process.wait()
    
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    # Python dependencies
    python_packages = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "langgraph": "langgraph",
        "langchain-openai": "langchain_openai",
        "python-dotenv": "dotenv",
        "httpx": "httpx",
        "pydantic": "pydantic"
    }
    
    missing_python = []
    for package, import_name in python_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_python.append(package)
    
    if missing_python:
        print("❌ Missing Python packages:")
        for package in missing_python:
            print(f"   - {package}")
        print("\n💡 Install with: poetry install")
        return False
    
    # Check Node.js and npm for frontend
    frontend_dir = Path("react-frontend")
    if frontend_dir.exists():
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ npm not found. Install Node.js to run the React frontend.")
                return False
        except FileNotFoundError:
            print("❌ npm not found. Install Node.js to run the React frontend.")
            return False
        
        # Check if node_modules exists
        if not (frontend_dir / "node_modules").exists():
            print("⚠️  Frontend dependencies not installed.")
            print("💡 Run: cd react-frontend && npm install")
            return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Expert System Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_system.py --mode web     # Start full web system (API + React)
  python start_system.py --mode api     # Start API server only
  python start_system.py --check        # Check dependencies
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["web", "api"], 
        default="web",
        help="Run mode: 'web' for full system, 'api' for API only (default: web)"
    )
    
    parser.add_argument(
        "--check", 
        action="store_true",
        help="Check if all dependencies are installed"
    )
    
    args = parser.parse_args()
    
    print("🤖 Multi-Agent Expert System Launcher")
    print("=" * 50)
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    if args.check:
        print("✅ All dependencies are installed!")
        return
    
    # Set up environment
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("💡 Create a .env file with your OPENROUTER_API_KEY:")
        print("   OPENROUTER_API_KEY=your_api_key_here")
        print()
    
    # Run the selected mode
    if args.mode == "web":
        success = run_web_system()
    elif args.mode == "api":
        success = run_api_server() is not None
        if success:
            try:
                print("📡 API Server running. Press Ctrl+C to stop...")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 API Server stopped")
    else:
        print(f"❌ Unknown mode: {args.mode}")
        success = False
    
    if success:
        print("✅ System completed successfully")
    else:
        print("❌ System encountered errors")
        sys.exit(1)

if __name__ == "__main__":
    main() 