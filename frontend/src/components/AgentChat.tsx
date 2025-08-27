import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader, Wrench, AlertCircle, RefreshCw, Trash2 } from 'lucide-react';
import * as api from '../services/api';
import { Agent } from '../types';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
  error?: string;
  workflowGenerated?: any;
}

interface ToolCall {
  tool: string;
  action: string;
  params?: Record<string, any>;
  result?: any;
  success: boolean;
  error?: string;
}

interface ChatSession {
  agentId: string;
  messages: Message[];
}

export const AgentChat: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [sessions, setSessions] = useState<Record<string, ChatSession>>({});
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [sessions, selectedAgentId]);

  const loadAgents = async () => {
    try {
      const agentList = await api.listAgents();
      setAgents(agentList);
      if (agentList.length > 0 && !selectedAgentId) {
        setSelectedAgentId(agentList[0].id);
      }
    } catch (error) {
      console.error('Failed to load agents:', error);
      setError('Failed to load agents');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const getCurrentSession = (): ChatSession => {
    if (!sessions[selectedAgentId]) {
      return { agentId: selectedAgentId, messages: [] };
    }
    return sessions[selectedAgentId];
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !selectedAgentId || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    // Add user message to session
    const currentSession = getCurrentSession();
    const updatedMessages = [...currentSession.messages, userMessage];
    setSessions({
      ...sessions,
      [selectedAgentId]: { agentId: selectedAgentId, messages: updatedMessages }
    });

    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      // Prepare chat history for API
      const chatHistory = updatedMessages.slice(0, -1).map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      // Send message to API
      const response = await api.chatWithAgent(
        selectedAgentId,
        userMessage.content,
        chatHistory
      );

      if (response.success) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.message,
          timestamp: new Date(),
          toolCalls: response.tool_calls,
          workflowGenerated: response.workflow_generated
        };

        setSessions({
          ...sessions,
          [selectedAgentId]: {
            agentId: selectedAgentId,
            messages: [...updatedMessages, assistantMessage]
          }
        });
      } else {
        throw new Error(response.error || 'Failed to get response');
      }
    } catch (error: any) {
      console.error('Failed to send message:', error);
      
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your message.',
        timestamp: new Date(),
        error: error.message || 'Unknown error occurred'
      };

      setSessions({
        ...sessions,
        [selectedAgentId]: {
          agentId: selectedAgentId,
          messages: [...updatedMessages, errorMessage]
        }
      });
      
      setError(error.message || 'Failed to send message');
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const clearChat = () => {
    if (selectedAgentId) {
      setSessions({
        ...sessions,
        [selectedAgentId]: { agentId: selectedAgentId, messages: [] }
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const selectedAgent = agents.find(a => a.id === selectedAgentId);
  const currentSession = getCurrentSession();

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Bot className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Agent Chat</h2>
          </div>
          
          <div className="flex items-center space-x-3">
            {/* Agent Selector */}
            <select
              value={selectedAgentId}
              onChange={(e) => setSelectedAgentId(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            >
              <option value="">Select an agent...</option>
              {agents.map(agent => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>

            {/* Action Buttons */}
            <button
              onClick={clearChat}
              disabled={currentSession.messages.length === 0}
              className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Clear chat"
            >
              <Trash2 size={18} />
            </button>
            
            <button
              onClick={loadAgents}
              className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              title="Refresh agents"
            >
              <RefreshCw size={18} />
            </button>
          </div>
        </div>

        {/* Agent Info */}
        {selectedAgent && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600">
              <span className="font-medium">Instructions:</span> {selectedAgent.instructions}
            </div>
            {selectedAgent.mcp_tool_permissions.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {selectedAgent.mcp_tool_permissions.map(tool => (
                  <span
                    key={tool}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    <Wrench size={10} className="mr-1" />
                    {tool.replace('_tool', '')}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 chat-scrollbar">
        {!selectedAgentId ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Bot size={48} className="mb-4 text-gray-400" />
            <p className="text-lg font-medium">Select an agent to start chatting</p>
          </div>
        ) : currentSession.messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Bot size={48} className="mb-4 text-gray-400" />
            <p className="text-lg font-medium">No messages yet</p>
            <p className="text-sm mt-2">Send a message to {selectedAgent?.name} to get started</p>
          </div>
        ) : (
          <div className="space-y-4 max-w-4xl mx-auto">
            {currentSession.messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} chat-message-enter`}
              >
                <div
                  className={`flex max-w-[70%] ${
                    message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  }`}
                >
                  {/* Avatar */}
                  <div
                    className={`flex-shrink-0 ${
                      message.role === 'user' ? 'ml-3' : 'mr-3'
                    }`}
                  >
                    <div
                      className={`h-8 w-8 rounded-full flex items-center justify-center ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-600 text-white'
                      }`}
                    >
                      {message.role === 'user' ? (
                        <User size={16} />
                      ) : (
                        <Bot size={16} />
                      )}
                    </div>
                  </div>

                  {/* Message Content */}
                  <div className="flex flex-col">
                    <div
                      className={`px-4 py-2 rounded-lg ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : message.error
                          ? 'bg-red-100 text-red-900 border border-red-200'
                          : 'bg-white text-gray-900 border border-gray-200'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>

                    {/* Error Display */}
                    {message.error && (
                      <div className="mt-2 flex items-start space-x-2 text-sm text-red-600">
                        <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
                        <span>{message.error}</span>
                      </div>
                    )}

                    {/* Tool Calls Display */}
                    {message.toolCalls && message.toolCalls.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {message.toolCalls.map((toolCall, toolIndex) => (
                          <div
                            key={toolIndex}
                            className={`p-3 rounded-lg text-sm ${
                              toolCall.success
                                ? 'bg-green-50 border border-green-200'
                                : 'bg-red-50 border border-red-200'
                            }`}
                          >
                            <div className="flex items-center space-x-2 mb-1">
                              <Wrench size={14} />
                              <span className="font-medium">
                                {toolCall.tool} - {toolCall.action}
                              </span>
                              {toolCall.success ? (
                                <span className="text-green-600 text-xs">✓ Success</span>
                              ) : (
                                <span className="text-red-600 text-xs">✗ Failed</span>
                              )}
                            </div>
                            
                            {toolCall.params && Object.keys(toolCall.params).length > 0 && (
                              <details className="mt-2">
                                <summary className="cursor-pointer text-xs text-gray-600 hover:text-gray-800">
                                  View parameters
                                </summary>
                                <pre className="mt-1 text-xs bg-white p-2 rounded overflow-x-auto">
                                  {JSON.stringify(toolCall.params, null, 2)}
                                </pre>
                              </details>
                            )}
                            
                            {toolCall.result && (
                              <details className="mt-2">
                                <summary className="cursor-pointer text-xs text-gray-600 hover:text-gray-800">
                                  View result
                                </summary>
                                <pre className="mt-1 text-xs bg-white p-2 rounded overflow-x-auto">
                                  {JSON.stringify(toolCall.result, null, 2)}
                                </pre>
                              </details>
                            )}
                            
                            {toolCall.error && (
                              <div className="mt-2 text-xs text-red-600">
                                Error: {toolCall.error}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Generated Workflow Display */}
                    {message.workflowGenerated && (
                      <div className="mt-3 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="text-purple-600">⚡</span>
                            <span className="font-medium text-sm text-purple-900">
                              Workflow Generated: {message.workflowGenerated.name}
                            </span>
                          </div>
                          <button
                            onClick={() => {
                              // Open workflow editor with the generated workflow
                              window.location.href = `/workflow/${message.workflowGenerated.id}`;
                            }}
                            className="text-xs px-2 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
                          >
                            View Workflow
                          </button>
                        </div>
                        {message.workflowGenerated.description && (
                          <p className="text-sm text-gray-700 mb-2">
                            {message.workflowGenerated.description}
                          </p>
                        )}
                        <div className="flex items-center space-x-4 text-xs text-gray-600">
                          <span>{message.workflowGenerated.nodes?.length || 0} nodes</span>
                          <span>{message.workflowGenerated.edges?.length || 0} connections</span>
                          <span>{message.workflowGenerated.variables?.length || 0} variables</span>
                        </div>
                      </div>
                    )}

                    {/* Timestamp */}
                    <div className="mt-1 text-xs text-gray-500">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-center space-x-2 px-4 py-2 bg-gray-100 rounded-lg">
                  <Loader className="animate-spin h-4 w-4 text-gray-600" />
                  <span className="text-sm text-gray-600">Thinking...</span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white border-t px-6 py-4">
        {error && (
          <div className="mb-3 flex items-center space-x-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}
        
        <div className="flex space-x-3">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              selectedAgentId
                ? `Message ${selectedAgent?.name || 'agent'}...`
                : 'Select an agent to start chatting'
            }
            disabled={!selectedAgentId || isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          
          <button
            onClick={sendMessage}
            disabled={!selectedAgentId || !inputMessage.trim() || isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {isLoading ? (
              <Loader className="animate-spin h-5 w-5" />
            ) : (
              <Send size={18} />
            )}
            <span>{isLoading ? 'Sending...' : 'Send'}</span>
          </button>
        </div>

        {/* Example prompts */}
        {selectedAgent && currentSession.messages.length === 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="text-xs text-gray-500">Try:</span>
            {selectedAgent.mcp_tool_permissions.includes('email_tool') && (
              <button
                onClick={() => setInputMessage('Can you help me read my emails?')}
                className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
              >
                📧 Read emails
              </button>
            )}
            {selectedAgent.mcp_tool_permissions.includes('slack_tool') && (
              <button
                onClick={() => setInputMessage('Can you post a message to our team channel?')}
                className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
              >
                💬 Post to Slack
              </button>
            )}
            {selectedAgent.mcp_tool_permissions.includes('file_tool') && (
              <button
                onClick={() => setInputMessage('Can you help me read a file?')}
                className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
              >
                📁 Read file
              </button>
            )}
            <button
              onClick={() => setInputMessage('Hello, how can you help me?')}
              className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
            >
              👋 Say hello
            </button>
            <button
              onClick={() => setInputMessage('Create a workflow that reads emails and sends summaries')}
              className="text-xs px-2 py-1 bg-purple-100 hover:bg-purple-200 rounded-full text-purple-700 transition-colors"
            >
              ⚡ Create workflow
            </button>
          </div>
        )}
      </div>
    </div>
  );
};