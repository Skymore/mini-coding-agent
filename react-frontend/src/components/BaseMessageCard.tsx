import { useState, ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronRight, Bug, X, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface BaseMessageCardProps {
  // Basic props
  className?: string
  colorClasses?: string
  
  // Header props
  icon?: ReactNode
  title: string
  subtitle?: string
  
  // Action buttons
  showExpandButton?: boolean
  showDebugButton?: boolean
  showCopyButton?: boolean
  showSuccessIndicator?: boolean
  customActions?: ReactNode[]
  
  // Content
  children: ReactNode
  expandedContent?: ReactNode
  
  // Data for debug and copy
  debugData?: {
    prompt?: { role: string; content: string }[]
    tool_args?: Record<string, unknown>
  }
  copyContent?: string
  
  // State
  defaultExpanded?: boolean
  success?: boolean
}

interface DebugModalProps {
  isOpen: boolean
  onClose: () => void
  prompt?: { role: string; content: string }[]
  tool_args?: Record<string, unknown>
}

const DebugModal = ({ isOpen, onClose, prompt, tool_args }: DebugModalProps) => {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div 
        className="bg-white rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-y-auto m-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Debug Information</h3>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
        
        {tool_args && (
          <div className="mb-6">
            <h4 className="text-sm font-medium mb-2">Tool Arguments</h4>
            <div className="bg-gray-100 rounded-lg p-3 font-mono text-xs">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(tool_args, null, 2)}
              </pre>
            </div>
          </div>
        )}
        
        {prompt && (
          <div>
            <h4 className="text-sm font-medium mb-2">Prompt</h4>
            <div className="bg-gray-100 rounded-lg p-3 font-mono text-xs max-h-64 overflow-y-auto">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(prompt, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export function BaseMessageCard({
  className,
  colorClasses,
  icon,
  title,
  subtitle,
  showExpandButton = false,
  showDebugButton = false,
  showCopyButton = false,
  showSuccessIndicator = false,
  customActions = [],
  children,
  expandedContent,
  debugData,
  copyContent,
  defaultExpanded = false,
  success
}: BaseMessageCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const [showDebug, setShowDebug] = useState(false)
  const [copied, setCopied] = useState(false)
  
  const handleCopy = async () => {
    if (copyContent) {
      try {
        await navigator.clipboard.writeText(copyContent)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      } catch (err) {
        console.error('Failed to copy:', err)
      }
    }
  }
  
  return (
    <>
      <Card className={cn('w-full transition-all duration-200', colorClasses, className)}>
        <div className="p-3">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0 flex-1">
              {/* Expand button or placeholder */}
              {(showExpandButton || expandedContent) ? (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="h-5 w-5 p-0 flex-shrink-0"
                >
                  {isExpanded ? (
                    <ChevronDown className="w-3 h-3" strokeWidth={1.5} />
                  ) : (
                    <ChevronRight className="w-3 h-3" strokeWidth={1.5} />
                  )}
                </Button>
              ) : (
                <div className="w-5 h-5 flex-shrink-0" /> // Placeholder
              )}

              {icon}
              <div className="min-w-0 flex-1">
                <div className="font-medium text-sm">{title}</div>
                {subtitle && (
                  <div className="text-xs text-muted-foreground mt-0.5 font-mono">{subtitle}</div>
                )}
              </div>
            </div>

            <div className="flex items-center justify-end gap-1.5 ml-3" style={{ minWidth: '80px' }}>
              {/* Custom actions */}
              {customActions.map((action, index) => (
                <div key={index}>{action}</div>
              ))}

              {/* Copy button */}
              {showCopyButton && copyContent && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                  className="h-5 w-5 p-0"
                  title="Copy"
                >
                  {copied ? (
                    <Check className="w-3 h-3 text-green-600" strokeWidth={1.5} />
                  ) : (
                    <Copy className="w-3 h-3" strokeWidth={1.5} />
                  )}
                </Button>
              )}

              {/* Debug button */}
              {showDebugButton && (debugData?.prompt || debugData?.tool_args) && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowDebug(true)}
                  className="h-5 w-5 p-0"
                  title="Debug Info"
                >
                  <Bug className="w-3 h-3" strokeWidth={1.5}/>
                </Button>
              )}

              {/* Success indicator */}
              {showSuccessIndicator && (
                success ? (
                  <Check className="w-3 h-3 text-green-600" strokeWidth={1.5}/>
                ) : (
                  <X className="w-3 h-3 text-red-600" strokeWidth={1.5}/>
                )
              )}
            </div>
          </div>
          
          {/* Main content */}
          <div className="mt-2 ml-7">
            {children}
          </div>
        </div>
        
        {/* Expanded content */}
        <AnimatePresence>
          {isExpanded && expandedContent && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="px-3 pb-3 border-t border-gray-200">
                <div className="mt-2">
                  {expandedContent}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
      
      <DebugModal 
        isOpen={showDebug}
        onClose={() => setShowDebug(false)}
        prompt={debugData?.prompt}
        tool_args={debugData?.tool_args}
      />
    </>
  )
}
