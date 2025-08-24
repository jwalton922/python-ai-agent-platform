import React, { useState } from 'react';
import { AgentBuilder } from './components/AgentBuilder';
import { WorkflowEditor } from './components/WorkflowEditor';
import { ActivityMonitor } from './components/ActivityMonitor';
import { AgentChat } from './components/AgentChat';
import { Navigation } from './components/Navigation';

// Import test utility in development
if (process.env.NODE_ENV === 'development') {
  import('./utils/testApiConfig');
}

type View = 'agents' | 'workflows' | 'activity' | 'chat';

function App() {
  const [currentView, setCurrentView] = useState<View>('chat');

  const renderView = () => {
    switch (currentView) {
      case 'agents':
        return <AgentBuilder />;
      case 'workflows':
        return <WorkflowEditor />;
      case 'chat':
        return <AgentChat />;
      case 'activity':
        return <ActivityMonitor />;
      default:
        return <AgentChat />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <Navigation currentView={currentView} onViewChange={setCurrentView} />
      <main className="flex-1 container mx-auto py-6 h-full">
        <div className="h-full bg-white rounded-lg shadow-lg overflow-hidden">
          {renderView()}
        </div>
      </main>
    </div>
  );
}

export default App;