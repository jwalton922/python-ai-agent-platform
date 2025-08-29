import React, { useState, useEffect } from 'react';

interface NodeConfigurationPanelProps {
  node: any;
  agents: any[];
  onNodeUpdate: (updates: any) => void;
  onClose: () => void;
}

export const NodeConfigurationPanel: React.FC<NodeConfigurationPanelProps> = ({
  node,
  agents,
  onNodeUpdate,
  onClose
}) => {
  const [config, setConfig] = useState<any>({});

  useEffect(() => {
    setConfig(node.data || {});
  }, [node]);

  const updateConfig = (updates: any) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    onNodeUpdate(updates);
  };

  const addInputMapping = () => {
    const inputMapping = config.inputMapping || [];
    inputMapping.push({ source: '', target: '' });
    updateConfig({ inputMapping });
  };

  const updateInputMapping = (index: number, field: string, value: string) => {
    const inputMapping = [...(config.inputMapping || [])];
    inputMapping[index] = { ...inputMapping[index], [field]: value };
    updateConfig({ inputMapping });
  };

  const removeInputMapping = (index: number) => {
    const inputMapping = [...(config.inputMapping || [])];
    inputMapping.splice(index, 1);
    updateConfig({ inputMapping });
  };

  const addOutputMapping = () => {
    const outputMapping = config.outputMapping || [];
    outputMapping.push({ source: '', target: '' });
    updateConfig({ outputMapping });
  };

  const updateOutputMapping = (index: number, field: string, value: string) => {
    const outputMapping = [...(config.outputMapping || [])];
    outputMapping[index] = { ...outputMapping[index], [field]: value };
    updateConfig({ outputMapping });
  };

  const removeOutputMapping = (index: number) => {
    const outputMapping = [...(config.outputMapping || [])];
    outputMapping.splice(index, 1);
    updateConfig({ outputMapping });
  };

  const renderBasicConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Node Name</label>
        <input
          type="text"
          value={config.label || ''}
          onChange={(e) => updateConfig({ label: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700">Description</label>
        <textarea
          value={config.description || ''}
          onChange={(e) => updateConfig({ description: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          rows={3}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Timeout (ms)</label>
        <input
          type="number"
          value={config.timeoutMs || 120000}
          onChange={(e) => updateConfig({ timeoutMs: parseInt(e.target.value) })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Error Handling</label>
        <select
          value={config.errorHandling || 'fail'}
          onChange={(e) => updateConfig({ errorHandling: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="fail">Fail</option>
          <option value="skip">Skip</option>
          <option value="retry">Retry</option>
          <option value="fallback">Fallback</option>
        </select>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          checked={config.cacheResults || false}
          onChange={(e) => updateConfig({ cacheResults: e.target.checked })}
          className="mr-2"
        />
        <label className="text-sm font-medium text-gray-700">Cache Results</label>
      </div>

      {config.cacheResults && (
        <div>
          <label className="block text-sm font-medium text-gray-700">Cache TTL (seconds)</label>
          <input
            type="number"
            value={config.cacheTtlSeconds || 3600}
            onChange={(e) => updateConfig({ cacheTtlSeconds: parseInt(e.target.value) })}
            className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
        </div>
      )}
    </div>
  );

  const renderAgentConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Agent</label>
        <select
          value={config.agentId || ''}
          onChange={(e) => updateConfig({ agentId: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="">Select an agent</option>
          {agents.map((agent) => (
            <option key={agent.id} value={agent.id}>
              {agent.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Instructions Override</label>
        <textarea
          value={config.instructionsOverride || ''}
          onChange={(e) => updateConfig({ instructionsOverride: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          rows={4}
          placeholder="Override the agent's default instructions..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Instructions Append</label>
        <textarea
          value={config.instructionsAppend || ''}
          onChange={(e) => updateConfig({ instructionsAppend: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          rows={3}
          placeholder="Additional instructions to append..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Max Tokens</label>
        <input
          type="number"
          value={config.tokenLimits?.max_tokens || 1000}
          onChange={(e) => updateConfig({ 
            tokenLimits: { 
              ...config.tokenLimits, 
              max_tokens: parseInt(e.target.value) 
            }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Max Cost (USD)</label>
        <input
          type="number"
          step="0.01"
          value={config.tokenLimits?.max_cost || 0.10}
          onChange={(e) => updateConfig({ 
            tokenLimits: { 
              ...config.tokenLimits, 
              max_cost: parseFloat(e.target.value) 
            }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
      </div>
    </div>
  );

  const renderDecisionConfig = () => (
    <div className="space-y-4">
      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium text-gray-700">Condition Branches</label>
          <button
            onClick={() => {
              const branches = config.conditionBranches || [];
              branches.push({ name: '', expression: '', target: '', priority: 1 });
              updateConfig({ conditionBranches: branches });
            }}
            className="bg-blue-500 text-white px-2 py-1 rounded text-xs"
          >
            Add Branch
          </button>
        </div>
        
        {(config.conditionBranches || []).map((branch: any, index: number) => (
          <div key={index} className="border rounded p-3 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Branch {index + 1}</span>
              <button
                onClick={() => {
                  const branches = [...(config.conditionBranches || [])];
                  branches.splice(index, 1);
                  updateConfig({ conditionBranches: branches });
                }}
                className="text-red-500 text-xs"
              >
                Remove
              </button>
            </div>
            
            <input
              type="text"
              placeholder="Branch name"
              value={branch.name || ''}
              onChange={(e) => {
                const branches = [...(config.conditionBranches || [])];
                branches[index] = { ...branch, name: e.target.value };
                updateConfig({ conditionBranches: branches });
              }}
              className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
            />
            
            <textarea
              placeholder="Expression (e.g., ${input.value} > 10)"
              value={branch.expression || ''}
              onChange={(e) => {
                const branches = [...(config.conditionBranches || [])];
                branches[index] = { ...branch, expression: e.target.value };
                updateConfig({ conditionBranches: branches });
              }}
              className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
              rows={2}
            />
            
            <input
              type="text"
              placeholder="Target node ID"
              value={branch.target || ''}
              onChange={(e) => {
                const branches = [...(config.conditionBranches || [])];
                branches[index] = { ...branch, target: e.target.value };
                updateConfig({ conditionBranches: branches });
              }}
              className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
            />
            
            <input
              type="number"
              placeholder="Priority"
              value={branch.priority || 1}
              onChange={(e) => {
                const branches = [...(config.conditionBranches || [])];
                branches[index] = { ...branch, priority: parseInt(e.target.value) };
                updateConfig({ conditionBranches: branches });
              }}
              className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
            />
          </div>
        ))}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Default Target</label>
        <input
          type="text"
          value={config.defaultTarget || ''}
          onChange={(e) => updateConfig({ defaultTarget: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          placeholder="Node ID for default case"
        />
      </div>
    </div>
  );

  const renderTransformConfig = () => (
    <div className="space-y-4">
      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium text-gray-700">Transformations</label>
          <button
            onClick={() => {
              const transformations = config.transformations || [];
              transformations.push({ field: '', operation: 'SET', value: '' });
              updateConfig({ transformations });
            }}
            className="bg-blue-500 text-white px-2 py-1 rounded text-xs"
          >
            Add Transform
          </button>
        </div>
        
        {(config.transformations || []).map((transform: any, index: number) => (
          <div key={index} className="border rounded p-3 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Transform {index + 1}</span>
              <button
                onClick={() => {
                  const transformations = [...(config.transformations || [])];
                  transformations.splice(index, 1);
                  updateConfig({ transformations });
                }}
                className="text-red-500 text-xs"
              >
                Remove
              </button>
            </div>
            
            <input
              type="text"
              placeholder="Field path (e.g., data.user.name)"
              value={transform.field || ''}
              onChange={(e) => {
                const transformations = [...(config.transformations || [])];
                transformations[index] = { ...transform, field: e.target.value };
                updateConfig({ transformations });
              }}
              className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
            />
            
            <select
              value={transform.operation || 'SET'}
              onChange={(e) => {
                const transformations = [...(config.transformations || [])];
                transformations[index] = { ...transform, operation: e.target.value };
                updateConfig({ transformations });
              }}
              className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
            >
              <option value="SET">Set</option>
              <option value="APPEND">Append</option>
              <option value="PREPEND">Prepend</option>
              <option value="DELETE">Delete</option>
              <option value="RENAME">Rename</option>
              <option value="CONVERT">Convert</option>
            </select>
            
            <input
              type="text"
              placeholder="Value or expression"
              value={transform.value || ''}
              onChange={(e) => {
                const transformations = [...(config.transformations || [])];
                transformations[index] = { ...transform, value: e.target.value };
                updateConfig({ transformations });
              }}
              className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
            />
          </div>
        ))}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Validation Schema (JSON)</label>
        <textarea
          value={config.validationSchema ? JSON.stringify(config.validationSchema, null, 2) : ''}
          onChange={(e) => {
            try {
              const schema = JSON.parse(e.target.value);
              updateConfig({ validationSchema: schema });
            } catch (error) {
              // Handle invalid JSON
            }
          }}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono"
          rows={4}
          placeholder='{"type": "object", "properties": {...}}'
        />
      </div>
    </div>
  );

  const renderLoopConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Loop Type</label>
        <select
          value={config.loopConfig?.type || 'for_each'}
          onChange={(e) => updateConfig({ 
            loopConfig: { ...config.loopConfig, type: e.target.value }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="for_each">For Each</option>
          <option value="while">While</option>
          <option value="until">Until</option>
          <option value="fixed_count">Fixed Count</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Max Iterations</label>
        <input
          type="number"
          value={config.loopConfig?.max_iterations || 10}
          onChange={(e) => updateConfig({ 
            loopConfig: { ...config.loopConfig, max_iterations: parseInt(e.target.value) }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Iteration Variable</label>
        <input
          type="text"
          value={config.loopConfig?.iteration_variable || 'item'}
          onChange={(e) => updateConfig({ 
            loopConfig: { ...config.loopConfig, iteration_variable: e.target.value }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          placeholder="Variable name for current item"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Loop Condition</label>
        <textarea
          value={config.loopConfig?.condition || ''}
          onChange={(e) => updateConfig({ 
            loopConfig: { ...config.loopConfig, condition: e.target.value }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          rows={2}
          placeholder="Expression for while/until loops"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Input Array Path</label>
        <input
          type="text"
          value={config.loopConfig?.input_array || ''}
          onChange={(e) => updateConfig({ 
            loopConfig: { ...config.loopConfig, input_array: e.target.value }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          placeholder="Path to array for iteration (e.g., data.items)"
        />
      </div>
    </div>
  );

  const renderParallelConfig = () => (
    <div className="space-y-4">
      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium text-gray-700">Parallel Branches</label>
          <button
            onClick={() => {
              const branches = config.parallelBranches || [];
              branches.push({ name: '', target: '', input_mapping: [] });
              updateConfig({ parallelBranches: branches });
            }}
            className="bg-blue-500 text-white px-2 py-1 rounded text-xs"
          >
            Add Branch
          </button>
        </div>
        
        {(config.parallelBranches || []).map((branch: any, index: number) => (
          <div key={index} className="border rounded p-3 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Branch {index + 1}</span>
              <button
                onClick={() => {
                  const branches = [...(config.parallelBranches || [])];
                  branches.splice(index, 1);
                  updateConfig({ parallelBranches: branches });
                }}
                className="text-red-500 text-xs"
              >
                Remove
              </button>
            </div>
            
            <input
              type="text"
              placeholder="Branch name"
              value={branch.name || ''}
              onChange={(e) => {
                const branches = [...(config.parallelBranches || [])];
                branches[index] = { ...branch, name: e.target.value };
                updateConfig({ parallelBranches: branches });
              }}
              className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
            />
            
            <input
              type="text"
              placeholder="Target node ID"
              value={branch.target || ''}
              onChange={(e) => {
                const branches = [...(config.parallelBranches || [])];
                branches[index] = { ...branch, target: e.target.value };
                updateConfig({ parallelBranches: branches });
              }}
              className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
            />
          </div>
        ))}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Wait Strategy</label>
        <select
          value={config.waitStrategy || 'wait_all'}
          onChange={(e) => updateConfig({ waitStrategy: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="wait_all">Wait All</option>
          <option value="wait_any">Wait Any</option>
          <option value="wait_first_n">Wait First N</option>
          <option value="wait_timeout">Wait Timeout</option>
        </select>
      </div>

      {config.waitStrategy === 'wait_first_n' && (
        <div>
          <label className="block text-sm font-medium text-gray-700">Wait Count</label>
          <input
            type="number"
            value={config.waitCount || 1}
            onChange={(e) => updateConfig({ waitCount: parseInt(e.target.value) })}
            className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
        </div>
      )}
    </div>
  );

  const renderHumanInLoopConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">UI Template</label>
        <textarea
          value={config.humanConfig?.ui_template || ''}
          onChange={(e) => updateConfig({ 
            humanConfig: { ...config.humanConfig, ui_template: e.target.value }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          rows={4}
          placeholder="Template with variables like ${variable_name}"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Notification Channels</label>
        <input
          type="text"
          value={config.humanConfig?.notification_channels?.join(', ') || ''}
          onChange={(e) => updateConfig({ 
            humanConfig: { 
              ...config.humanConfig, 
              notification_channels: e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean)
            }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          placeholder="slack, email, sms"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Timeout (ms)</label>
        <input
          type="number"
          value={config.humanConfig?.timeout_ms || 3600000}
          onChange={(e) => updateConfig({ 
            humanConfig: { ...config.humanConfig, timeout_ms: parseInt(e.target.value) }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Escalation After (ms)</label>
        <input
          type="number"
          value={config.humanConfig?.escalation_after_ms || 1800000}
          onChange={(e) => updateConfig({ 
            humanConfig: { ...config.humanConfig, escalation_after_ms: parseInt(e.target.value) }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Approval Options</label>
        <input
          type="text"
          value={config.humanConfig?.approval_options?.join(', ') || ''}
          onChange={(e) => updateConfig({ 
            humanConfig: { 
              ...config.humanConfig, 
              approval_options: e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean)
            }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          placeholder="approve, reject, modify"
        />
      </div>
    </div>
  );

  const renderStorageConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Operation</label>
        <select
          value={config.storageConfig?.operation || 'SAVE'}
          onChange={(e) => updateConfig({ 
            storageConfig: { ...config.storageConfig, operation: e.target.value }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="SAVE">Save</option>
          <option value="LOAD">Load</option>
          <option value="DELETE">Delete</option>
          <option value="UPDATE">Update</option>
          <option value="APPEND">Append</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Backend</label>
        <select
          value={config.storageConfig?.backend || 'file'}
          onChange={(e) => updateConfig({ 
            storageConfig: { ...config.storageConfig, backend: e.target.value }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="file">File</option>
          <option value="database">Database</option>
          <option value="memory">Memory</option>
          <option value="redis">Redis</option>
          <option value="s3">S3</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Key/Path</label>
        <input
          type="text"
          value={config.storageConfig?.key || ''}
          onChange={(e) => updateConfig({ 
            storageConfig: { ...config.storageConfig, key: e.target.value }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          placeholder="Storage key or file path"
        />
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          checked={config.storageConfig?.versioning || false}
          onChange={(e) => updateConfig({ 
            storageConfig: { ...config.storageConfig, versioning: e.target.checked }
          })}
          className="mr-2"
        />
        <label className="text-sm font-medium text-gray-700">Enable Versioning</label>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Format</label>
        <select
          value={config.storageConfig?.format || 'json'}
          onChange={(e) => updateConfig({ 
            storageConfig: { ...config.storageConfig, format: e.target.value }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="json">JSON</option>
          <option value="yaml">YAML</option>
          <option value="csv">CSV</option>
          <option value="txt">Text</option>
          <option value="binary">Binary</option>
        </select>
      </div>
    </div>
  );

  const renderErrorHandlerConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Error Types</label>
        <input
          type="text"
          value={config.errorTypes?.join(', ') || ''}
          onChange={(e) => updateConfig({ 
            errorTypes: e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean)
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          placeholder="timeout, agent_failure, validation_error"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Fallback Node</label>
        <input
          type="text"
          value={config.fallbackNode || ''}
          onChange={(e) => updateConfig({ fallbackNode: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          placeholder="Node ID to execute on error"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Max Retries</label>
        <input
          type="number"
          value={config.maxRetries || 3}
          onChange={(e) => updateConfig({ maxRetries: parseInt(e.target.value) })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Retry Delay (ms)</label>
        <input
          type="number"
          value={config.retryDelay || 1000}
          onChange={(e) => updateConfig({ retryDelay: parseInt(e.target.value) })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
      </div>
    </div>
  );

  const renderAggregatorConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Aggregation Method</label>
        <select
          value={config.aggregationMethod || 'MERGE'}
          onChange={(e) => updateConfig({ aggregationMethod: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="MERGE">Merge</option>
          <option value="CONCAT">Concat</option>
          <option value="SUM">Sum</option>
          <option value="AVERAGE">Average</option>
          <option value="MIN">Min</option>
          <option value="MAX">Max</option>
          <option value="COLLECT">Collect</option>
          <option value="CUSTOM">Custom</option>
        </select>
      </div>

      {config.aggregationMethod === 'CUSTOM' && (
        <div>
          <label className="block text-sm font-medium text-gray-700">Custom Script</label>
          <textarea
            value={config.aggregationConfig?.custom_script || ''}
            onChange={(e) => updateConfig({ 
              aggregationConfig: { ...config.aggregationConfig, custom_script: e.target.value }
            })}
            className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono"
            rows={6}
            placeholder="JavaScript function to aggregate inputs"
          />
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700">Output Path</label>
        <input
          type="text"
          value={config.aggregationConfig?.output_path || 'result'}
          onChange={(e) => updateConfig({ 
            aggregationConfig: { ...config.aggregationConfig, output_path: e.target.value }
          })}
          className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          placeholder="Path for aggregated result"
        />
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          checked={config.aggregationConfig?.preserve_individual || false}
          onChange={(e) => updateConfig({ 
            aggregationConfig: { ...config.aggregationConfig, preserve_individual: e.target.checked }
          })}
          className="mr-2"
        />
        <label className="text-sm font-medium text-gray-700">Preserve Individual Results</label>
      </div>
    </div>
  );

  const renderInputOutputMapping = () => (
    <div className="space-y-6">
      {/* Input Mapping */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium text-gray-700">Input Mapping</label>
          <button
            onClick={addInputMapping}
            className="bg-blue-500 text-white px-2 py-1 rounded text-xs"
          >
            Add Mapping
          </button>
        </div>
        
        {(config.inputMapping || []).map((mapping: any, index: number) => (
          <div key={index} className="flex items-center space-x-2 mb-2">
            <input
              type="text"
              placeholder="Source (e.g., ${global.customer_id})"
              value={mapping.source || ''}
              onChange={(e) => updateInputMapping(index, 'source', e.target.value)}
              className="flex-1 border border-gray-300 rounded px-2 py-1 text-sm"
            />
            <span className="text-gray-500">→</span>
            <input
              type="text"
              placeholder="Target field"
              value={mapping.target || ''}
              onChange={(e) => updateInputMapping(index, 'target', e.target.value)}
              className="flex-1 border border-gray-300 rounded px-2 py-1 text-sm"
            />
            <button
              onClick={() => removeInputMapping(index)}
              className="text-red-500 text-sm"
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      {/* Output Mapping */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium text-gray-700">Output Mapping</label>
          <button
            onClick={addOutputMapping}
            className="bg-blue-500 text-white px-2 py-1 rounded text-xs"
          >
            Add Mapping
          </button>
        </div>
        
        {(config.outputMapping || []).map((mapping: any, index: number) => (
          <div key={index} className="flex items-center space-x-2 mb-2">
            <input
              type="text"
              placeholder="Source field"
              value={mapping.source || ''}
              onChange={(e) => updateOutputMapping(index, 'source', e.target.value)}
              className="flex-1 border border-gray-300 rounded px-2 py-1 text-sm"
            />
            <span className="text-gray-500">→</span>
            <input
              type="text"
              placeholder="Target (e.g., customer_sentiment)"
              value={mapping.target || ''}
              onChange={(e) => updateOutputMapping(index, 'target', e.target.value)}
              className="flex-1 border border-gray-300 rounded px-2 py-1 text-sm"
            />
            <button
              onClick={() => removeOutputMapping(index)}
              className="text-red-500 text-sm"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  const renderNodeTypeSpecificConfig = () => {
    switch (node.data?.nodeType) {
      case 'agent':
        return renderAgentConfig();
      case 'decision':
        return renderDecisionConfig();
      case 'transform':
        return renderTransformConfig();
      case 'loop':
        return renderLoopConfig();
      case 'parallel':
        return renderParallelConfig();
      case 'human_in_loop':
        return renderHumanInLoopConfig();
      case 'storage':
        return renderStorageConfig();
      case 'error_handler':
        return renderErrorHandlerConfig();
      case 'aggregator':
        return renderAggregatorConfig();
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="text-lg font-semibold">
          Configure {node.data?.nodeType || 'Node'}
        </h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          ✕
        </button>
      </div>
      
      <div 
        className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-6 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100" 
        style={{ maxHeight: 'calc(100vh - 120px)' }}
      >
        {/* Basic Configuration */}
        <div>
          <h4 className="text-md font-medium mb-3">Basic Settings</h4>
          {renderBasicConfig()}
        </div>

        {/* Node Type Specific Configuration */}
        <div>
          <h4 className="text-md font-medium mb-3">
            {node.data?.nodeType?.replace('_', ' ').toUpperCase()} Settings
          </h4>
          {renderNodeTypeSpecificConfig()}
        </div>

        {/* Input/Output Mapping */}
        <div>
          <h4 className="text-md font-medium mb-3">Data Mapping</h4>
          {renderInputOutputMapping()}
        </div>
      </div>
    </div>
  );
};

export default NodeConfigurationPanel;