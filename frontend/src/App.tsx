import { useAppStore } from './store/store';
import AuthView from './components/AuthView';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import OnboardingModal from './components/OnboardingModal';
import QuizOverlay from './components/QuizOverlay';
import UserProfile from './components/UserProfile';
import { useState } from 'react';

function App() {
  const user = useAppStore(state => state.user);
  const [showOnboarding, setShowOnboarding] = useState(false);

  if (!user) {
    return <AuthView />;
  }

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden">
      <Sidebar onNewChat={() => setShowOnboarding(true)} />
      
      <main className="flex-1 flex flex-col relative bg-zinc-950">
        <header className="h-16 border-b border-zinc-800 flex items-center justify-end px-6 shrink-0 z-20">
          <UserProfile />
        </header>
        <ChatInterface />
        <QuizOverlay />
      </main>

      {showOnboarding && (
        <OnboardingModal onClose={() => setShowOnboarding(false)} />
      )}
    </div>
  );
}

export default App;
