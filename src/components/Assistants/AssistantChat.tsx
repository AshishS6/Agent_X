import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, ExternalLink, Zap, Clock, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';
// Removed axios import
// Removed unused type imports

interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: string[];
  metadata?: any;
}

interface AssistantChatProps {
  assistantName: 'fintech' | 'code' | 'general';
  knowledgeBase: string;
  title: string;
  description: string;
  headerSlot?: React.ReactNode;
  showHeader?: boolean;
  composerLeftSlot?: React.ReactNode;
  introTitle?: string;
  introDescription?: string;
  samplePrompts?: string[];
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

const AssistantChat: React.FC<AssistantChatProps> = ({
  assistantName,
  knowledgeBase,
  title,
  description,
  headerSlot,
  showHeader = true,
  composerLeftSlot,
  introTitle,
  introDescription,
  samplePrompts,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

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
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    // Add placeholder assistant message
    setMessages((prev) => [...prev, { role: 'assistant', content: '', citations: [], metadata: {} }]);

    let assistantContent = '';
    let assistantMetadata: any = {};

    try {
      const response = await fetch(`${API_URL}/assistants/${assistantName}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          assistant: assistantName,
          knowledge_base: knowledgeBase,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Network response was not ok');
      }

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep the last incomplete line

          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const data = JSON.parse(line);

              if (data.type === 'content') {
                assistantContent += data.content;
                setMessages((prev) => {
                  const newMsgs = [...prev];
                  const lastMsg = newMsgs[newMsgs.length - 1];
                  if (lastMsg.role === 'assistant') {
                    lastMsg.content = assistantContent;
                  }
                  return newMsgs;
                });
              } else if (data.type === 'meta') {
                // Initial metadata (citations, etc.)
                assistantMetadata = { ...assistantMetadata, ...data };

                setMessages((prev) => {
                  const newMsgs = [...prev];
                  const lastMsg = newMsgs[newMsgs.length - 1];
                  if (lastMsg.role === 'assistant') {
                    if (data.citations) lastMsg.citations = data.citations;
                    lastMsg.metadata = { ...lastMsg.metadata, ...data };
                  }
                  return newMsgs;
                });
              } else if (data.type === 'control' && data.event === 'metadata') {
                // LLM Provider metadata (e.g. { provider: 'openai', model_id: 'openai:gpt-4' })
                const controlMeta = { ...data.data };

                // Normalize model name (remove provider prefix if present)
                if (controlMeta.model_id) {
                  controlMeta.model = controlMeta.model_id.includes(':')
                    ? controlMeta.model_id.split(':')[1]
                    : controlMeta.model_id;
                }

                assistantMetadata = { ...assistantMetadata, ...controlMeta };
                setMessages((prev) => {
                  const newMsgs = [...prev];
                  const lastMsg = newMsgs[newMsgs.length - 1];
                  if (lastMsg.role === 'assistant') {
                    lastMsg.metadata = { ...lastMsg.metadata, ...controlMeta };
                  }
                  return newMsgs;
                });
              } else if (data.type === 'control' && data.event === 'usage') {
                // Usage metadata (tokens, cost, latency)
                assistantMetadata = { ...assistantMetadata, ...data.data };
                setMessages((prev) => {
                  const newMsgs = [...prev];
                  const lastMsg = newMsgs[newMsgs.length - 1];
                  if (lastMsg.role === 'assistant') {
                    lastMsg.metadata = { ...lastMsg.metadata, ...data.data };
                  }
                  return newMsgs;
                });
              } else if (data.type === 'error') {
                throw new Error(data.error);
              }
            } catch (e) {
              console.error('Error parsing JSON chunk', e);
            }
          }
        }

        if (done) break;
      }

    } catch (err: any) {
      console.error('Chat error:', err);
      const errorMsg = err.message || 'Failed to get response. Please try again.';
      setError(errorMsg);

      // Update the last message to show error
      setMessages((prev) => {
        const newMsgs = [...prev];
        const lastMsg = newMsgs[newMsgs.length - 1];
        if (lastMsg.role === 'assistant' && !lastMsg.content) {
          lastMsg.content = `Error: ${errorMsg}`;
        }
        return newMsgs;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-950 rounded-xl border border-gray-800 overflow-hidden">
      {/* Header (optional) */}
      {(showHeader || headerSlot) && (
        <div className="p-4 border-b border-gray-800 bg-gray-900 flex-shrink-0">
          {headerSlot}
          {showHeader && (
            <div className={clsx(headerSlot ? 'mt-3' : '')}>
              <h2 className="text-xl font-semibold text-white">{title}</h2>
              <p className="text-sm text-gray-400 mt-1">{description}</p>
            </div>
          )}
        </div>
      )}

      {/* Messages Area - Takes remaining space */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar min-h-0">
        {messages.length === 0 && (
          <div className="max-w-3xl mx-auto mt-10">
            <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-gray-800 border border-gray-700 flex items-center justify-center shrink-0">
                  <Bot size={18} className="text-gray-300" />
                </div>
                <div className="min-w-0">
                  <p className="text-white font-semibold text-lg">
                    {introTitle || `How can I help with ${title}?`}
                  </p>
                  <p className="text-sm text-gray-400 mt-1">
                    {introDescription || description}
                  </p>
                </div>
              </div>

              {samplePrompts && samplePrompts.length > 0 && (
                <div className="mt-5">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Try one of these
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {samplePrompts.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => {
                          setInput(prompt);
                          inputRef.current?.focus();
                        }}
                        className="px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700 text-gray-200 text-sm hover:bg-gray-800 hover:border-gray-600 transition-colors"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
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
                            <p className="mb-4 text-gray-200 leading-relaxed last:mb-0">{children}
                            </p>
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
                                  {React.Children.map(children, (child, i) => {
                                    if (React.isValidElement(child) && child.type === 'p') {
                                      // Convert paragraph to inline span
                                      return <span key={i} className="inline">{(child.props as any).children}</span>;
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

                      {msg.metadata.model && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-800 text-gray-400 border border-gray-700 rounded text-xs">
                          {msg.metadata.model}
                        </span>
                      )}

                      {msg.metadata.latency_ms > 0 && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-800 text-gray-400 border border-gray-700 rounded text-xs">
                          <Clock size={12} />
                          {Math.round(msg.metadata.latency_ms)}ms
                        </span>
                      )}

                      {((msg.metadata.input_tokens || 0) + (msg.metadata.output_tokens || 0)) > 0 && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-800 text-gray-400 border border-gray-700 rounded text-xs">
                          {(msg.metadata.input_tokens || 0) + (msg.metadata.output_tokens || 0)} tokens
                        </span>
                      )}
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
            {/* 
                Only show thinking spinner if content is empty (waiting for first token).
                Once content starts streaming, the new message bubble appears.
            */}
            {messages.length > 0 && messages[messages.length - 1].role === 'assistant' && !messages[messages.length - 1].content && (
              <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-800 flex items-center gap-2">
                <Loader2 size={16} className="animate-spin text-gray-400" />
                <span className="text-sm text-gray-400">Thinking...</span>
              </div>
            )}
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
        <div className="flex items-center gap-3">
          {composerLeftSlot && (
            <div className="shrink-0">
              {composerLeftSlot}
            </div>
          )}
          <div className="relative w-full">
            <input
              ref={inputRef}
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
        </div>
      </form>
    </div>
  );
};

export default AssistantChat;
