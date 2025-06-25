import { BaseMessageCard } from './BaseMessageCard'
import { MarkdownRenderer } from './MarkdownRenderer.tsx'

interface AIMessageCardProps {
  content: string
  expert?: string
  expert_icon?: string
  prompt?: { role: string; content: string }[]
}

export function AIMessageCard({ 
  content, 
  expert, 
  expert_icon, 
  prompt 
}: AIMessageCardProps) {
  return (
    <BaseMessageCard
      className="bg-muted"
      icon={<span className="text-base">{expert_icon}</span>}
      title={expert || 'AI Assistant'}
      showCopyButton={true}
      showDebugButton={true}
      copyContent={content}
      debugData={{ prompt }}
      customActions={[
        <div key="spacer-1" className="w-12" />,
        <div key="spacer-2" className="w-6" />,
      ]}
      showSuccessIndicator={true}
      success={true}
    >
      <div className="text-sm leading-relaxed">
        <MarkdownRenderer content={content} />
      </div>
    </BaseMessageCard>
  )
}
