import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, Brain, Settings, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { v4 as uuidv4 } from 'uuid'
import { fetchEventSource } from '@microsoft/fetch-event-source'

const MarkdownRenderer = ({ content }: { content: string }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ inline, className, children, ...props }: React.HTMLAttributes<HTMLElement> & { inline?: boolean }) {
          const match = /language-(\w+)/.exec(className || '')
          return !inline && match ? (
            <SyntaxHighlighter
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              style={vscDarkPlus as any}
              language={match[1]}
              PreTag="div"
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className={className} {...props}>
              {children}
            </code>
          )
        }
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

interface EventData {
  type: string
  message?: {
    id: string
    type: 'user' | 'agent' | 'tool_call' | 'tool_result' | 'routing'
    content: string
    expert?: string
    expert_icon?: string
    timestamp: string
    tool_name?: string
    tool_args?: Record<string, unknown>
    prompt?: { role: string; content: string }[]
  }
  error?: string
  session_id?: string
}

interface Message {
  id: string
  type: 'user' | 'agent' | 'tool_call' | 'tool_result' | 'routing'
  content: string
  expert?: string
  expert_icon?: string
  timestamp: Date
  tool_name?: string
  tool_args?: Record<string, unknown>
  prompt?: { role: string; content: string }[]
}

interface Expert {
  name: string
  description: string
  icon: string
  tools: string[]
}

interface Model {
  id: string
  name: string
  provider: string
}

const exampleQueries = [
  "Write a binary search algorithm in Python",
  "Create a simple calculator and test it",
  "Build a REST API endpoint with FastAPI",
  "Review the code quality in my files"
]

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>(() => [{
    id: '1',
    type: 'agent',
    content: 'Hello! I\'m your Code Agent System. I have two specialists ready to help you: **CodeGenerator** ⚡ for writing code and **CodeReviewer** ✅ for analyzing code quality. What would you like to build today?',
    expert: 'System',
    expert_icon: '🤖',
    timestamp: new Date()
  }])
  
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'chat' | 'experts' | 'settings'>('chat')
  const [experts, setExperts] = useState<Record<string, Expert>>({})
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [models, setModels] = useState<Model[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [showModelDropdown, setShowModelDropdown] = useState(false)
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const modelDropdownRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    const loadExperts = async () => {
      try {
        const response = await fetch('http://localhost:8001/experts')
        const data = await response.json()
        setExperts(data.experts)
      } catch (error) {
        console.error('Failed to load experts:', error)
      }
    }
    loadExperts()
  }, [])

  useEffect(() => {
    const loadModels = async () => {
      try {
        const response = await fetch('http://localhost:8001/models')
        const data = await response.json()
        setModels(data.models)
        setSelectedModel(data.default_model)
      } catch (error) {
        console.error('Failed to load models:', error)
      }
    }
    loadModels()
  }, [])

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('http://localhost:8001/health')
        if (response.ok) {
          setHealthStatus('healthy')
        } else {
          setHealthStatus('unhealthy')
        }
      } catch (error) {
        console.error('Health check failed:', error)
        setHealthStatus('unhealthy')
      }
    }
    
    // Check health immediately
    checkHealth()
    
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const clearChat = useCallback(() => {
    setMessages([{
      id: '1',
      type: 'agent',
      content: 'Hello! I\'m your Code Agent System. I have two specialists ready to help you: **CodeGenerator** ⚡ for writing code and **CodeReviewer** ✅ for analyzing code quality. What would you like to build today?',
      expert: 'System',
      expert_icon: '🤖',
      timestamp: new Date()
    }])
    setSessionId(null)
  }, [])

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: uuidv4(),
      type: 'user',
      content: input,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      await fetchEventSource('http://localhost:8001/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          session_id: sessionId,
          model: selectedModel,
        }),
        onmessage(event) {
          if (event.data) {
            try {
              const eventData: EventData = JSON.parse(event.data)
              console.log('📥 Received event:', eventData.type, eventData)

              if (eventData.session_id && !sessionId) {
                setSessionId(eventData.session_id)
              }
              
              if (eventData.type === 'message' && eventData.message) {
                const newMessage: Message = {
                  id: eventData.message.id,
                  type: eventData.message.type,
                  content: eventData.message.content,
                  expert: eventData.message.expert,
                  expert_icon: eventData.message.expert_icon,
                  timestamp: new Date(eventData.message.timestamp),
                  tool_name: eventData.message.tool_name,
                  tool_args: eventData.message.tool_args,
                  prompt: eventData.message.prompt as unknown as {role:string;content:string}[]
                }
                setMessages(prev => [...prev, newMessage])
              } else if (eventData.type === 'error') {
                throw new Error(eventData.error)
              } else if (eventData.type === 'end') {
                setIsLoading(false)
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', event.data, parseError)
            }
          }
        },
        onclose() {
          console.log('Connection closed by the server.')
          setIsLoading(false)
        },
        onerror(err) {
          console.error('EventSource failed:', err)
          const errorMessage: Message = {
            id: uuidv4(),
            type: 'agent',
            content: `An unexpected error occurred: ${err.message || 'Unknown error'}`,
            expert: 'System',
            expert_icon: '❌',
            timestamp: new Date(),
          }
          setMessages(prev => [...prev, errorMessage])
          setIsLoading(false)
          throw err // Stop retries
        },
      })
    } catch (e) {
      // Error is handled in onerror, this catch is for any other setup errors
      console.error("Streaming chat setup failed:", e)
      if (isLoading) {
        setIsLoading(false)
      }
    }
  }, [input, isLoading, sessionId, selectedModel])

  const setExampleQuery = useCallback((query: string) => {
    setInput(query)
  }, [])

  // Use Map to manage each message's prompt display state
  const [promptStates, setPromptStates] = useState<Map<string, boolean>>(new Map())
  
  const togglePrompt = useCallback((messageId: string) => {
    setPromptStates(prev => {
      const newMap = new Map(prev)
      newMap.set(messageId, !newMap.get(messageId))
      return newMap
    })
  }, [])

  // Effect to handle clicks outside the model dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (modelDropdownRef.current && !modelDropdownRef.current.contains(event.target as Node)) {
        setShowModelDropdown(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [modelDropdownRef])

  // Use useMemo to optimize message rendering
  const renderedMessages = useMemo(() => {
    return messages.map((message) => {
      const showPrompt = promptStates.get(message.id) || false
      
      const PromptSection = ({ prompt }: { prompt: { role: string; content: string }[] }) => (
        <div className="mt-2">
          <button 
            className="text-xs underline" 
            onClick={() => togglePrompt(message.id)}
          >
            {showPrompt ? 'Hide Prompt' : 'View Prompt'}
          </button>
          {showPrompt && (
            <div className="mt-1 bg-white/60 rounded p-2 max-h-40 overflow-y-auto text-xs font-mono whitespace-pre-wrap">
              {JSON.stringify(prompt, null, 2)}
            </div>
          )}
        </div>
      )
      
      return (
        <motion.div
          key={message.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={cn(
            "flex w-full",
            message.type === 'user' ? 'justify-end' : 'justify-start'
          )}
        >
          <div className={cn(
            "rounded-2xl px-4 py-3 shadow-sm",
            message.type === 'user' 
              ? 'bg-primary text-primary-foreground ml-12 max-w-[80%]' 
              : 'bg-muted mr-12 max-w-[85%]' 
          )}>
            {message.type !== 'user' && (
              <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
                <span className="text-base">{message.expert_icon}</span>
                <span className="font-medium">{message.expert}</span>
              </div>
            )}
            
            <div className="text-sm leading-relaxed">
              {message.type === 'tool_call' ? (
                <div>
                  {message.prompt && <PromptSection prompt={message.prompt} />}
                  <div className="p-2 bg-orange-50 border border-orange-200 rounded">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-orange-600">🔧</span>
                      <span className="text-xs text-orange-700 font-medium">Calling tool: {message.tool_name}</span>
                    </div>
                    <details className="mb-2">
                      <summary className="text-xs cursor-pointer text-orange-600 hover:text-orange-800">
                        View arguments
                      </summary>
                      <div className="mt-1 text-xs bg-white/50 rounded p-2 font-mono">
                        <pre className="whitespace-pre-wrap">
                          {JSON.stringify(message.tool_args, null, 2)}
                        </pre>
                      </div>
                    </details>
                    {message.content && (
                      <div className="text-sm">
                        <MarkdownRenderer content={message.content} />
                      </div>
                    )}
                  </div>
                </div>
              ) : message.type === 'tool_result' ? (
                <div className="p-3 bg-green-50 border border-green-200 rounded">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-green-600">✅</span>
                    <span className="text-xs text-green-700 font-medium">Tool Result</span>
                  </div>
                  <div className="text-sm bg-white/80 rounded p-2 font-mono text-green-800 max-h-32 overflow-y-auto">
                    <pre className="whitespace-pre-wrap">
                      {message.content}
                    </pre>
                  </div>
                </div>
              ) : (
                <>
                  {message.prompt && <PromptSection prompt={message.prompt} />}
                  <MarkdownRenderer content={message.content} />
                </>
              )}
            </div>
            
            <div className="text-xs opacity-60 mt-2">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </motion.div>
      )
    })
  }, [messages, promptStates, togglePrompt])

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="w-80 border-r bg-muted/30 p-4">
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h1 className="font-bold text-lg">Mini Coding Agent</h1>
              <p className="text-sm text-muted-foreground">Educational Showcase</p>
            </div>
            <div className="flex items-center gap-1">
              <div 
                className={`w-2 h-2 rounded-full ${
                  healthStatus === 'healthy' ? 'bg-green-500' : 
                  healthStatus === 'unhealthy' ? 'bg-red-500' : 
                  'bg-yellow-500 animate-pulse'
                }`}
              />
              <span className="text-xs text-muted-foreground">
                {healthStatus === 'healthy' ? 'Online' : 
                 healthStatus === 'unhealthy' ? 'Offline' : 
                 'Checking...'}
              </span>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex bg-muted rounded-lg p-1">
            {[
              { id: 'chat', icon: Bot, label: 'Chat' },
              { id: 'experts', icon: Brain, label: 'Agents' },
              { id: 'settings', icon: Settings, label: 'Settings' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'chat' | 'experts' | 'settings')}
                className={cn(
                  "flex-1 flex items-center justify-center gap-1 py-2 px-2 rounded-md text-xs font-medium transition-colors",
                  activeTab === tab.id 
                    ? "bg-background text-foreground shadow-sm" 
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <tab.icon className="w-3 h-3" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="space-y-4">
            <AnimatePresence mode="wait">
            {activeTab === 'chat' && (
                <motion.div
                  key="chat"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-3"
                >
                  <div className="flex items-center justify-between">
                <h3 className="font-medium text-sm">Quick Examples</h3>
                    <Button variant="ghost" size="sm" onClick={clearChat}>
                      Clear
                    </Button>
                  </div>
                {exampleQueries.map((query, index) => (
                  <button
                      key={`${query}-${index}`}
                      onClick={() => setExampleQuery(query)}
                    className="w-full text-left p-3 rounded-lg bg-background hover:bg-accent text-sm transition-colors"
                  >
                    {query}
                  </button>
                ))}
                </motion.div>
            )}

            {activeTab === 'experts' && (
                <motion.div
                  key="experts"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-3"
                >
                <h3 className="font-medium text-sm">Available Code Agents</h3>
                {Object.values(experts).map((expert, index) => (
                    <div key={`${expert.name}-${index}`} className="p-3 rounded-lg bg-background border">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">{expert.icon}</span>
                      <span className="font-medium text-sm">{expert.name}</span>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">
                      {expert.description}
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {expert.tools.map(tool => (
                        <span key={tool} className="px-2 py-1 bg-muted rounded text-xs">
                          {tool}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
                </motion.div>
            )}

            {activeTab === 'settings' && (
                <motion.div
                  key="settings"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-4"
                >
                  <h3 className="font-medium text-sm">Model Selection</h3>
                  <div className="relative" ref={modelDropdownRef}>
                    <button
                      onClick={() => setShowModelDropdown(!showModelDropdown)}
                      className="w-full flex items-center justify-between p-3 rounded-lg bg-background border text-sm"
                    >
                      <span>
                        {models.find(m => m.id === selectedModel)?.name || selectedModel}
                      </span>
                      <ChevronDown className="w-4 h-4" />
                    </button>
                    {showModelDropdown && (
                      <div className="absolute top-full left-0 right-0 mt-1 bg-background border rounded-lg shadow-lg z-10 max-h-60 overflow-y-auto">
                        {models.map(model => (
                          <button
                            key={model.id}
                            onClick={() => {
                              setSelectedModel(model.id)
                              setShowModelDropdown(false)
                            }}
                            className={cn(
                              "w-full text-left p-3 text-sm hover:bg-accent",
                              selectedModel === model.id && "bg-accent"
                            )}
                          >
                            <div className="font-medium">{model.name}</div>
                            <div className="text-xs text-muted-foreground">{model.provider}</div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Current model: {models.find(m => m.id === selectedModel)?.provider || 'Unknown'}
                  </div>
                </motion.div>
            )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <AnimatePresence>
            {renderedMessages}
          </AnimatePresence>
          
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-muted rounded-2xl px-4 py-3 mr-12 max-w-[85%]">
                <div className="flex items-center gap-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                  <span className="text-sm text-muted-foreground">Expert is working...</span>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t p-6">
          <form onSubmit={(e) => { e.preventDefault(); sendMessage(); }} className="flex gap-3">
            <div className="flex-1 relative">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask our code agents to write or review code..."
                disabled={isLoading}
                className="w-full px-4 py-3 border rounded-xl bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50"
              />
            </div>
            <Button 
              type="submit" 
              disabled={isLoading || !input.trim()}
              size="lg"
              className="px-6"
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
} 