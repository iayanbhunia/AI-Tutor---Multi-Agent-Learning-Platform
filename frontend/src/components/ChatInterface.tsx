import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useAppStore } from '../store/store';
import { Send, Bot, User as UserIcon, Loader2, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

class ErrorBoundary extends React.Component<{children: React.ReactNode, fallback?: React.ReactNode}, {hasError: boolean, error: any}> {
  constructor(props: any) { super(props); this.state = { hasError: false, error: null }; }
  static getDerivedStateFromError(error: any) { return { hasError: true, error }; }
  render() { 
    if (this.state.hasError) return this.props.fallback || <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> Failed to render component.</div>; 
    return this.props.children; 
  }
}

const MermaidRenderer = ({ chartStr, setSelectedImage }: { chartStr: string, setSelectedImage: (src: string) => void }) => {
  const [hasError, setHasError] = useState(false);

  if (hasError) {
    return (
      <div className="my-4">
        <div className="text-xs text-amber-400 p-2 border border-amber-500/20 rounded-t-lg bg-amber-500/10 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" /> Diagram rendering failed. Showing raw code:
        </div>
        <pre className="bg-zinc-950 p-4 rounded-b-lg overflow-x-auto border border-t-0 border-zinc-800">
          <code className="text-zinc-300 text-[13px] font-mono">{chartStr}</code>
        </pre>
      </div>
    );
  }

  try {
    // Encode to base64 safely handling unicode
    const b64 = btoa(unescape(encodeURIComponent(chartStr)));
    const src = `https://mermaid.ink/img/${b64}`;
    return (
      <div className="bg-white p-2 rounded-lg border border-zinc-800 my-4 overflow-x-auto flex justify-center">
        <img 
          src={src} 
          alt="Mermaid diagram" 
          className="max-w-full cursor-pointer hover:opacity-90 transition-opacity" 
          onClick={() => setSelectedImage(src)}
          onError={() => setHasError(true)} 
        />
      </div>
    );
  } catch (err) {
    return <div className="text-xs text-red-400 p-2 border border-red-500/20 rounded-lg bg-red-500/10">Failed to encode diagram</div>;
  }
};

export default function ChatInterface() {
  const { user, activePath, chatHistory, setChatHistory, addChatMessage, updateLastMessage } = useAppStore();
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingStatus, setStreamingStatus] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const markdownComponents = useMemo(() => ({
    code({node, inline, className, children, ...props}: any) {
      const match = /language-(\w+)/.exec(className || '');
      if (!inline && match && match[1] === 'mermaid') {
        const chartStr = String(children).replace(/\n$/, '');
        return <MermaidRenderer chartStr={chartStr} setSelectedImage={setSelectedImage} />;
      }
      return !inline ? (
        <pre className="bg-zinc-950 p-4 rounded-lg overflow-x-auto border border-zinc-800">
          <code className={className} {...props}>
            {children}
          </code>
        </pre>
      ) : (
        <code className="bg-zinc-800 text-zinc-200 px-1.5 py-0.5 rounded text-[13px] font-mono border border-zinc-700" {...props}>
          {children}
        </code>
      )
    },
    img({node, src, alt, ...props}: any) {
      return (
        <ErrorBoundary fallback={<div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> Failed to load image</div>}>
          <img 
            src={src} 
            alt={alt} 
            className="max-w-full rounded-lg border border-zinc-800 my-4 cursor-pointer hover:opacity-90 transition-opacity" 
            onClick={() => setSelectedImage(src)}
            onError={(e) => (e.currentTarget.style.display = 'none')} 
            {...props} 
          />
        </ErrorBoundary>
      )
    }
  }), [setSelectedImage]);

  const bottomRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (activePath && user) {
      fetch(`/api/chat/history/${activePath}?user_id=${user.user_id}`)
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            const normalizedHistory = data.map(msg => ({
              ...msg,
              response: msg.agent === 'user' ? (msg.query || msg.response) : msg.response
            }));
            setChatHistory(normalizedHistory);
          }
        });
      
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/chat/${activePath}?user_id=${user.user_id}`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'status') {
          setStreamingStatus(data.content);
        } else if (data.type === 'chunk') {
          updateLastMessage(data.content);
          setStreamingStatus(null);
        } else if (data.type === 'done') {
          setIsStreaming(false);
          setStreamingStatus(null);
        } else if (data.type === 'trigger_quiz') {
          const msgId = Date.now().toString() + '_quiz';
          const moduleName = data.module;
          
          useAppStore.getState().addChatMessage({
            id: msgId,
            agent: 'system',
            response: 'Creating quiz...',
            timestamp: new Date().toISOString(),
            isQuizTrigger: true,
            quizModule: moduleName,
            quizStatus: 'loading'
          });

          // Fetch the quiz in the background
          const { user, activePath } = useAppStore.getState();
          if (user && activePath) {
            fetch('/api/quiz/start', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ user_id: user.user_id, session_id: activePath })
            })
            .then(res => res.json())
            .then(quizData => {
              useAppStore.getState().updateQuizTriggerMessage(msgId, 'ready', quizData);
            })
            .catch(err => console.error('Failed to fetch quiz', err));
          }
        }
      };

      return () => {
        if (wsRef.current) wsRef.current.close();
      };
    }
  }, [activePath, user]);

  useEffect(() => {
    const handleQuizCompleted = (e: Event) => {
      const customEvent = e as CustomEvent;
      const moduleName = customEvent.detail.module;
      
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          prompt: `[System Action]: The user has successfully passed the quiz for module '${moduleName}'. The syllabus state has been updated to mark this module as completed. You MUST now proceed to teach the very next topic in the syllabus.`,
          hidden: true
        }));
      }
    };

    window.addEventListener('quiz_completed', handleQuizCompleted);
    return () => window.removeEventListener('quiz_completed', handleQuizCompleted);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, streamingStatus]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !activePath || !wsRef.current || isStreaming) return;

    const userMsg = {
      id: Date.now().toString(),
      agent: 'user',
      response: input,
      timestamp: new Date().toISOString()
    };
    
    addChatMessage(userMsg);
    
    addChatMessage({
      id: Date.now().toString() + '_ai',
      agent: 'ai_tutor',
      response: '',
      timestamp: new Date().toISOString()
    });

    setIsStreaming(true);
    setStreamingStatus('Analyzing...');
    
    wsRef.current.send(JSON.stringify({
      prompt: input
    }));

    setInput('');
  };

  if (!activePath) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-zinc-500 bg-zinc-950">
        <div className="w-12 h-12 rounded-lg border border-zinc-800 bg-zinc-900 flex items-center justify-center mb-4">
          <Bot className="w-6 h-6 text-zinc-400" />
        </div>
        <h2 className="text-lg font-medium text-zinc-300 mb-1">Select a Learning Path</h2>
        <p className="text-sm">Choose an existing path or create a new one to start.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col relative bg-zinc-950 min-h-0 items-center">
      <div className="flex-1 overflow-y-auto w-full max-w-3xl p-6 space-y-8 custom-scrollbar pb-32">
        {chatHistory.map((msg, idx) => (
          <div key={msg.id || idx} className={`flex gap-4 ${msg.agent === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-md flex items-center justify-center shrink-0 border ${msg.agent === 'user' ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-100 border-zinc-200'}`}>
              {msg.agent === 'user' ? <UserIcon className="w-4 h-4 text-zinc-300" /> : <Bot className="w-4 h-4 text-zinc-900" />}
            </div>
            <div className={`min-w-0 max-w-[85%] ${msg.agent === 'user' ? 'pt-1.5' : 'bg-zinc-900 border border-zinc-800 rounded-xl p-5'}`}>
              {msg.agent !== 'user' && (
                <div className="text-[11px] font-semibold text-zinc-500 mb-2 uppercase tracking-wide flex items-center gap-2">
                  {msg.agent.replace('_', ' ')}
                </div>
              )}
              
              <div className="prose prose-invert prose-zinc max-w-none prose-sm">
                {msg.isQuizTrigger ? (
                  <div className="mt-2">
                    {msg.quizStatus === 'completed' ? (
                      <div className="p-4 bg-emerald-950/30 border border-emerald-900/50 rounded-xl">
                        <h4 className="font-medium text-emerald-400 flex items-center gap-2 mb-2">
                          <CheckCircle2 className="w-4 h-4" />
                          Quiz Completed: {msg.quizScore || "Pass"}
                        </h4>
                        <p className="text-zinc-300 text-sm m-0">
                          {msg.quizFeedback || "Great job completing the module assessment!"}
                        </p>
                      </div>
                    ) : msg.quizStatus === 'abandoned' ? (
                      <div className="p-4 bg-red-950/30 border border-red-900/50 rounded-xl">
                        <h4 className="font-medium text-red-400 flex items-center gap-2 mb-2">
                          <XCircle className="w-4 h-4" />
                          Quiz Abandoned
                        </h4>
                        <p className="text-zinc-400 text-sm m-0">
                          You closed the quiz before finishing. Ask the AI Tutor to generate a new quiz to proceed.
                        </p>
                      </div>
                    ) : (
                      <button
                        onClick={() => {
                          if (msg.quizStatus === 'ready' && msg.quizModule) {
                            useAppStore.getState().setQuizState(true, msg.quizModule, msg.id as string);
                          }
                        }}
                        disabled={msg.quizStatus !== 'ready'}
                        className={`w-full flex items-center justify-between p-4 rounded-xl border transition-all ${
                          msg.quizStatus === 'ready' 
                            ? 'bg-indigo-500/10 border-indigo-500/30 hover:border-indigo-500 text-indigo-100 cursor-pointer shadow-[0_0_15px_rgba(99,102,241,0.1)] hover:shadow-[0_0_20px_rgba(99,102,241,0.2)]' 
                            : 'bg-zinc-900 border-zinc-800 text-zinc-400 cursor-not-allowed'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${msg.quizStatus === 'ready' ? 'bg-indigo-500/20 text-indigo-400' : 'bg-zinc-800 text-zinc-500'}`}>
                            {msg.quizStatus === 'ready' ? <Bot className="w-5 h-5" /> : <Loader2 className="w-5 h-5 animate-spin" />}
                          </div>
                          <div className="text-left">
                            <p className={`text-sm font-semibold m-0 ${msg.quizStatus === 'ready' ? 'text-indigo-200' : 'text-zinc-300'}`}>
                              {msg.response}
                            </p>
                            <p className="text-xs text-zinc-500 m-0 mt-0.5">
                              Module Assessment • {msg.quizModule}
                            </p>
                          </div>
                        </div>
                        {msg.quizStatus === 'ready' && (
                          <div className="text-xs font-medium text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20">
                            Start Quiz →
                          </div>
                        )}
                      </button>
                    )}
                  </div>
                ) : msg.response && (
                   <ReactMarkdown 
                     remarkPlugins={[remarkGfm]}
                     components={markdownComponents}
                   >
                     {msg.response}
                   </ReactMarkdown>
                )}
                
                {isStreaming && idx === chatHistory.length - 1 && (
                  <div className={`flex items-center gap-2 ${msg.response ? 'mt-4 pt-3 border-t border-zinc-800/50' : 'h-5'}`}>
                    <span className="text-[11px] font-medium text-zinc-400">
                      {streamingStatus || (msg.response ? 'Typing...' : 'Thinking...')}
                    </span>
                    <span className="flex items-center gap-1 h-full">
                      <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce"></span>
                      <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{animationDelay: '0.15s'}}></span>
                      <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{animationDelay: '0.3s'}}></span>
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        <div ref={bottomRef} />
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-zinc-950 via-zinc-950 to-transparent pt-10 pointer-events-none">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative group pointer-events-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-5 py-3.5 pr-14 text-sm text-zinc-100 focus:outline-none focus:border-zinc-600 transition-colors shadow-sm"
            disabled={isStreaming}
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="absolute right-2 top-2 bottom-2 aspect-square bg-zinc-100 hover:bg-white disabled:bg-zinc-800 disabled:text-zinc-600 text-zinc-900 rounded-lg flex items-center justify-center transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <div className="text-center mt-3 text-[10px] text-zinc-500 pointer-events-auto">
          AI Tutor can make mistakes. Please verify important information.
        </div>
      </div>

      {selectedImage && (
        <div 
          className="fixed inset-0 z-[100] bg-black/80 flex items-center justify-center p-4 cursor-zoom-out animate-in fade-in duration-200"
          onClick={() => setSelectedImage(null)}
        >
          <img 
            src={selectedImage} 
            alt="Enlarged" 
            className="max-w-full max-h-[90vh] rounded-lg object-contain bg-zinc-900/50" 
          />
        </div>
      )}
    </div>
  );
}
