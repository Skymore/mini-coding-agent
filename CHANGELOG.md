# Changelog

All notable changes to the Multi-Agent System project will be documented in this file.

## [0.2.0] - 2024-06-24

### Added
- **Enhanced Frontend Components**: Complete UI redesign with specialized message rendering
  - `BaseMessageCard`: Unified base component for all message types
  - `AIMessageCard`: Rich AI response display with markdown and code highlighting
  - `ToolCallCard`: Dedicated tool execution visualization with syntax highlighting for read_file
  - `FileOperationCard`: File creation/modification with diff display and file viewer modal
  - `TerminalCard`: Terminal command output with proper formatting
  - `CodeBlock`: Syntax highlighted code with copy functionality
  - `DiffViewer`: Enhanced diff visualization with proper color coding
  - `MarkdownRenderer`: Full GitHub-flavored markdown support
- **Improved Chat Interface**: Modular architecture with better separation of concerns
- **Real-time Features**: Enhanced streaming with proper UI updates for each event type
- **File Viewing Modal**: Click-to-view functionality for created/modified files
- **Backend API**: New `/file/view` endpoint for secure file content retrieval
- **Documentation**: Commit convention guide in `docs/commit-convention.md`

### Changed
- **Frontend Architecture**: Refactored from monolithic ChatInterface to modular components
- **Message Rendering**: Switched from inline rendering to component-based approach
- **Code Display**: Upgraded to `react-syntax-highlighter` for better code highlighting
- **Markdown Support**: Implemented `react-markdown` with remark/rehype plugins
- **Tool Display**: Show actual file/directory names instead of generic placeholders
- **Layout**: Standardized left-aligned layout for all message content

### Enhanced
- **User Experience**: 
  - Better visual hierarchy with consistent card-based design
  - Improved code readability with syntax highlighting based on file extensions
  - Clear separation between different message types with visual borders
  - Copy-to-clipboard functionality for code blocks
  - Expand/collapse functionality with proper icon placement
  - Consistent icon sizes across all message types
- **Developer Experience**:
  - Type-safe component props with TypeScript
  - Reusable component library for future extensions
  - Clear component boundaries and responsibilities
- **Tool Integration**:
  - Fixed tool parameter extraction (directory_path vs path naming)
  - Enhanced diff tracking for file operations
  - Improved error handling and user feedback

### Fixed
- **Backend**: Tool parameter naming consistency issues
- **Testing**: Model ID references updated (gemini-flash-2.5 → gemini-2.5-flash)
- **UI**: Icon alignment and sizing inconsistencies

## [0.1.0] - 2024-06-24

### Added
- **Enhanced File Operation Tools**: Added intelligent file operation events
  - `created_file` event for new file creation with content tracking
  - `edited_file_full` event for complete file replacement with diff display
  - `edited_file_diff` event for partial file modifications with diff display
- **Comprehensive Test Suite**: Extended testing to cover all experts and tools
  - `test_all_experts.py`: Tests all 4 experts (Coordinator, CodeGenerator, CodeReviewer, Planner)
  - `test_all_tools.py`: Tests all 6 tools with security validation
  - `test_node_functionality.py`: Focused PLANNER node testing
- **Extended Examples**: Expanded from 3 to 7 examples covering all experts
  - PLANNER examples: Project analysis, system exploration, feature planning
  - CODEGEN examples: New feature creation, bug fixes
  - REVIEWER examples: Code quality review, security audit
- **Cost-Optimized Testing**: Using `google/gemini-2.5-flash` for affordable testing
- **Security Enhancements**: Comprehensive command whitelisting and path validation
- **Documentation**: Complete testing guide and usage documentation

### Changed
- **File Naming**: Renamed test files to remove `planner` prefix for clarity
  - `test_planner_node.py` → `test_node_functionality.py`
  - `planner_examples.py` → `examples_all_experts.py`
- **Code Standards**: All code comments and documentation now English-only
- **Documentation Structure**: Merged PLANNER guide into main README
- **Tool Descriptions**: Updated to reflect new event-driven file operations

### Enhanced
- **write_file Tool**: 
  - Now detects if file exists before writing
  - Generates appropriate events (`created_file` vs `edited_file_full`)
  - Captures before/after content for diff generation
- **find_and_replace_in_file Tool**:
  - Now generates `edited_file_diff` events
  - Captures precise changes with line-by-line diff
  - Reports modification statistics (+X -Y lines)

### Fixed
- **Test Environment**: Automatic test_sandbox copying to output directory
- **Path Compatibility**: Resolved sandbox path issues for PLANNER tools
- **Model Configuration**: Standardized on cost-effective gemini-flash model

### Security
- **Command Validation**: Enhanced safe command execution with comprehensive whitelist
- **Sandbox Isolation**: Improved file operation security within output directory
- **Input Sanitization**: Strengthened validation for all tool inputs

## [Previous] - Before 2024-06-24

### Initial Implementation
- Basic multi-agent system with 4 experts
- Core tools: read_file, write_file, list_directory, find_and_replace_in_file, execute_bash_command
- PLANNER node with safe command execution
- Basic routing and tool execution
- Initial test suite and examples

---

## Legend
- **Added**: New features
- **Changed**: Changes in existing functionality  
- **Enhanced**: Improvements to existing features
- **Fixed**: Bug fixes
- **Security**: Security-related changes
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
