import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ChatInterface } from './components/ChatInterface'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background text-foreground">
        <ChatInterface />
      </div>
    </QueryClientProvider>
  )
}

export default App
