import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface DiffViewerProps {
  diffText: string
  title?: string
  maxHeight?: string
}

export function DiffViewer({ 
  diffText, 
  title = "Diff",
  maxHeight = '400px'
}: DiffViewerProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(diffText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const lines = diffText.split('\n')

  return (
    <div className="relative rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">
            DIFF
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

      {/* Diff content */}
      <div 
        className="overflow-auto font-mono text-sm"
        style={{ maxHeight }}
      >
        <div className="bg-gray-50">
          {lines.map((line, index) => {
            let className = 'px-4 py-1 border-l-4 border-transparent'
            let bgColor = ''
            let textColor = 'text-gray-800'
            let prefix = ''
            
            if (line.startsWith('+++') || line.startsWith('---')) {
              bgColor = 'bg-gray-100'
              textColor = 'text-gray-600'
              className += ' font-semibold'
            } else if (line.startsWith('@@')) {
              bgColor = 'bg-blue-50'
              textColor = 'text-blue-800'
              className += ' font-semibold border-l-blue-300'
            } else if (line.startsWith('+')) {
              bgColor = 'bg-green-50'
              textColor = 'text-green-800'
              className += ' border-l-green-400'
              prefix = '+'
            } else if (line.startsWith('-')) {
              bgColor = 'bg-red-50'
              textColor = 'text-red-800'
              className += ' border-l-red-400'
              prefix = '-'
            } else {
              bgColor = 'bg-white'
            }
            
            return (
              <div 
                key={index} 
                className={`${className} ${bgColor} ${textColor}`}
              >
                {prefix && (
                  <span className="select-none opacity-60 mr-2 font-bold">
                    {prefix}
                  </span>
                )}
                <span className="whitespace-pre">
                  {line.substring(prefix.length)}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
