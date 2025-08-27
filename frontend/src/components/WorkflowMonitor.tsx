import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  Square,
  Clock,
  DollarSign,
  Zap,
  CheckCircle,
  XCircle,
  AlertCircle,
  BarChart3,
  Activity
} from 'lucide-react';

interface WorkflowExecution {
  execution_id: string;
  workflow_id: string;
  workflow_name: string;
  status: string;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  tokens_used: number;
  cost_usd: number;
  nodes_executed: number;
  success_rate: number;
  errors?: any[];
}

interface WorkflowMetrics {
  workflow_id: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  success_rate: number;
  avg_duration_ms: number;
  avg_tokens_used: number;
  avg_cost_usd: number;
  total_cost_usd: number;
}

export const WorkflowMonitor: React.FC = () => {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [metrics, setMetrics] = useState<Record<string, WorkflowMetrics>>({});
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [activeTab, setActiveTab] = useState<'executions' | 'metrics' | 'performance'>('executions');
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadExecutions();
    loadMetrics();
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadExecutions();
        loadMetrics();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const loadExecutions = async () => {
    try {
      const response = await fetch('/api/workflows/enhanced/executions?limit=50');
      if (response.ok) {
        const data = await response.json();
        setExecutions(data);
      }
    } catch (error) {
      console.error('Failed to load executions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async () => {
    try {
      // Load metrics for all workflows
      const workflowsResponse = await fetch('/api/workflows/enhanced/');
      if (workflowsResponse.ok) {
        const workflows = await workflowsResponse.json();
        
        const metricsData: Record<string, WorkflowMetrics> = {};
        for (const workflow of workflows) {
          try {
            const metricsResponse = await fetch(`/api/workflows/enhanced/${workflow.id}/metrics`);
            if (metricsResponse.ok) {
              const workflowMetrics = await metricsResponse.json();
              metricsData[workflow.id] = {
                ...workflowMetrics,
                workflow_name: workflow.name
              };
            }
          } catch (error) {
            console.error(`Failed to load metrics for workflow ${workflow.id}:`, error);
          }
        }
        setMetrics(metricsData);
      }
    } catch (error) {
      console.error('Failed to load metrics:', error);
    }
  };

  const cancelExecution = async (executionId: string) => {
    try {
      const response = await fetch(`/api/workflows/enhanced/executions/${executionId}/cancel`, {
        method: 'POST'
      });
      
      if (response.ok) {
        loadExecutions();
        alert('Execution cancelled successfully');
      } else {
        alert('Failed to cancel execution');
      }
    } catch (error) {
      console.error('Error cancelling execution:', error);
      alert('Failed to cancel execution');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running':
        return <Play className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'cancelled':
        return <Square className="w-5 h-5 text-gray-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(4)}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading workflow data...</span>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Workflow Monitor</h2>
          <p className="text-gray-600">Monitor workflow executions and performance</p>
        </div>
        <div className="flex items-center space-x-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="mr-2"
            />
            Auto-refresh
          </label>
          <button
            onClick={() => { loadExecutions(); loadMetrics(); }}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'executions', label: 'Recent Executions', icon: Activity },
            { id: 'metrics', label: 'Workflow Metrics', icon: BarChart3 },
            { id: 'performance', label: 'Performance', icon: Zap }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id as any)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'executions' && (
        <div className="space-y-4">
          {executions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No workflow executions found
            </div>
          ) : (
            executions.map((execution) => (
              <div
                key={execution.execution_id}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedExecution(execution)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(execution.status)}
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {execution.workflow_name || `Workflow ${execution.workflow_id}`}
                      </h3>
                      <p className="text-sm text-gray-600">
                        ID: {execution.execution_id.substring(0, 8)}...
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-6 text-sm text-gray-600">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{formatDuration(execution.duration_ms)}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Zap className="w-4 h-4" />
                      <span>{execution.tokens_used} tokens</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <DollarSign className="w-4 h-4" />
                      <span>{formatCost(execution.cost_usd)}</span>
                    </div>
                    <div className="text-xs">
                      {new Date(execution.started_at).toLocaleString()}
                    </div>
                    {execution.status === 'running' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          cancelExecution(execution.execution_id);
                        }}
                        className="bg-red-500 text-white px-2 py-1 rounded text-xs hover:bg-red-600"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'metrics' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(metrics).map(([workflowId, metric]) => (
            <div key={workflowId} className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="font-semibold text-gray-900 mb-4">
                {(metric as any).workflow_name || `Workflow ${workflowId}`}
              </h3>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Executions:</span>
                  <span className="font-medium">{metric.total_executions}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Success Rate:</span>
                  <span className={`font-medium ${
                    metric.success_rate >= 0.9 ? 'text-green-600' :
                    metric.success_rate >= 0.7 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {(metric.success_rate * 100).toFixed(1)}%
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Avg Duration:</span>
                  <span className="font-medium">{formatDuration(metric.avg_duration_ms)}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Avg Tokens:</span>
                  <span className="font-medium">{Math.round(metric.avg_tokens_used)}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Cost:</span>
                  <span className="font-medium">{formatCost(metric.total_cost_usd)}</span>
                </div>
              </div>
              
              {/* Progress bar for success rate */}
              <div className="mt-4">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Success Rate</span>
                  <span>{metric.successful_executions}/{metric.total_executions}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      metric.success_rate >= 0.9 ? 'bg-green-500' :
                      metric.success_rate >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${metric.success_rate * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'performance' && (
        <div className="space-y-6">
          {/* Performance Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Executions</p>
                  <p className="text-2xl font-bold text-gray-900">{executions.length}</p>
                </div>
                <Activity className="w-8 h-8 text-blue-500" />
              </div>
            </div>
            
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Success Rate</p>
                  <p className="text-2xl font-bold text-green-600">
                    {executions.length > 0 
                      ? ((executions.filter(e => e.status === 'completed').length / executions.length) * 100).toFixed(1)
                      : 0}%
                  </p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </div>
            
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Duration</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatDuration(
                      executions.reduce((sum, e) => sum + (e.duration_ms || 0), 0) / Math.max(executions.length, 1)
                    )}
                  </p>
                </div>
                <Clock className="w-8 h-8 text-blue-500" />
              </div>
            </div>
            
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Cost</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {formatCost(executions.reduce((sum, e) => sum + e.cost_usd, 0))}
                  </p>
                </div>
                <DollarSign className="w-8 h-8 text-purple-500" />
              </div>
            </div>
          </div>

          {/* Recent Activity Chart Placeholder */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Execution Timeline</h3>
            <div className="h-64 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                <p>Timeline chart visualization would go here</p>
                <p className="text-sm">Showing execution patterns over time</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Execution Details Modal */}
      {selectedExecution && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Execution Details</h3>
                <button
                  onClick={() => setSelectedExecution(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-600">Execution ID</label>
                    <p className="text-sm font-mono bg-gray-100 p-2 rounded">{selectedExecution.execution_id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600">Status</label>
                    <div className="flex items-center space-x-2 mt-1">
                      {getStatusIcon(selectedExecution.status)}
                      <span className="capitalize">{selectedExecution.status}</span>
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-600">Started At</label>
                    <p className="text-sm">{new Date(selectedExecution.started_at).toLocaleString()}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600">Duration</label>
                    <p className="text-sm">{formatDuration(selectedExecution.duration_ms)}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-600">Tokens Used</label>
                    <p className="text-sm">{selectedExecution.tokens_used}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600">Cost</label>
                    <p className="text-sm">{formatCost(selectedExecution.cost_usd)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600">Nodes Executed</label>
                    <p className="text-sm">{selectedExecution.nodes_executed}</p>
                  </div>
                </div>
                
                {selectedExecution.errors && selectedExecution.errors.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-600 mb-2">Errors</label>
                    <div className="bg-red-50 border border-red-200 rounded p-3 max-h-32 overflow-y-auto">
                      <pre className="text-xs text-red-800">{JSON.stringify(selectedExecution.errors, null, 2)}</pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};