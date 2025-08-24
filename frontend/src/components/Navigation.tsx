import React from 'react';
import { Bot, Workflow, Activity, MessageCircle } from 'lucide-react';

type View = 'agents' | 'workflows' | 'activity' | 'chat';

interface NavigationProps {
  currentView: View;
  onViewChange: (view: View) => void;
}

export const Navigation: React.FC<NavigationProps> = ({ currentView, onViewChange }) => {
  const navItems = [
    { id: 'agents' as View, label: 'Agents', icon: Bot },
    { id: 'workflows' as View, label: 'Workflows', icon: Workflow },
    { id: 'chat' as View, label: 'Chat', icon: MessageCircle },
    { id: 'activity' as View, label: 'Activity', icon: Activity },
  ];

  return (
    <nav className="bg-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <h1 className="text-xl font-bold text-gray-900">AI Agent Platform</h1>
            
            <div className="flex space-x-4">
              {navItems.map((item) => {
                const IconComponent = item.icon;
                const isActive = currentView === item.id;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => onViewChange(item.id)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <IconComponent size={16} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};