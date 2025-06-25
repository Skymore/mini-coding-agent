import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { prism } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface CodeBlockProps {
  code: string
  language: string
  title?: string
  showLineNumbers?: boolean
  maxHeight?: string
}

export function CodeBlock({ 
  code, 
  language, 
  title, 
  showLineNumbers = false,
  maxHeight = '400px'
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="relative rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">
            {language}
          </span>
          {title && (
            <span className="text-sm text-gray-700">{title}</span>
          )}
        </div>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-6 px-2 text-xs"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 mr-1 text-green-600" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="w-3 h-3 mr-1" />
              Copy
            </>
          )}
        </Button>
      </div>

      {/* Code content */}
      <div
        className="overflow-auto"
        style={{ maxHeight }}
      >
        {language && language !== 'text' ? (
          <SyntaxHighlighter
            language={language}
            style={prism as { [key: string]: React.CSSProperties }}
            customStyle={{
              margin: 0,
              borderRadius: 0,
              fontSize: '13px',
              backgroundColor: '#f6f8fa',
              padding: '16px'
            }}
            showLineNumbers={showLineNumbers}
            lineNumberStyle={{
              color: '#6e7781',
              fontSize: '12px',
              paddingRight: '16px',
              borderRight: '1px solid #d1d9e0',
              marginRight: '16px'
            }}
          >
            {code}
          </SyntaxHighlighter>
        ) : (
          // Fallback for plain text or unknown languages
          <div className="bg-gray-50 p-4 font-mono text-sm">
            <pre className="whitespace-pre-wrap text-gray-800">
              {code}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
