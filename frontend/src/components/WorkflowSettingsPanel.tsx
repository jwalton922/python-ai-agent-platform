import React, { useState, useEffect } from 'react';

interface WorkflowSettingsPanelProps {
  settings: any;
  onSettingsChange: (settings: any) => void;
  onClose: () => void;
}

export const WorkflowSettingsPanel: React.FC<WorkflowSettingsPanelProps> = ({
  settings,
  onSettingsChange,
  onClose
}) => {
  const [config, setConfig] = useState<any>({});

  useEffect(() => {
    setConfig(settings || {});
  }, [settings]);

  const updateConfig = (updates: any) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    onSettingsChange(newConfig);
  };

  const updateNestedConfig = (section: string, updates: any) => {
    const newConfig = {
      ...config,
      [section]: { ...config[section], ...updates }
    };
    setConfig(newConfig);
    onSettingsChange(newConfig);
  };

  const addTriggerCondition = () => {
    const triggers = config.trigger_conditions || [];
    triggers.push({
      name: '',
      type: 'webhook',
      condition: '',
      config: {}
    });
    updateConfig({ trigger_conditions: triggers });
  };

  const updateTriggerCondition = (index: number, field: string, value: any) => {
    const triggers = [...(config.trigger_conditions || [])];
    triggers[index] = { ...triggers[index], [field]: value };
    updateConfig({ trigger_conditions: triggers });
  };

  const removeTriggerCondition = (index: number) => {
    const triggers = [...(config.trigger_conditions || [])];
    triggers.splice(index, 1);
    updateConfig({ trigger_conditions: triggers });
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="text-lg font-semibold">Workflow Settings</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          ✕
        </button>
      </div>
      
      <div 
        className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-6 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100" 
        style={{ maxHeight: 'calc(100vh - 80px)' }}
      >
        {/* Execution Settings */}
        <div>
          <h4 className="text-md font-medium mb-3">Execution Settings</h4>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Execution Mode</label>
              <select
                value={config.execution_mode || 'sequential'}
                onChange={(e) => updateConfig({ execution_mode: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="sequential">Sequential</option>
                <option value="parallel">Parallel</option>
                <option value="streaming">Streaming</option>
                <option value="batch">Batch</option>
                <option value="event_driven">Event Driven</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Max Execution Time (ms)</label>
              <input
                type="number"
                value={config.settings?.max_execution_time_ms || 300000}
                onChange={(e) => updateNestedConfig('settings', { 
                  max_execution_time_ms: parseInt(e.target.value) 
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Max Total Tokens</label>
              <input
                type="number"
                value={config.settings?.max_total_tokens || 5000}
                onChange={(e) => updateNestedConfig('settings', { 
                  max_total_tokens: parseInt(e.target.value) 
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Max Parallel Executions</label>
              <input
                type="number"
                value={config.settings?.max_parallel_executions || 5}
                onChange={(e) => updateNestedConfig('settings', { 
                  max_parallel_executions: parseInt(e.target.value) 
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Priority</label>
              <select
                value={config.settings?.priority || 'medium'}
                onChange={(e) => updateNestedConfig('settings', { priority: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Max Memory (MB)</label>
              <input
                type="number"
                value={config.settings?.max_memory_mb || ''}
                onChange={(e) => updateNestedConfig('settings', { 
                  max_memory_mb: e.target.value ? parseInt(e.target.value) : null
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                placeholder="No limit"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Max API Calls</label>
              <input
                type="number"
                value={config.settings?.max_api_calls || ''}
                onChange={(e) => updateNestedConfig('settings', { 
                  max_api_calls: e.target.value ? parseInt(e.target.value) : null
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                placeholder="No limit"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Rate Limit (per minute)</label>
              <input
                type="number"
                value={config.settings?.rate_limit_per_minute || ''}
                onChange={(e) => updateNestedConfig('settings', { 
                  rate_limit_per_minute: e.target.value ? parseInt(e.target.value) : null
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                placeholder="No limit"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Max Cost (USD)</label>
              <input
                type="number"
                step="0.01"
                value={config.settings?.max_cost_usd || ''}
                onChange={(e) => updateNestedConfig('settings', { 
                  max_cost_usd: e.target.value ? parseFloat(e.target.value) : null
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                placeholder="No limit"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Cost Warning Threshold</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={config.settings?.cost_warning_threshold || 0.8}
                onChange={(e) => updateNestedConfig('settings', { 
                  cost_warning_threshold: parseFloat(e.target.value) 
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">Percentage of max cost to trigger warning (0-1)</p>
            </div>
          </div>
        </div>

        {/* State Management */}
        <div>
          <h4 className="text-md font-medium mb-3">State Management</h4>
          
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={config.settings?.save_intermediate_state || true}
                onChange={(e) => updateNestedConfig('settings', { 
                  save_intermediate_state: e.target.checked 
                })}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Save Intermediate State</label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={config.settings?.enable_checkpoints || true}
                onChange={(e) => updateNestedConfig('settings', { 
                  enable_checkpoints: e.target.checked 
                })}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Enable Checkpoints</label>
            </div>

            {config.settings?.enable_checkpoints && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Checkpoint Interval (ms)</label>
                <input
                  type="number"
                  value={config.settings?.checkpoint_interval_ms || 60000}
                  onChange={(e) => updateNestedConfig('settings', { 
                    checkpoint_interval_ms: parseInt(e.target.value) 
                  })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>
            )}

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={config.settings?.continue_on_error || false}
                onChange={(e) => updateNestedConfig('settings', { 
                  continue_on_error: e.target.checked 
                })}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Continue on Error</label>
            </div>
          </div>
        </div>

        {/* Error Handling */}
        <div>
          <h4 className="text-md font-medium mb-3">Error Handling</h4>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Error Handling Strategy</label>
              <select
                value={config.error_handling_strategy || 'retry_then_fail'}
                onChange={(e) => updateConfig({ error_handling_strategy: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="fail_fast">Fail Fast</option>
                <option value="retry_then_fail">Retry Then Fail</option>
                <option value="skip_and_continue">Skip and Continue</option>
                <option value="fallback_then_continue">Fallback Then Continue</option>
                <option value="custom">Custom</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Max Retries</label>
              <input
                type="number"
                value={config.max_retries || 3}
                onChange={(e) => updateConfig({ max_retries: parseInt(e.target.value) })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Global Error Handler</label>
              <input
                type="text"
                value={config.global_error_handler || ''}
                onChange={(e) => updateConfig({ global_error_handler: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                placeholder="Node ID for global error handling"
              />
            </div>
          </div>
        </div>

        {/* Monitoring */}
        <div>
          <h4 className="text-md font-medium mb-3">Monitoring & Logging</h4>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Log Level</label>
              <select
                value={config.monitoring?.log_level || 'info'}
                onChange={(e) => updateNestedConfig('monitoring', { log_level: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="debug">Debug</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Trace Sampling Rate</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={config.monitoring?.trace_sampling || 0.1}
                onChange={(e) => updateNestedConfig('monitoring', { 
                  trace_sampling: parseFloat(e.target.value) 
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">Percentage of executions to trace (0-1)</p>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={config.monitoring?.metrics_enabled || true}
                onChange={(e) => updateNestedConfig('monitoring', { 
                  metrics_enabled: e.target.checked 
                })}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Enable Metrics</label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={config.monitoring?.capture_inputs || true}
                onChange={(e) => updateNestedConfig('monitoring', { 
                  capture_inputs: e.target.checked 
                })}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Capture Inputs</label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={config.monitoring?.capture_outputs || true}
                onChange={(e) => updateNestedConfig('monitoring', { 
                  capture_outputs: e.target.checked 
                })}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Capture Outputs</label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={config.monitoring?.capture_intermediate || false}
                onChange={(e) => updateNestedConfig('monitoring', { 
                  capture_intermediate: e.target.checked 
                })}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Capture Intermediate Results</label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Alert Channels</label>
              <input
                type="text"
                value={config.monitoring?.alert_channels?.join(', ') || ''}
                onChange={(e) => updateNestedConfig('monitoring', { 
                  alert_channels: e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean)
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                placeholder="slack, email, webhook"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">SLA (ms)</label>
              <input
                type="number"
                value={config.monitoring?.sla_ms || ''}
                onChange={(e) => updateNestedConfig('monitoring', { 
                  sla_ms: e.target.value ? parseInt(e.target.value) : null
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                placeholder="No SLA"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Error Rate Threshold</label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={config.monitoring?.error_rate_threshold || 0.1}
                onChange={(e) => updateNestedConfig('monitoring', { 
                  error_rate_threshold: parseFloat(e.target.value) 
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">Alert when error rate exceeds this (0-1)</p>
            </div>
          </div>
        </div>

        {/* Trigger Conditions */}
        <div>
          <h4 className="text-md font-medium mb-3">Trigger Conditions</h4>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700">Workflow Triggers</label>
                <button
                  onClick={addTriggerCondition}
                  className="bg-blue-500 text-white px-2 py-1 rounded text-xs"
                >
                  Add Trigger
                </button>
              </div>
              
              {(config.trigger_conditions || []).map((trigger: any, index: number) => (
                <div key={index} className="border rounded p-3 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Trigger {index + 1}</span>
                    <button
                      onClick={() => removeTriggerCondition(index)}
                      className="text-red-500 text-xs"
                    >
                      Remove
                    </button>
                  </div>
                  
                  <input
                    type="text"
                    placeholder="Trigger name"
                    value={trigger.name || ''}
                    onChange={(e) => updateTriggerCondition(index, 'name', e.target.value)}
                    className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                  />
                  
                  <select
                    value={trigger.type || 'webhook'}
                    onChange={(e) => updateTriggerCondition(index, 'type', e.target.value)}
                    className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                  >
                    <option value="webhook">Webhook</option>
                    <option value="schedule">Schedule</option>
                    <option value="event">Event</option>
                    <option value="queue">Queue</option>
                    <option value="manual">Manual</option>
                  </select>
                  
                  <textarea
                    placeholder="Trigger condition/configuration"
                    value={trigger.condition || ''}
                    onChange={(e) => updateTriggerCondition(index, 'condition', e.target.value)}
                    className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                    rows={2}
                  />
                </div>
              ))}

              {(config.trigger_conditions || []).length === 0 && (
                <div className="text-sm text-gray-500 italic p-4 border border-dashed rounded">
                  No triggers configured. Workflow can only be executed manually.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Testing Configuration */}
        <div>
          <h4 className="text-md font-medium mb-3">Testing</h4>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Test Mode</label>
              <select
                value={config.testing?.mode || 'none'}
                onChange={(e) => updateNestedConfig('testing', { mode: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="none">Disabled</option>
                <option value="dry_run">Dry Run</option>
                <option value="mock">Mock Execution</option>
                <option value="sandbox">Sandbox</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={config.testing?.generate_test_cases || false}
                onChange={(e) => updateNestedConfig('testing', { 
                  generate_test_cases: e.target.checked 
                })}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Auto-generate Test Cases</label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Test Coverage Target (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={config.testing?.coverage_target || 80}
                onChange={(e) => updateNestedConfig('testing', { 
                  coverage_target: parseInt(e.target.value) 
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
            </div>
          </div>
        </div>

        {/* Configuration Preview */}
        <div>
          <h4 className="text-md font-medium mb-3">Configuration Preview</h4>
          <div className="bg-gray-50 p-3 rounded">
            <pre className="text-xs text-gray-700 overflow-auto max-h-64">
              {JSON.stringify(config, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};