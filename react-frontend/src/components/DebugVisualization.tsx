import { expertDetails } from './expertDetails'

interface DebugVisualizationProps {
  expert?: string
  className?: string
}

export function DebugVisualization({ expert, className }: DebugVisualizationProps) {
  if (!expert || !expertDetails[expert]) {
    return (
      <div className={className}>
        <div className="p-4 bg-muted rounded-lg">
          <h3 className="text-sm font-medium mb-2">Expert Information</h3>
          <p className="text-xs text-muted-foreground">
            {expert ? `Unknown expert: ${expert}` : 'No expert selected'}
          </p>
        </div>
      </div>
    )
  }

  const expertInfo = expertDetails[expert]

  return (
    <div className={className}>
      <div className="p-4 bg-background border rounded-lg">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-2xl">{expertInfo.icon}</span>
          <div>
            <h3 className="font-medium">{expert}</h3>
            <p className="text-sm text-muted-foreground">{expertInfo.description}</p>
          </div>
        </div>
        
        <div className="space-y-3">
          <div>
            <h4 className="text-sm font-medium mb-2">Available Tools</h4>
            <div className="flex flex-wrap gap-1">
              {expertInfo.tools.map(tool => (
                <span 
                  key={tool} 
                  className="px-2 py-1 bg-muted rounded text-xs font-mono"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>
          

        </div>
      </div>
    </div>
  )
}

export function ExpertGrid() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Object.keys(expertDetails).map((name) => (
        <DebugVisualization key={name} expert={name} />
      ))}
    </div>
  )
}
