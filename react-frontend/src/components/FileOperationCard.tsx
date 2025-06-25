import { useState, useEffect, useCallback } from 'react'
import { ExternalLink, FilePlus, FileEdit, FileCode, X, Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { prism } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { BaseMessageCard } from './BaseMessageCard'
import { CodeBlock } from './CodeBlock'
import { DiffViewer } from './DiffViewer'

interface FileOperationEvent {
  type: 'file_operation'
  operation: 'created_file' | 'edited_file_full' | 'edited_file_diff'
  file_path: string
  success: boolean
  timestamp: string
  content?: string
  before_content?: string
  after_content?: string
  diff?: {
    diff_text: string
    added_lines: number
    removed_lines: number
    total_changes: number
  }
  prompt?: { role: string; content: string }[]
  tool_args?: Record<string, unknown>
}

interface FileOperationCardProps {
  event: FileOperationEvent
}

interface FileViewModalProps {
  isOpen: boolean
  onClose: () => void
  filePath: string
}

const FileViewModal = ({ isOpen, onClose, filePath }: FileViewModalProps) => {
  const [fileData, setFileData] = useState<{
    content: string
    language: string
    size: number
    lines: number
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const fetchFileContent = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`http://localhost:8001/file/view?file_path=${encodeURIComponent(filePath)}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch file: ${response.statusText}`)
      }
      const data = await response.json()
      setFileData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load file')
    } finally {
      setLoading(false)
    }
  }, [filePath])

  const handleCopy = async () => {
    if (fileData?.content) {
      try {
        await navigator.clipboard.writeText(fileData.content)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      } catch (err) {
        console.error('Failed to copy:', err)
      }
    }
  }

  useEffect(() => {
    if (isOpen && filePath) {
      fetchFileContent()
    }
  }, [isOpen, filePath, fetchFileContent])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-lg max-w-6xl max-h-[90vh] w-full flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold">File Viewer</h3>
            {fileData && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="bg-gray-100 px-2 py-1 rounded text-xs font-mono">
                  {fileData.language}
                </span>
                <span>{fileData.lines} lines</span>
                <span>{fileData.size} bytes</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {fileData && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                className="h-8"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-green-600" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* File path */}
        <div className="px-4 py-2 bg-gray-50 border-b">
          <div className="text-sm font-mono text-gray-600">{filePath}</div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-500">Loading file...</div>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center h-full">
              <div className="text-red-500">Error: {error}</div>
            </div>
          )}

          {fileData && (
            <div className="h-full overflow-auto">
              <SyntaxHighlighter
                language={fileData.language}
                style={prism as { [key: string]: React.CSSProperties }}
                customStyle={{
                  margin: 0,
                  borderRadius: 0,
                  fontSize: '14px',
                  backgroundColor: '#f6f8fa'
                }}
                showLineNumbers={true}
                lineNumberStyle={{ color: '#6e7781', fontSize: '12px' }}
              >
                {fileData.content}
              </SyntaxHighlighter>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

const getOperationIcon = (operation: string) => {
  switch (operation) {
    case 'created_file':
      return <FilePlus className="w-5 h-5 text-green-600" />
    case 'edited_file_full':
      return <FileEdit className="w-5 h-5 text-blue-600" />
    case 'edited_file_diff':
      return <FileEdit className="w-5 h-5 text-blue-600" />
    default:
      return <FileCode className="w-5 h-5 text-gray-600" />
  }
}

const getOperationTitle = (operation: string) => {
  switch (operation) {
    case 'created_file':
      return 'Created file'
    case 'edited_file_full':
      return 'Edited file'
    case 'edited_file_diff':
      return 'Edited file'
    default:
      return 'File operation'
  }
}

const getOperationColor = (operation: string, success: boolean) => {
  if (!success) return 'text-red-600 bg-red-50 border-red-200'
  
  switch (operation) {
    case 'created_file':
      return 'text-green-600 bg-green-50 border-green-200'
    case 'edited_file_full':
      return 'text-blue-600 bg-blue-50 border-blue-200'
    case 'edited_file_diff':
      return 'text-purple-600 bg-purple-50 border-purple-200'
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}

export function FileOperationCard({ event }: FileOperationCardProps) {
  const [showFileViewer, setShowFileViewer] = useState(false)

  const handleOpenInNewWindow = () => {
    setShowFileViewer(true)
  }

  const colorClasses = getOperationColor(event.operation, event.success)

  // Custom actions for file operations
  const customActions = [
    // Show diff stats for edited files
    event.operation !== 'created_file' && event.diff && (
      <div key="diff-stats" className="flex items-center gap-1 text-xs">
        <span className="text-green-600">+{event.diff.added_lines}</span>
        <span className="text-red-600">-{event.diff.removed_lines}</span>
      </div>
    ),
    // Open file button
    <Button
      key="open-file"
      variant="ghost"
      size="sm"
      onClick={handleOpenInNewWindow}
      className="h-6 w-6 p-0"
      title="Open File"
    >
      <ExternalLink className="w-4 h-4" strokeWidth={1.5} />
    </Button>
  ].filter(Boolean)

  // Detect file language from extension
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
      'sql': 'sql'
    }
    return languageMap[ext || ''] || 'text'
  }

  const expandedContent = (
    <>
      {/* File content for created files */}
      {event.operation === 'created_file' && event.content && (
        <div>
          <CodeBlock
            code={event.content}
            language={getLanguageFromPath(event.file_path)}
            title={event.file_path.split('/').pop()}
            showLineNumbers={true}
            maxHeight="400px"
          />
        </div>
      )}

      {/* Diff view for edited files */}
      {(event.operation === 'edited_file_full' || event.operation === 'edited_file_diff') &&
       event.diff && event.diff.diff_text && (
        <div>
          <DiffViewer
            diffText={event.diff.diff_text}
            title={event.file_path.split('/').pop()}
            maxHeight="400px"
          />
        </div>
      )}
    </>
  )

  return (
    <>
      <BaseMessageCard
        className={`border-l-4 ${colorClasses}`}
        icon={getOperationIcon(event.operation)}
        title={getOperationTitle(event.operation)}
        subtitle={undefined}
        showExpandButton={true}
        showDebugButton={true}
        showSuccessIndicator={true}
        customActions={customActions}
        expandedContent={expandedContent}
        debugData={{
          prompt: event.prompt,
          tool_args: event.tool_args
        }}
        success={event.success}
      >
        <div className="text-sm font-mono text-gray-700">
          {event.file_path.split('/').pop()}
        </div>
      </BaseMessageCard>

      <FileViewModal
        isOpen={showFileViewer}
        onClose={() => setShowFileViewer(false)}
        filePath={event.file_path}
      />
    </>
  )
}
