import axios from 'axios';
import { Agent, Workflow, Activity, MCPTool } from '../types';

const API_BASE = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Agent API
export const listAgents = async (): Promise<Agent[]> => {
  const response = await api.get('/agents/');
  return response.data;
};

export const getAgent = async (id: string): Promise<Agent> => {
  const response = await api.get(`/agents/${id}`);
  return response.data;
};

export const createAgent = async (agentData: Partial<Agent>): Promise<Agent> => {
  const response = await api.post('/agents/', agentData);
  return response.data;
};

export const updateAgent = async (id: string, agentData: Partial<Agent>): Promise<Agent> => {
  const response = await api.put(`/agents/${id}`, agentData);
  return response.data;
};

export const deleteAgent = async (id: string): Promise<void> => {
  await api.delete(`/agents/${id}`);
};

// Workflow API
export const listWorkflows = async (): Promise<Workflow[]> => {
  const response = await api.get('/workflows/');
  return response.data;
};

export const getWorkflow = async (id: string): Promise<Workflow> => {
  const response = await api.get(`/workflows/${id}`);
  return response.data;
};

export const createWorkflow = async (workflowData: Partial<Workflow>): Promise<Workflow> => {
  const response = await api.post('/workflows/', workflowData);
  return response.data;
};

export const updateWorkflow = async (id: string, workflowData: Partial<Workflow>): Promise<Workflow> => {
  const response = await api.put(`/workflows/${id}`, workflowData);
  return response.data;
};

export const deleteWorkflow = async (id: string): Promise<void> => {
  await api.delete(`/workflows/${id}`);
};

export const executeWorkflow = async (id: string, context: Record<string, any>): Promise<any> => {
  const response = await api.post(`/workflows/${id}/execute`, context);
  return response.data;
};

export const getWorkflowStatus = async (id: string): Promise<any> => {
  const response = await api.get(`/workflows/${id}/status`);
  return response.data;
};

// Activity API
export const listActivities = async (limit = 100, offset = 0): Promise<Activity[]> => {
  const response = await api.get('/activities/', { params: { limit, offset } });
  return response.data;
};

export const createActivity = async (activityData: Partial<Activity>): Promise<Activity> => {
  const response = await api.post('/activities/', activityData);
  return response.data;
};

// MCP Tool API
export const listMCPTools = async (): Promise<MCPTool[]> => {
  const response = await api.get('/mcp-tools/');
  return response.data;
};

export const getToolSchema = async (toolId: string): Promise<any> => {
  const response = await api.get(`/mcp-tools/${toolId}/schema`);
  return response.data;
};

export const executeToolAction = async (
  toolId: string, 
  params: Record<string, any>,
  agentId?: string,
  workflowId?: string
): Promise<any> => {
  const response = await api.post(`/mcp-tools/${toolId}/action`, params, {
    params: { agent_id: agentId, workflow_id: workflowId }
  });
  return response.data;
};

// Chat API
export const chatWithAgent = async (
  agentId: string,
  message: string,
  chatHistory: Array<{ role: string; content: string }> = []
): Promise<{
  message: string;
  tool_calls: any[];
  success: boolean;
  error?: string;
}> => {
  const response = await api.post('/chat/', {
    agent_id: agentId,
    message: message,
    chat_history: chatHistory
  });
  return response.data;
};

// Health check
export const healthCheck = async (): Promise<{ status: string }> => {
  const response = await api.get('/health');
  return response.data;
};