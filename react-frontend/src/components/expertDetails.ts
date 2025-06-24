export interface ExpertInfo {
  icon: string
  color: string
  description: string
  tools: string[]
}

export const expertDetails: Record<string, ExpertInfo> = {
  "Coordinator": {
    icon: "🎯",
    color: "from-blue-500 to-blue-600",
    description: "Analyzes requests and routes them to the most appropriate specialist agent",
    tools: []
  },
  "CodeGenerator": {
    icon: "⚡",
    color: "from-purple-500 to-purple-600", 
    description: "Generates code solutions based on requirements and specifications",
    tools: ["write_file", "find_and_replace_in_file", "read_file", "list_directory", "execute_bash_command"]
  },
  "CodeReviewer": {
    icon: "✅",
    color: "from-orange-500 to-orange-600",
    description: "Reviews code quality, security, and adherence to best practices", 
    tools: ["read_file", "list_directory", "find_and_replace_in_file", "execute_bash_command"]
  }
} 