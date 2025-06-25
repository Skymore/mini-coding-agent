import { MonitorSpeaker } from 'lucide-react'
import { BaseMessageCard } from './BaseMessageCard'
import { CodeBlock } from './CodeBlock'

interface TerminalEvent {
  type: 'terminal'
  tool_name: string
  command: string
  result: string
  success: boolean
  timestamp: string
  prompt?: { role: string; content: string }[]
  tool_args?: Record<string, unknown>
}

interface TerminalCardProps {
  event: TerminalEvent
}

export function TerminalCard({ event }: TerminalCardProps) {
  const colorClasses = event.success
    ? 'text-green-600 bg-green-50 border-green-200'
    : 'text-red-600 bg-red-50 border-red-200'

  const expandedContent = (
    <div>
      <CodeBlock
        code={event.result}
        language="bash"
        title="Terminal Output"
        showLineNumbers={false}
        maxHeight="320px"
      />
    </div>
  )

  return (
    <BaseMessageCard
      className={`border-l-4 ${colorClasses}`}
      icon={<MonitorSpeaker className="w-5 h-5 text-gray-700" />}
      title="Terminal"
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
        <span className="text-green-600 font-bold">$</span> {event.command}
      </div>
    </BaseMessageCard>
  )
}
