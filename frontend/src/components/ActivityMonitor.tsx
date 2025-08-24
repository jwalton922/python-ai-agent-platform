import React, { useState, useEffect } from 'react';
import { Activity as ActivityIcon, Bot, Workflow, Wrench, CheckCircle, XCircle, Clock } from 'lucide-react';
import * as api from '../services/api';
import { Activity } from '../types';

export const ActivityMonitor: React.FC = () => {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadActivities();
    
    // Set up SSE for real-time updates
    const eventSource = new EventSource('/api/activities/stream');
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type !== 'heartbeat') {
        // Add new activity to the list
        setActivities(prev => [data, ...prev].slice(0, 100)); // Keep only latest 100
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      eventSource.close();
      // Fallback to polling
      const interval = setInterval(loadActivities, 5000);
      return () => clearInterval(interval);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  const loadActivities = async () => {
    try {
      const activityList = await api.listActivities(100);
      setActivities(activityList);
    } catch (error) {
      console.error('Failed to load activities:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getActivityIcon = (activity: Activity) => {
    switch (activity.type) {
      case 'agent_execution':
        return <Bot size={16} className={activity.success ? 'text-green-600' : 'text-red-600'} />;
      case 'tool_invocation':
        return <Wrench size={16} className={activity.success ? 'text-blue-600' : 'text-red-600'} />;
      case 'workflow_start':
      case 'workflow_complete':
      case 'workflow_failed':
        return <Workflow size={16} className={activity.success ? 'text-purple-600' : 'text-red-600'} />;
      default:
        return <ActivityIcon size={16} className="text-gray-600" />;
    }
  };

  const getStatusIcon = (activity: Activity) => {
    if (activity.success) {
      return <CheckCircle size={14} className="text-green-500" />;
    } else {
      return <XCircle size={14} className="text-red-500" />;
    }
  };

  const renderToolInputParams = (activity: Activity) => {
    if (activity.type !== 'tool_invocation') return null;
    
    const inputParams = activity.data?.all_input_params || activity.data?.params;
    if (!inputParams || Object.keys(inputParams).length === 0) return null;

    return (
      <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
        <h4 className="text-sm font-medium text-blue-900 mb-2">🔧 MCP Tool Input Parameters</h4>
        <div className="space-y-2">
          {Object.entries(inputParams).map(([key, value]) => (
            <div key={key} className="flex flex-col">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-blue-800 bg-blue-100 px-2 py-1 rounded">
                  {key}
                </span>
                <span className="text-xs text-blue-600">
                  {typeof value} ({String(value).length} chars)
                </span>
              </div>
              <div className="mt-1 text-xs text-blue-700 bg-white p-2 rounded border">
                {typeof value === 'object' ? (
                  <pre className="overflow-x-auto">{JSON.stringify(value, null, 2)}</pre>
                ) : (
                  <span className="break-all">{String(value)}</span>
                )}
              </div>
            </div>
          ))}
        </div>
        
        {activity.data?.input_params_detailed && (
          <div className="mt-2 pt-2 border-t border-blue-200">
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {activity.data.input_params_detailed.param_count} parameters
              </span>
              {activity.data.input_params_detailed.has_sensitive_data && (
                <span className="bg-red-100 text-red-800 px-2 py-1 rounded">
                  ⚠️ Contains sensitive data
                </span>
              )}
              {activity.data.action && (
                <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                  Action: {activity.data.action}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderToolResult = (activity: Activity) => {
    if (activity.type !== 'tool_invocation') return null;
    
    const result = activity.data?.execution_result || activity.data?.result;
    if (!result) return null;

    return (
      <div className="mt-3 bg-green-50 border border-green-200 rounded-lg p-3">
        <h4 className="text-sm font-medium text-green-900 mb-2">📤 Tool Execution Result</h4>
        <div className="text-xs text-green-700 bg-white p-2 rounded border">
          {typeof result === 'object' ? (
            <pre className="overflow-x-auto">{JSON.stringify(result, null, 2)}</pre>
          ) : (
            <span className="break-all">{String(result)}</span>
          )}
        </div>
        
        {activity.data?.result_metadata && (
          <div className="mt-2 pt-2 border-t border-green-200">
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                Type: {activity.data.result_metadata.result_type}
              </span>
              <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                Size: {activity.data.result_metadata.result_size} chars
              </span>
              {activity.data.result_metadata.result_is_dict && (
                <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                  Keys: {activity.data.result_metadata.result_keys?.join(', ')}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const filteredActivities = activities.filter(activity => {
    if (filter === 'all') return true;
    return activity.type === filter;
  });

  const activityTypes = [
    { value: 'all', label: 'All Activities' },
    { value: 'agent_execution', label: 'Agent Executions' },
    { value: 'tool_invocation', label: 'Tool Invocations' },
    { value: 'workflow_start', label: 'Workflow Starts' },
    { value: 'workflow_complete', label: 'Workflow Completions' },
    { value: 'workflow_failed', label: 'Workflow Failures' },
    { value: 'agent_creation', label: 'Agent Creation' },
    { value: 'agent_update', label: 'Agent Updates' },
    { value: 'agent_deletion', label: 'Agent Deletions' },
    { value: 'workflow_creation', label: 'Workflow Creation' },
    { value: 'workflow_update', label: 'Workflow Updates' },
    { value: 'workflow_deletion', label: 'Workflow Deletions' },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Activity Monitor</h1>
        <div className="flex items-center space-x-4">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
          >
            {activityTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span>Live</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow border border-gray-200">
        {filteredActivities.length === 0 ? (
          <div className="text-center py-12">
            <ActivityIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No activities yet</h3>
            <p className="text-gray-600">Activities will appear here as your agents and workflows run.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredActivities.map((activity) => (
              <div key={activity.id} className="p-6">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 mt-1">
                    {getActivityIcon(activity)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-medium text-gray-900">
                          {activity.title}
                        </h3>
                        {getStatusIcon(activity)}
                      </div>
                      
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <Clock size={12} />
                        <span>{new Date(activity.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                    
                    <p className="mt-1 text-sm text-gray-600">
                      {activity.description}
                    </p>
                    
                    {activity.error && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
                        <strong>Error:</strong> {activity.error}
                      </div>
                    )}
                    
                    <div className="mt-2 flex flex-wrap gap-2">
                      {activity.agent_id && (
                        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
                          Agent: {activity.agent_id.slice(0, 8)}
                        </span>
                      )}
                      
                      {activity.workflow_id && (
                        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-purple-100 text-purple-800">
                          Workflow: {activity.workflow_id.slice(0, 8)}
                        </span>
                      )}
                      
                      {activity.tool_id && (
                        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-100 text-green-800">
                          Tool: {activity.tool_id.replace('_tool', '')}
                        </span>
                      )}
                      
                      <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium capitalize ${
                        activity.type === 'agent_execution' ? 'bg-blue-100 text-blue-800' :
                        activity.type === 'tool_invocation' ? 'bg-green-100 text-green-800' :
                        activity.type.startsWith('workflow') ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {activity.type.replace('_', ' ')}
                      </span>
                    </div>
                    
                    {/* Prominent display of MCP tool input params */}
                    {renderToolInputParams(activity)}
                    
                    {/* Prominent display of tool execution result */}
                    {renderToolResult(activity)}
                    
                    {/* Fallback detailed view for other data */}
                    {Object.keys(activity.data).length > 0 && activity.type !== 'tool_invocation' && (
                      <details className="mt-3">
                        <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                          View details
                        </summary>
                        <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                          {JSON.stringify(activity.data, null, 2)}
                        </pre>
                      </details>
                    )}
                    
                    {/* Additional details for tool invocations */}
                    {activity.type === 'tool_invocation' && Object.keys(activity.data).length > 0 && (
                      <details className="mt-3">
                        <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                          View all technical details
                        </summary>
                        <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                          {JSON.stringify(activity.data, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};