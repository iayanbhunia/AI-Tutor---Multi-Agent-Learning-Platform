import { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../store/store';
import { User as UserIcon, LogOut, ChevronDown } from 'lucide-react';

export default function UserProfile() {
  const { user, setUser, setActivePath } = useAppStore();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    setUser(null);
    setActivePath(null);
  };

  if (!user) return null;

  return (
    <div className="relative z-30" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 p-1.5 pr-3 rounded-full transition-colors shadow-sm"
      >
        <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center shrink-0">
          <UserIcon className="w-4 h-4 text-zinc-300" />
        </div>
        <span className="text-sm font-medium text-zinc-200 max-w-[100px] truncate text-left">{user.name || 'Guest'}</span>
        <ChevronDown className={`w-4 h-4 text-zinc-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="p-4 border-b border-zinc-800 bg-zinc-950">
            <p className="text-sm font-semibold text-zinc-100 truncate">{user.name || 'Guest'}</p>
            <p className="text-[11px] text-zinc-500 font-mono mt-0.5 truncate flex items-center gap-1.5">
               <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
               {user.user_id}
            </p>
          </div>
          <div className="p-1.5">
            <button 
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-500/10 hover:text-red-300 rounded-md transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
