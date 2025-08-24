import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Bot } from 'lucide-react';
import * as api from '../services/api';
import { Agent, MCPTool } from '../types';

export const AgentBuilder: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [mcpTools, setMcpTools] = useState<MCPTool[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);

  useEffect(() => {
    loadAgents();
    loadMCPTools();
  }, []);

  const loadAgents = async () => {
    try {
      const agentList = await api.listAgents();
      setAgents(agentList);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const loadMCPTools = async () => {
    try {
      const toolList = await api.listMCPTools();
      setMcpTools(toolList);
    } catch (error) {
      console.error('Failed to load MCP tools:', error);
    }
  };

  const handleCreateAgent = () => {
    setIsCreating(true);
    setEditingAgent(null);
  };

  const handleEditAgent = (agent: Agent) => {
    setEditingAgent(agent);
    setIsCreating(false);
  };

  const handleDeleteAgent = async (agentId: string) => {
    if (window.confirm('Are you sure you want to delete this agent?')) {
      try {
        await api.deleteAgent(agentId);
        setAgents(prev => prev.filter(a => a.id !== agentId));
      } catch (error) {
        console.error('Failed to delete agent:', error);
        alert('Failed to delete agent');
      }
    }
  };

  const handleSaveAgent = async (agentData: Partial<Agent>) => {
    try {
      if (editingAgent) {
        const updated = await api.updateAgent(editingAgent.id, agentData);
        setAgents(prev => prev.map(a => a.id === updated.id ? updated : a));
      } else {
        const created = await api.createAgent(agentData);
        setAgents(prev => [...prev, created]);
      }
      setIsCreating(false);
      setEditingAgent(null);
    } catch (error) {
      console.error('Failed to save agent:', error);
      alert('Failed to save agent');
    }
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingAgent(null);
  };

  if (isCreating || editingAgent) {
    return (
      <AgentForm
        agent={editingAgent}
        mcpTools={mcpTools}
        onSave={handleSaveAgent}
        onCancel={handleCancel}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">AI Agents</h1>
        <button
          onClick={handleCreateAgent}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={20} />
          <span>Create Agent</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="bg-white rounded-lg shadow-md border border-gray-200 p-6"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Bot className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {agent.name}
                  </h3>
                  {agent.description && (
                    <p className="text-sm text-gray-600">{agent.description}</p>
                  )}
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleEditAgent(agent)}
                  className="text-gray-500 hover:text-blue-600 transition-colors"
                >
                  <Edit size={18} />
                </button>
                <button
                  onClick={() => handleDeleteAgent(agent.id)}
                  className="text-gray-500 hover:text-red-600 transition-colors"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Instructions:</p>
                <p className="text-sm text-gray-600 line-clamp-3">
                  {agent.instructions}
                </p>
              </div>

              {agent.mcp_tool_permissions.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Tools:</p>
                  <div className="flex flex-wrap gap-1">
                    {agent.mcp_tool_permissions.map((toolId) => (
                      <span
                        key={toolId}
                        className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {toolId.replace('_tool', '')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="text-xs text-gray-500">
                Created: {new Date(agent.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>
        ))}
      </div>

      {agents.length === 0 && (
        <div className="text-center py-12">
          <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No agents yet</h3>
          <p className="text-gray-600 mb-4">Create your first AI agent to get started.</p>
          <button
            onClick={handleCreateAgent}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create Your First Agent
          </button>
        </div>
      )}
    </div>
  );
};

interface AgentFormProps {
  agent: Agent | null;
  mcpTools: MCPTool[];
  onSave: (agentData: Partial<Agent>) => void;
  onCancel: () => void;
}

const AgentForm: React.FC<AgentFormProps> = ({ agent, mcpTools, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    name: agent?.name || '',
    description: agent?.description || '',
    instructions: agent?.instructions || '',
    mcp_tool_permissions: agent?.mcp_tool_permissions || [],
    trigger_conditions: agent?.trigger_conditions || ['manual']
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.instructions) {
      alert('Name and instructions are required');
      return;
    }
    onSave(formData);
  };

  const handleToolToggle = (toolId: string) => {
    setFormData(prev => ({
      ...prev,
      mcp_tool_permissions: prev.mcp_tool_permissions.includes(toolId)
        ? prev.mcp_tool_permissions.filter(id => id !== toolId)
        : [...prev.mcp_tool_permissions, toolId]
    }));
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        {agent ? 'Edit Agent' : 'Create New Agent'}
      </h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Agent Name *
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Email Assistant"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <input
            type="text"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Brief description of the agent's purpose"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Instructions *
          </label>
          <textarea
            value={formData.instructions}
            onChange={(e) => setFormData(prev => ({ ...prev, instructions: e.target.value }))}
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Detailed instructions for the AI agent..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Available Tools
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {mcpTools.map((tool) => (
              <label
                key={tool.id}
                className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50"
              >
                <input
                  type="checkbox"
                  checked={formData.mcp_tool_permissions.includes(tool.id)}
                  onChange={() => handleToolToggle(tool.id)}
                  className="rounded border-gray-300"
                />
                <div>
                  <div className="font-medium text-sm">{tool.name}</div>
                  <div className="text-xs text-gray-600">{tool.schema.description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="flex space-x-4 pt-6">
          <button
            type="submit"
            className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {agent ? 'Update Agent' : 'Create Agent'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};