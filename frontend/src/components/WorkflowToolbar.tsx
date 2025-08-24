import React from 'react';
import { Plus, Save, Play, FolderOpen } from 'lucide-react';
import { Agent, Workflow } from '../types';

interface WorkflowToolbarProps {
  agents: Agent[];
  workflows: Workflow[];
  currentWorkflow: Workflow | null;
  onAddNode: (agentId: string) => void;
  onSave: () => void;
  onExecute: () => void;
  onLoadWorkflow: (workflow: Workflow) => void;
  isExecuting: boolean;
}

export const WorkflowToolbar: React.FC<WorkflowToolbarProps> = ({
  agents,
  workflows,
  currentWorkflow,
  onAddNode,
  onSave,
  onExecute,
  onLoadWorkflow,
  isExecuting
}) => {
  return (
    <div className="bg-white border-b border-gray-200 p-4">
      <div className="flex flex-wrap items-center gap-4">
        {/* Current workflow info */}
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium">Workflow:</span>
          <span className="text-sm text-gray-600">
            {currentWorkflow?.name || 'Untitled'}
          </span>
        </div>

        {/* Agent dropdown */}
        <div className="flex items-center space-x-2">
          <Plus size={16} className="text-gray-500" />
          <select
            onChange={(e) => e.target.value && onAddNode(e.target.value)}
            value=""
            className="text-sm border border-gray-300 rounded px-3 py-1 focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Add Agent Node</option>
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </div>

        {/* Load workflow dropdown */}
        <div className="flex items-center space-x-2">
          <FolderOpen size={16} className="text-gray-500" />
          <select
            onChange={(e) => {
              const workflow = workflows.find(w => w.id === e.target.value);
              if (workflow) onLoadWorkflow(workflow);
            }}
            value=""
            className="text-sm border border-gray-300 rounded px-3 py-1 focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Load Workflow</option>
            {workflows.map((workflow) => (
              <option key={workflow.id} value={workflow.id}>
                {workflow.name}
              </option>
            ))}
          </select>
        </div>

        {/* Action buttons */}
        <div className="flex items-center space-x-2 ml-auto">
          <button
            onClick={onSave}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
          >
            <Save size={16} />
            <span>Save</span>
          </button>

          <button
            onClick={onExecute}
            disabled={isExecuting}
            className="flex items-center space-x-2 px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 transition-colors text-sm"
          >
            <Play size={16} />
            <span>{isExecuting ? 'Executing...' : 'Execute'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};