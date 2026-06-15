import { useState, useEffect } from 'react';
import { useAppStore } from '../store/store';
import { Plus, BookOpen, Layers, ArrowLeft, Database, Cloud } from 'lucide-react';

interface SidebarProps {
  onNewChat: () => void;
}

export default function Sidebar({ onNewChat }: SidebarProps) {
  const { user, activePath, setActivePath, modelMode, setModelMode } = useAppStore();
  const [paths, setPaths] = useState<any[]>([]);
  const [activePathDetails, setActivePathDetails] = useState<any>(null);

  useEffect(() => {
    if (user && !activePath) {
      fetchPaths();
    }
  }, [user, activePath]);

  useEffect(() => {
    if (activePath) {
      fetchPathDetails(activePath);
    }
  }, [activePath]);

  useEffect(() => {
    const handlePathUpdated = () => {
      if (activePath) fetchPathDetails(activePath);
    };
    window.addEventListener('path_updated', handlePathUpdated);
    return () => window.removeEventListener('path_updated', handlePathUpdated);
  }, [activePath, user]);

  const fetchPaths = async () => {
    try {
      const res = await fetch(`/api/paths?user_id=${user?.user_id}`);
      const data = await res.json();
      if (Array.isArray(data)) setPaths(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchPathDetails = async (sessionId: string) => {
    try {
      const res = await fetch(`/api/paths/${sessionId}?user_id=${user?.user_id}`);
      const data = await res.json();
      setActivePathDetails(data);
    } catch (err) {
      console.error(err);
    }
  };

  const toggleModel = async (newMode: 'local' | 'online') => {
    if (modelMode === newMode) return;
    try {
      await fetch('/api/chat/settings/model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode })
      });
      setModelMode(newMode);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <aside className="w-80 bg-zinc-950 border-r border-zinc-800 flex flex-col transition-all h-full shrink-0">
      <div className="h-16 px-4 border-b border-zinc-800 flex items-center justify-between shrink-0">
        <h2 className="font-semibold text-base text-zinc-100 tracking-tight">
          AI Tutor
        </h2>
        {activePath && (
          <button 
            onClick={() => setActivePath(null)}
            className="p-1.5 hover:bg-zinc-900 rounded-md text-zinc-400 hover:text-zinc-100 transition-colors"
            title="Back to Paths"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        {!activePath ? (
          <div className="space-y-4">
            <button 
              onClick={onNewChat}
              className="w-full py-2 px-4 bg-zinc-100 hover:bg-white text-zinc-900 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" /> New Learning Path
            </button>
            
            <div className="mt-8">
              <h3 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-3">Your Paths</h3>
              <div className="space-y-1">
                {paths.length === 0 ? (
                  <p className="text-xs text-zinc-500 text-center py-4">No active paths yet.</p>
                ) : (
                  paths.map(path => (
                    <button
                      key={path.session_id}
                      onClick={() => setActivePath(path.session_id)}
                      className="w-full text-left p-2.5 rounded-lg hover:bg-zinc-900 transition-colors group flex items-center gap-3"
                    >
                      <div className="text-zinc-500 group-hover:text-zinc-300 transition-colors">
                        <BookOpen className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-zinc-300 group-hover:text-zinc-100 transition-colors">
                          {path.title}
                        </div>
                        <div className="text-[11px] text-zinc-500 mt-0.5 capitalize">
                          {path.subject}
                        </div>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6 animate-in fade-in slide-in-from-left-2 duration-200">
            {activePathDetails ? (() => {
              let syllabusList = null;
              if (Array.isArray(activePathDetails.syllabus)) {
                syllabusList = activePathDetails.syllabus;
              } else if (activePathDetails.syllabus?.syllabus) {
                syllabusList = activePathDetails.syllabus.syllabus;
              } else if (activePathDetails.syllabus?.modules) {
                syllabusList = activePathDetails.syllabus.modules.map((m: any) => ({
                  module: m.title,
                  completed: m.completed,
                  completed_topics: m.completed_topics || [],
                  subtopics: m.topics,
                  status: m.status || 'pending'
                }));
              }
              
              let totalTopics = 0;
              let completedTopics = 0;
              
              if (syllabusList) {
                syllabusList.forEach((m: any) => {
                  if (m.subtopics && m.subtopics.length > 0) {
                    m.subtopics.forEach((t: any) => {
                      totalTopics++;
                      if (typeof t === 'string' && m.completed_topics?.includes(t)) {
                        completedTopics++;
                      } else if (t.completed) {
                        completedTopics++;
                      }
                    });
                  } else {
                     totalTopics++;
                     if (m.status === 'completed' || m.status === 'done' || m.completed) completedTopics++;
                  }
                });
              }
              
              let progressPercent = totalTopics === 0 ? 0 : Math.round((completedTopics / totalTopics) * 100);

              return (
                <>
                  <div>
                    <h3 className="text-base font-semibold text-zinc-100 mb-1">{activePathDetails.path?.title || 'Loading...'}</h3>
                    <div className="flex items-center gap-1.5 text-[11px] font-medium text-zinc-400">
                      <Layers className="w-3 h-3" /> <span className="capitalize">{activePathDetails.profile?.level || 'Beginner'}</span>
                    </div>
                  </div>

                  <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-[11px] font-medium text-zinc-400">Progress</span>
                      <span className="text-[11px] font-medium text-zinc-100">{progressPercent}%</span>
                    </div>
                    <div className="w-full bg-zinc-950 rounded-full h-1.5 overflow-hidden border border-zinc-800">
                      <div className="bg-zinc-100 h-full rounded-full transition-all duration-500" style={{ width: `${progressPercent}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-3">Syllabus</h4>
                    <div className="pl-3">
                      {syllabusList && syllabusList.length > 0 ? (
                        syllabusList.map((item: any, idx: number) => {
                          const isCompleted = item.completed || item.status === 'completed' || item.status === 'done';
                          const isOngoing = item.status === 'ongoing' || item.status === 'in-progress' || item.status === 'started';
                          const isLast = idx === syllabusList.length - 1;
                          
                          return (
                            <div key={idx} className="text-sm text-zinc-300 relative pb-5">
                              {/* Vertical connecting line */}
                              {!isLast && (
                                <div className={`absolute left-[-10px] top-2 bottom-[-8px] ${isCompleted ? 'w-[2px] bg-zinc-300' : 'w-px bg-zinc-800'}`}></div>
                              )}
                              
                              {/* Module Dot */}
                              <div className={`absolute w-1.5 h-1.5 rounded-full -left-[12px] top-1.5 ring-4 ring-zinc-950 z-10 ${isCompleted ? 'bg-zinc-300' : isOngoing ? 'bg-zinc-100 shadow-[0_0_8px_rgba(255,255,255,0.3)]' : 'bg-zinc-700'}`}></div>
                              
                              <span className={`font-medium ${isCompleted ? 'text-zinc-300' : isOngoing ? 'text-zinc-100' : 'text-zinc-500'}`}>
                                {item.module || item.title || 'Module'}
                              </span>
                              
                              {item.subtopics && item.subtopics.length > 0 && (
                                <ul className={`text-xs mt-1.5 list-disc ml-4 space-y-1 ${isOngoing ? 'text-zinc-400' : 'text-zinc-500'}`}>
                                  {item.subtopics.map((topic: any, tIdx: number) => {
                                    const topicTitle = typeof topic === 'string' ? topic : topic.title || 'Topic';
                                    const topicCompleted = typeof topic === 'string' ? item.completed_topics?.includes(topic) : topic.completed;
                                    const topicTaught = typeof topic === 'object' && topic.taught;
                                    
                                    return (
                                      <li key={tIdx} className={topicCompleted ? 'text-emerald-400 font-medium' : topicTaught ? 'text-amber-400 font-medium' : (!isOngoing && !isCompleted ? 'opacity-50' : '')}>
                                        {topicTitle} {topicCompleted ? ' ✓' : topicTaught ? ' (Quiz Pending)' : ''}
                                      </li>
                                    );
                                  })}
                                </ul>
                              )}
                            </div>
                          );
                        })
                      ) : (
                        <p className="text-xs text-zinc-500">No syllabus available.</p>
                      )}
                    </div>
                  </div>
                </>
              );
            })() : (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-zinc-500"></div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="p-4 border-t border-zinc-800 bg-zinc-950">
        <div className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-2">Model Selection</div>
        <div className="flex bg-zinc-900 p-0.5 rounded-md border border-zinc-800">
          <button 
            onClick={() => toggleModel('local')}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-[4px] text-xs font-medium transition-colors ${modelMode === 'local' ? 'bg-zinc-800 text-zinc-100 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <Database className="w-3.5 h-3.5" />
            Local
          </button>
          <button 
            onClick={() => toggleModel('online')}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-[4px] text-xs font-medium transition-colors ${modelMode === 'online' ? 'bg-zinc-800 text-zinc-100 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <Cloud className="w-3.5 h-3.5" />
            Online
          </button>
        </div>
      </div>
    </aside>
  );
}
