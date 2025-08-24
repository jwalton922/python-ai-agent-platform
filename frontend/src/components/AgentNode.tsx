import React from 'react';
import { Handle, Position } from 'reactflow';
import { Bot, Trash2 } from 'lucide-react';
import { Agent } from '../types';

interface AgentNodeProps {
  data: {
    agent: Agent;
    onDelete: (nodeId: string) => void;
  };
  id: string;
}

export const AgentNode: React.FC<AgentNodeProps> = ({ data, id }) => {
  if (!data.agent) {
    return (
      <div className="bg-red-100 border-2 border-red-300 rounded-lg p-3 min-w-[200px]">
        <div className="text-red-600">Agent not found</div>
      </div>
    );
  }

  return (
    <div className="bg-white border-2 border-blue-300 rounded-lg p-3 min-w-[200px] shadow-lg">
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Bot size={16} className="text-blue-600" />
          <span className="font-medium text-sm">{data.agent.name}</span>
        </div>
        
        <button
          onClick={() => data.onDelete(id)}
          className="text-red-500 hover:text-red-700 transition-colors"
          title="Delete node"
        >
          <Trash2 size={14} />
        </button>
      </div>
      
      {data.agent.description && (
        <div className="text-xs text-gray-600 mb-2">
          {data.agent.description}
        </div>
      )}
      
      <div className="text-xs text-gray-500 truncate">
        {data.agent.instructions.slice(0, 50)}...
      </div>
      
      {data.agent.mcp_tool_permissions.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {data.agent.mcp_tool_permissions.slice(0, 2).map((tool) => (
            <span
              key={tool}
              className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded"
            >
              {tool.replace('_tool', '')}
            </span>
          ))}
          {data.agent.mcp_tool_permissions.length > 2 && (
            <span className="text-xs text-gray-500">
              +{data.agent.mcp_tool_permissions.length - 2} more
            </span>
          )}
        </div>
      )}
      
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
};