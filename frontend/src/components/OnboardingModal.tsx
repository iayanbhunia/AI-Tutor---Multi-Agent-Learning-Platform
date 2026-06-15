import { useState, useEffect } from 'react';
import { useAppStore } from '../store/store';
import { X, Bot, ArrowRight, CheckCircle2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface OnboardingModalProps {
  onClose: () => void;
}

export default function OnboardingModal({ onClose }: OnboardingModalProps) {
  const { user, setActivePath } = useAppStore();
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [finalSyllabus, setFinalSyllabus] = useState<any>(null);
  const [subject, setSubject] = useState('');
  const [title, setTitle] = useState('');

  useEffect(() => {
    startOnboarding();
  }, []);

  const startOnboarding = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/paths/onboarding/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user?.user_id })
      });
      const data = await res.json();
      setMessages([{ agent: 'ai_tutor', text: data.question || data.response, options: data.options }]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e?: React.FormEvent, overrideText?: string) => {
    if (e) e.preventDefault();
    const userText = overrideText || input;
    if (!userText.trim() || loading) return;

    setMessages(prev => [...prev, { agent: 'user', text: userText }]);
    if (!overrideText) setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/paths/onboarding/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user?.user_id, answer: userText, history: messages })
      });
      const data = await res.json();
      
      if (data.syllabus) {
        setFinalSyllabus(data.syllabus);
        setSubject(data.subject || 'general');
        setTitle(data.title || 'New Learning Path');
        setMessages(prev => [...prev, { agent: 'ai_tutor', text: "Great! I've created a syllabus for you. Review it and click Create Path to begin." }]);
      } else {
        setMessages(prev => [...prev, { agent: 'ai_tutor', text: data.question || data.response, options: data.options }]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePath = async () => {
    setLoading(true);
    try {
      const sessionId = `path_${Date.now()}`;
      const res = await fetch('/api/paths/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user?.user_id,
          session_id: sessionId,
          subject,
          title,
          syllabus: JSON.stringify(finalSyllabus)
        })
      });
      
      if (res.ok) {
        setActivePath(sessionId);
        onClose();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-zinc-950 border border-zinc-800 rounded-xl flex flex-col max-h-[85vh] overflow-hidden shadow-2xl">
        <div className="px-5 py-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-950">
          <div className="flex items-center gap-3">
            <div className="p-1.5 border border-zinc-800 text-zinc-300 rounded-md">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-zinc-100">Path Setup Wizard</h2>
              <p className="text-[11px] text-zinc-500">Personalize your learning journey</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-zinc-500 hover:text-zinc-100 hover:bg-zinc-900 rounded-md transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-zinc-950">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 ${msg.agent === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`max-w-[85%] rounded-xl p-4 ${msg.agent === 'user' ? 'bg-zinc-800 text-zinc-100' : 'bg-zinc-900 border border-zinc-800 text-zinc-200'}`}>
                <div className="prose prose-invert prose-sm prose-zinc">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              </div>
            </div>
          ))}
          {loading && !finalSyllabus && (
             <div className="flex gap-4">
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 w-16 flex justify-center items-center h-12">
                   <span className="flex items-center gap-1">
                     <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce"></span>
                     <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{animationDelay: '0.15s'}}></span>
                     <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{animationDelay: '0.3s'}}></span>
                   </span>
                </div>
             </div>
          )}

          {finalSyllabus && (
            <div className="mt-6 bg-zinc-950 border border-zinc-800 rounded-xl p-5 animate-in slide-in-from-bottom-4 shadow-xl">
              <h3 className="text-emerald-400 text-base font-semibold flex items-center gap-2 mb-4 pb-3 border-b border-zinc-800/50">
                <CheckCircle2 className="w-5 h-5" /> Syllabus Generated Successfully!
              </h3>
              
              <div className="space-y-4 max-h-[40vh] overflow-y-auto pr-2 custom-scrollbar">
                {finalSyllabus.modules?.map((mod: any, i: number) => (
                  <div key={i} className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-4 shadow-sm">
                    <h4 className="text-zinc-100 text-sm font-semibold mb-3 flex items-start gap-2">
                      <span className="text-indigo-400 text-xs mt-0.5 bg-indigo-500/10 px-1.5 rounded">M{i+1}</span>
                      {mod.title}
                    </h4>
                    <ul className="space-y-2">
                      {mod.topics?.map((topic: any, j: number) => (
                        <li key={j} className="text-xs text-zinc-400 flex items-start gap-2 leading-relaxed">
                          <span className="text-zinc-600 mt-0.5 shrink-0">•</span>
                          {typeof topic === 'string' ? topic : topic.title || 'Unknown Topic'}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-zinc-800 bg-zinc-950">
          {!finalSyllabus ? (
            <div className="space-y-3">
              {messages.length > 0 && messages[messages.length - 1].agent === 'ai_tutor' && messages[messages.length - 1].options && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {messages[messages.length - 1].options.map((opt: string, i: number) => (
                    <button
                      key={i}
                      onClick={() => {
                        setInput(opt);
                        handleSend(undefined, opt);
                      }}
                      disabled={loading}
                      className="px-4 py-2 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 rounded-lg text-sm transition-colors text-left disabled:opacity-50"
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              )}
              <form onSubmit={(e) => handleSend(e)} className="relative">
                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  disabled={loading}
                  placeholder="Type your answer..."
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 pr-12 text-sm text-zinc-100 focus:outline-none focus:border-indigo-500 transition-colors disabled:opacity-50"
                />
                <button 
                  type="submit"
                  disabled={!input.trim() || loading}
                  className="absolute right-1.5 top-1.5 bottom-1.5 aspect-square bg-indigo-600 hover:bg-indigo-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-md flex items-center justify-center transition-colors"
                >
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>
            </div>
          ) : (
            <button 
              onClick={handleCreatePath}
              disabled={loading}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm rounded-lg transition-colors shadow-[0_0_15px_rgba(99,102,241,0.2)]"
            >
              {loading ? 'Creating...' : 'Create Path & Start Learning'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
