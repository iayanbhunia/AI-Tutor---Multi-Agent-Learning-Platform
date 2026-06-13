import { useState } from 'react';
import { useAppStore } from '../store/store';
import { LogIn, UserPlus, Ghost } from 'lucide-react';

export default function AuthView() {
  const setUser = useAppStore(state => state.setUser);
  const [activeTab, setActiveTab] = useState<'login' | 'signup' | 'guest'>('login');
  const [userId, setUserId] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      let endpoint = '';
      let body: any = {};
      
      if (activeTab === 'login') {
        endpoint = '/api/auth/login';
        body = { user_id: userId };
      } else if (activeTab === 'signup') {
        endpoint = '/api/auth/signup';
        body = { user_id: userId, name };
      } else {
        endpoint = '/api/auth/guest';
      }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await res.json();
      if (!res.ok || data.error) {
        throw new Error(data.error || 'Authentication failed');
      }

      setUser(data.user || data);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm p-8 bg-zinc-950 border border-zinc-800 rounded-xl">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-semibold text-zinc-100">
            AI Tutor
          </h1>
          <p className="text-sm text-zinc-400 mt-2">Sign in to continue</p>
        </div>

        <div className="flex gap-1 mb-6 bg-zinc-900 p-1 rounded-lg border border-zinc-800">
          <button 
            onClick={() => setActiveTab('login')}
            className={`flex-1 py-1.5 px-3 rounded-md text-xs font-medium transition-colors ${activeTab === 'login' ? 'bg-zinc-800 text-zinc-100 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <LogIn className="w-3.5 h-3.5 inline-block mr-1.5" /> Login
          </button>
          <button 
            onClick={() => setActiveTab('signup')}
            className={`flex-1 py-1.5 px-3 rounded-md text-xs font-medium transition-colors ${activeTab === 'signup' ? 'bg-zinc-800 text-zinc-100 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <UserPlus className="w-3.5 h-3.5 inline-block mr-1.5" /> Sign Up
          </button>
          <button 
            onClick={() => setActiveTab('guest')}
            className={`flex-1 py-1.5 px-3 rounded-md text-xs font-medium transition-colors ${activeTab === 'guest' ? 'bg-zinc-800 text-zinc-100 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <Ghost className="w-3.5 h-3.5 inline-block mr-1.5" /> Guest
          </button>
        </div>

        <form onSubmit={handleAuth} className="space-y-4">
          {activeTab !== 'guest' && (
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5">User ID</label>
              <input 
                type="text" 
                required 
                value={userId}
                onChange={e => setUserId(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-zinc-600 transition-colors"
                placeholder="Enter your ID"
              />
            </div>
          )}
          
          {activeTab === 'signup' && (
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5">Full Name</label>
              <input 
                type="text" 
                required 
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-zinc-600 transition-colors"
                placeholder="Jane Doe"
              />
            </div>
          )}

          {error && <p className="text-red-400 text-xs mt-2">{error}</p>}

          <button 
            type="submit" 
            className="w-full mt-6 bg-zinc-100 hover:bg-white text-zinc-900 font-medium text-sm py-2.5 rounded-lg transition-colors"
          >
            {activeTab === 'login' ? 'Sign In' : activeTab === 'signup' ? 'Create Account' : 'Continue as Guest'}
          </button>
        </form>
      </div>
    </div>
  );
}
