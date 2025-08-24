import React, { useState } from 'react';
import { AgentBuilder } from './components/AgentBuilder';
import { WorkflowEditor } from './components/WorkflowEditor';
import { ActivityMonitor } from './components/ActivityMonitor';
import { Navigation } from './components/Navigation';

type View = 'agents' | 'workflows' | 'activity';

function App() {
  const [currentView, setCurrentView] = useState<View>('workflows');

  const renderView = () => {
    switch (currentView) {
      case 'agents':
        return <AgentBuilder />;
      case 'workflows':
        return <WorkflowEditor />;
      case 'activity':
        return <ActivityMonitor />;
      default:
        return <WorkflowEditor />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Navigation currentView={currentView} onViewChange={setCurrentView} />
      <main className="container mx-auto py-6">
        {renderView()}
      </main>
    </div>
  );
}

export default App;