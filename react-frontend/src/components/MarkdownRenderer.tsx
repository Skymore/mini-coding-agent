import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { prism } from 'react-syntax-highlighter/dist/esm/styles/prism'
import * as React from 'react'

export const MarkdownRenderer = ({ content }: { content: string }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ inline, className, children, ...props }: React.HTMLAttributes<HTMLElement> & { inline?: boolean }) {
          const match = /language-(\w+)/.exec(className || '')
          return !inline && match ? (
            <SyntaxHighlighter
              style={prism as any} // eslint-disable-line @typescript-eslint/no-explicit-any
              language={match[1]}
              PreTag="div"
              customStyle={{
                borderRadius: '8px',
                backgroundColor: '#f6f8fa'
              }}
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className={`${className} bg-gray-100 px-1 py-0.5 rounded text-sm`} {...props}>
              {children}
            </code>
          )
        },
        pre({ children }) {
          return <div className="overflow-x-auto">{children}</div>
        },
        blockquote({ children }) {
          return (
            <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4">
              {children}
            </blockquote>
          )
        },
        table({ children }) {
          return (
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse border border-gray-300">
                {children}
              </table>
            </div>
          )
        },
        th({ children }) {
          return (
            <th className="border border-gray-300 px-4 py-2 bg-gray-100 font-semibold text-left">
              {children}
            </th>
          )
        },
        td({ children }) {
          return (
            <td className="border border-gray-300 px-4 py-2">
              {children}
            </td>
          )
        }
      }}
    >
      {content}
    </ReactMarkdown>
  )
}
