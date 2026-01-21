import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, ExternalLink, Zap, Clock, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';
import axios from 'axios';
import { AssistantResponse, AssistantRequest } from '../../types/assistants';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: string[];
  metadata?: AssistantResponse['metadata'];
}

interface AssistantChatProps {
  assistantName: 'fintech' | 'code' | 'general';
  knowledgeBase: string;
  title: string;
  description: string;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

const AssistantChat: React.FC<AssistantChatProps> = ({
  assistantName,
  knowledgeBase,
  title,
  description,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const copyToClipboard = async (text: string, codeId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCodeId(codeId);
      setTimeout(() => setCopiedCodeId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setError(null);

    // Add user message
    const userMsg: Message = { role: 'user', content: userMessage };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const request: AssistantRequest = {
        message: userMessage,
        assistant: assistantName,
        knowledge_base: knowledgeBase,
      };

      const response = await axios.post<AssistantResponse>(
        `${API_URL}/assistants/${assistantName}/chat`,
        request
      );

      // Add assistant response
      const assistantMsg: Message = {
        role: 'assistant',
        content: response.data.answer,
        citations: response.data.citations,
        metadata: response.data.metadata,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error('Chat error:', err);
      const errorMsg = err.response?.data?.error || 'Failed to get response. Please try again.';
      setError(errorMsg);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${errorMsg}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-950 rounded-xl border border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-gray-800 bg-gray-900 flex-shrink-0">
        <h1 className="text-2xl font-bold text-white mb-2">{title}</h1>
        <p className="text-sm text-gray-400">{description}</p>
      </div>

      {/* Messages Area - Takes remaining space */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar min-h-0">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-12">
            <Bot size={48} className="mx-auto mb-4 opacity-20" />
            <p className="text-lg mb-2">Start a conversation</p>
            <p className="text-sm">Ask me anything about {title.toLowerCase()}.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={clsx(
              'flex gap-4 w-full',
              msg.role === 'user' ? 'justify-end' : ''
            )}
          >
            {msg.role === 'user' ? (
              <div className="flex gap-3 max-w-2xl flex-row-reverse">
                <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                  <User size={20} />
                </div>
                <div className="bg-blue-600/20 text-blue-100 border border-blue-600/30 rounded-2xl rounded-tr-none p-4">
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ) : (
              <div className="flex gap-4 w-full">
                <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center flex-shrink-0">
                  <Bot size={20} />
                </div>
                <div className="flex-1 space-y-4">
                  <div className="bg-gray-900/50 text-gray-100 border border-gray-800 rounded-lg p-6">
                    <div className="prose prose-invert prose-base max-w-none">
                      <ReactMarkdown
                        components={{
                          code: ({ node, className, children, ...props }: any) => {
                            const match = /language-(\w+)/.exec(className || '');
                            const isInline = !match;
                            
                            if (isInline) {
                              return (
                                <code className="bg-gray-800 px-1.5 py-0.5 rounded text-base font-mono text-blue-300" {...props}>
                                  {children}
                                </code>
                              );
                            }
                            
                            // For code blocks, return plain code element
                            // The pre component will wrap it with copy button
                            return (
                              <code className={clsx(className, "text-base font-mono")} {...props}>
                                {children}
                              </code>
                            );
                          },
                          pre: ({ children }: any) => {
                            // Extract code text for copying from the code element inside pre
                            const codeElement = React.Children.toArray(children)[0] as any;
                            const codeText = codeElement?.props?.children || '';
                            const cleanCodeText = String(codeText).replace(/\n$/, '');
                            const codeId = `code-${idx}-${Math.random().toString(36).substr(2, 9)}`;
                            const isCopied = copiedCodeId === codeId;
                            
                            return (
                              <div className="relative group -mx-6 my-6">
                                <div className="absolute top-3 right-3 z-10">
                                  <button
                                    onClick={() => copyToClipboard(cleanCodeText, codeId)}
                                    className={clsx(
                                      "p-2 rounded-md transition-all",
                                      "bg-gray-800/80 hover:bg-gray-700 border border-gray-700",
                                      "text-gray-400 hover:text-white",
                                      "opacity-0 group-hover:opacity-100"
                                    )}
                                    title="Copy code"
                                  >
                                    {isCopied ? (
                                      <Check size={16} className="text-green-400" />
                                    ) : (
                                      <Copy size={16} />
                                    )}
                                  </button>
                                </div>
                                <pre className="bg-gray-950 p-6 rounded-lg overflow-x-auto border border-gray-800">
                                  {children}
                                </pre>
                              </div>
                            );
                          },
                          p: ({ children }: any) => (
                            <p className="mb-4 text-gray-200 leading-relaxed last:mb-0">{children}</p>
                          ),
                          a: ({ href, children }: any) => (
                            <a
                              href={href}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:text-blue-300 underline"
                            >
                              {children}
                            </a>
                          ),
                          ul: ({ children }: any) => (
                            <ul className="mb-4 space-y-2 list-disc list-inside text-gray-200">{children}</ul>
                          ),
                          ol: ({ children }: any) => (
                            <ol className="mb-4 space-y-3 list-decimal ml-6 text-gray-200 marker:text-gray-400">
                              {children}
                            </ol>
                          ),
                          li: ({ children }: any) => {
                            // Render list items with inline content to keep numbers and headings together
                            // Handle case where markdown creates paragraphs inside list items
                            return (
                              <li className="text-gray-200 leading-relaxed">
                                <span className="[&>p]:inline [&>p]:m-0 [&>p:first-child]:before:content-[''] [&>strong]:font-semibold [&>strong]:mr-2">
                                  {React.Children.map(children, (child) => {
                                    if (React.isValidElement(child) && child.type === 'p') {
                                      // Convert paragraph to inline span
                                      return <span className="inline">{child.props.children}</span>;
                                    }
                                    return child;
                                  })}
                                </span>
                              </li>
                            );
                          },
                          h1: ({ children }: any) => (
                            <h1 className="text-2xl font-bold text-white mb-4 mt-6 first:mt-0">{children}</h1>
                          ),
                          h2: ({ children }: any) => (
                            <h2 className="text-xl font-bold text-white mb-3 mt-5 first:mt-0">{children}</h2>
                          ),
                          h3: ({ children }: any) => (
                            <h3 className="text-lg font-semibold text-white mb-2 mt-4 first:mt-0">{children}</h3>
                          ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {/* Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="space-y-2 pt-4 border-t border-gray-800">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sources
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {msg.citations.map((url, i) => (
                          <a
                            key={i}
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-800/50 hover:bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-300 hover:text-white transition-colors"
                          >
                            <ExternalLink size={12} />
                            <span className="max-w-xs truncate">{url}</span>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Metadata Badges */}
                  {msg.metadata && (
                    <div className="flex flex-wrap gap-2 pt-2">
                      {msg.metadata.rag_used && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded text-xs">
                          <Zap size={12} />
                          RAG Used
                        </span>
                      )}
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-800 text-gray-400 border border-gray-700 rounded text-xs">
                        {msg.metadata.model}
                      </span>
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-800 text-gray-400 border border-gray-700 rounded text-xs">
                        <Clock size={12} />
                        {msg.metadata.latency_ms}ms
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center flex-shrink-0">
              <Bot size={20} />
            </div>
            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-800 flex items-center gap-2">
              <Loader2 size={16} className="animate-spin text-gray-400" />
              <span className="text-sm text-gray-400">Thinking...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Fixed to bottom */}
      <form onSubmit={handleSubmit} className="p-6 bg-gray-900 border-t border-gray-800 flex-shrink-0">
        <div className="relative w-full">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask about ${title.toLowerCase()}...`}
            disabled={loading}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-4 pr-12 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AssistantChat;
