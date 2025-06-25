import { Cog } from 'lucide-react'
import { BaseMessageCard } from './BaseMessageCard'
import { CodeBlock } from './CodeBlock'

interface ToolCallEvent {
  type: 'tool_call'
  tool_name: string
  command: string
  result: string
  success: boolean
  timestamp: string
  prompt?: { role: string; content: string }[]
  tool_args?: Record<string, unknown>
}

interface ToolCallCardProps {
  event: ToolCallEvent
}

interface ListDirectoryArgs {
  directory_path?: string;
  path?: string;
  directory?: string;
  dir?: string;
}

interface ReadFileArgs {
  file_path?: string;
  path?: string;
  filename?: string;
  file?: string;
  start_line_one_indexed?: number;
  end_line_one_indexed_inclusive?: number;
}

const getToolTitle = (event: ToolCallEvent) => {
  if (event.tool_name === 'read_file') {
    return 'Read file'
  } else if (event.tool_name === 'list_directory') {
    return 'List directory'
  } else {
    return event.tool_name
  }
}

const getMainContent = (event: ToolCallEvent) => {
  // Extract meaningful content based on tool type
  if (event.tool_name === 'list_directory') {
    const args = (event.tool_args || {}) as ListDirectoryArgs
    // Default to '.' if no path is provided, otherwise use the given path
    const dirPath = args?.directory_path || args?.path || args?.directory || args?.dir || '.'
    return dirPath
  } else if (event.tool_name === 'read_file') {
    // Show file path and line info - the correct parameter name is 'file_path'
    const args = (event.tool_args || {}) as ReadFileArgs
    const filePath = args?.file_path || args?.path || args?.filename || args?.file
    if (filePath) {
      const fileName = filePath.split('/').pop() || filePath
      const startLine = args?.start_line_one_indexed
      const endLine = args?.end_line_one_indexed_inclusive
      if (startLine && endLine) {
        return `${fileName} (lines ${startLine}-${endLine})`
      }
      return `${fileName} (entire file)`
    }
    // Fallback: try to extract from command if available
    if (event.command && event.command.includes('read_file')) {
      const match = event.command.match(/read_file\(['"]([^'"]+)['"]\)/)
      if (match) {
        const fileName = match[1].split('/').pop() || match[1]
        return `${fileName} (entire file)`
      }
    }
    return 'unknown file (entire file)'
  } else {
    // For other tools, show the command or tool name
    return event.command || event.tool_name
  }
}

export function ToolCallCard({ event }: ToolCallCardProps) {
  const colorClasses = event.success
    ? 'text-blue-600 bg-blue-50 border-blue-200'
    : 'text-red-600 bg-red-50 border-red-200'

  // Get file language for syntax highlighting
  const getLanguageFromPath = (filePath: string) => {
    const ext = filePath.split('.').pop()?.toLowerCase()
    const languageMap: Record<string, string> = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'jsx': 'jsx',
      'tsx': 'tsx',
      'html': 'html',
      'css': 'css',
      'json': 'json',
      'md': 'markdown',
      'yml': 'yaml',
      'yaml': 'yaml',
      'xml': 'xml',
      'sh': 'bash',
      'sql': 'sql',
      'txt': 'text'
    }
    return languageMap[ext || ''] || 'text'
  }

  const expandedContent = (
    <div>
      {event.tool_name === 'read_file' ? (
        // Special handling for read_file to show syntax highlighted content
        (() => {
          const args = (event.tool_args || {}) as ReadFileArgs
          const filePath = args?.file_path || args?.path || args?.filename || args?.file || ''
          let fileName = 'File content'

          if (filePath) {
            fileName = filePath.split('/').pop() || filePath
          } else if (event.command && event.command.includes('read_file')) {
            // Try to extract from command
            const match = event.command.match(/read_file\(['"]([^'"]+)['"]\)/)
            if (match) {
              fileName = match[1].split('/').pop() || match[1]
            }
          }

          const language = getLanguageFromPath(filePath || fileName)
          const startLine = args?.start_line_one_indexed
          const endLine = args?.end_line_one_indexed_inclusive
          const showLineNumbers = startLine && endLine ? true : true // Always show line numbers for read_file

          return (
            <CodeBlock
              code={event.result}
              language={language}
              title={fileName}
              showLineNumbers={showLineNumbers}
              maxHeight="500px"
            />
          )
        })()
      ) : event.tool_name === 'list_directory' ? (
        // Special handling for directory listings
        <CodeBlock
          code={event.result}
          language="text"
          title="Directory Contents"
          showLineNumbers={false}
          maxHeight="400px"
        />
      ) : (
        // Default result display for other tools using CodeBlock for consistency
        <CodeBlock
          code={event.result}
          language="text"
          title="Tool Output"
          showLineNumbers={false}
          maxHeight="400px"
        />
      )}
    </div>
  )
  
  return (
    <BaseMessageCard
      className={`border-l-4 ${colorClasses}`}
      icon={<Cog className="w-5 h-5 text-blue-600" />}
      title={getToolTitle(event)}
      showExpandButton={true}
      showDebugButton={true}
      showSuccessIndicator={true}
      expandedContent={expandedContent}
      debugData={{
        prompt: event.prompt,
        tool_args: event.tool_args
      }}
      success={event.success}
    >
      <div className="text-sm font-mono text-gray-700">
        {getMainContent(event)}
      </div>
    </BaseMessageCard>
  )
}
