import React, { useState, useEffect } from 'react';

interface EdgeConfigurationPanelProps {
  edge: any;
  nodes: any[];
  onEdgeUpdate: (updates: any) => void;
  onClose: () => void;
}

export const EdgeConfigurationPanel: React.FC<EdgeConfigurationPanelProps> = ({
  edge,
  nodes,
  onEdgeUpdate,
  onClose
}) => {
  const [config, setConfig] = useState<any>({});

  useEffect(() => {
    setConfig(edge.data || {});
  }, [edge]);

  const updateConfig = (updates: any) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    onEdgeUpdate(updates);
  };

  const getNodeName = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    return node ? node.data?.label || node.id : nodeId;
  };

  const addDataMapping = () => {
    const dataMapping = config.data_mapping || [];
    dataMapping.push({ source: '', target: '', transformation: '' });
    updateConfig({ data_mapping: dataMapping });
  };

  const updateDataMapping = (index: number, field: string, value: string) => {
    const dataMapping = [...(config.data_mapping || [])];
    dataMapping[index] = { ...dataMapping[index], [field]: value };
    updateConfig({ data_mapping: dataMapping });
  };

  const removeDataMapping = (index: number) => {
    const dataMapping = [...(config.data_mapping || [])];
    dataMapping.splice(index, 1);
    updateConfig({ data_mapping: dataMapping });
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="text-lg font-semibold">Configure Edge</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          ✕
        </button>
      </div>
      
      <div 
        className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-6 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100" 
        style={{ maxHeight: 'calc(100vh - 80px)' }}
      >
        {/* Edge Information */}
        <div className="bg-gray-50 p-3 rounded">
          <div className="text-sm text-gray-600">
            <div><strong>From:</strong> {getNodeName(edge.source)}</div>
            <div><strong>To:</strong> {getNodeName(edge.target)}</div>
            <div><strong>Edge ID:</strong> {edge.id}</div>
          </div>
        </div>

        {/* Basic Configuration */}
        <div>
          <h4 className="text-md font-medium mb-3">Basic Settings</h4>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Label</label>
              <input
                type="text"
                value={config.label || ''}
                onChange={(e) => updateConfig({ label: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                placeholder="Edge label (optional)"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                value={config.description || ''}
                onChange={(e) => updateConfig({ description: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                rows={2}
                placeholder="Describe this connection..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Priority</label>
              <input
                type="number"
                value={config.priority || 1}
                onChange={(e) => updateConfig({ priority: parseInt(e.target.value) })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                min="1"
                max="10"
              />
              <p className="text-xs text-gray-500 mt-1">Higher numbers = higher priority</p>
            </div>
          </div>
        </div>

        {/* Conditional Execution */}
        <div>
          <h4 className="text-md font-medium mb-3">Conditional Execution</h4>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Condition Expression</label>
              <textarea
                value={config.condition || ''}
                onChange={(e) => updateConfig({ condition: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono"
                rows={3}
                placeholder="e.g., ${source_node.output.success} == true"
              />
              <p className="text-xs text-gray-500 mt-1">
                Use ${'${node_id.field}'} syntax to reference node outputs. Leave empty for unconditional execution.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Condition Type</label>
              <select
                value={config.condition_type || 'javascript'}
                onChange={(e) => updateConfig({ condition_type: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="javascript">JavaScript Expression</option>
                <option value="jmespath">JMESPath Query</option>
                <option value="jsonpath">JSONPath Expression</option>
                <option value="regex">Regular Expression</option>
                <option value="simple">Simple Comparison</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={config.negate_condition || false}
                onChange={(e) => updateConfig({ negate_condition: e.target.checked })}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Negate Condition</label>
            </div>
          </div>
        </div>

        {/* Data Mapping */}
        <div>
          <h4 className="text-md font-medium mb-3">Data Mapping</h4>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700">Field Mappings</label>
                <button
                  onClick={addDataMapping}
                  className="bg-blue-500 text-white px-2 py-1 rounded text-xs"
                >
                  Add Mapping
                </button>
              </div>
              
              {(config.data_mapping || []).map((mapping: any, index: number) => (
                <div key={index} className="border rounded p-3 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Mapping {index + 1}</span>
                    <button
                      onClick={() => removeDataMapping(index)}
                      className="text-red-500 text-xs"
                    >
                      Remove
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-1 gap-2">
                    <div>
                      <label className="block text-xs font-medium text-gray-600">Source Field</label>
                      <input
                        type="text"
                        placeholder="e.g., result.data.customer_id"
                        value={mapping.source || ''}
                        onChange={(e) => updateDataMapping(index, 'source', e.target.value)}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs font-medium text-gray-600">Target Field</label>
                      <input
                        type="text"
                        placeholder="e.g., customer_id"
                        value={mapping.target || ''}
                        onChange={(e) => updateDataMapping(index, 'target', e.target.value)}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs font-medium text-gray-600">Transformation (Optional)</label>
                      <select
                        value={mapping.transformation || ''}
                        onChange={(e) => updateDataMapping(index, 'transformation', e.target.value)}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      >
                        <option value="">No transformation</option>
                        <option value="uppercase">Uppercase</option>
                        <option value="lowercase">Lowercase</option>
                        <option value="trim">Trim whitespace</option>
                        <option value="json_parse">Parse JSON</option>
                        <option value="json_stringify">Stringify JSON</option>
                        <option value="to_number">Convert to number</option>
                        <option value="to_string">Convert to string</option>
                        <option value="to_boolean">Convert to boolean</option>
                        <option value="format_date">Format date</option>
                        <option value="custom">Custom function</option>
                      </select>
                    </div>
                    
                    {mapping.transformation === 'custom' && (
                      <div>
                        <label className="block text-xs font-medium text-gray-600">Custom Transformation</label>
                        <textarea
                          placeholder="JavaScript function: (value) => transformedValue"
                          value={mapping.custom_transformation || ''}
                          onChange={(e) => updateDataMapping(index, 'custom_transformation', e.target.value)}
                          className="w-full border border-gray-300 rounded px-2 py-1 text-sm font-mono"
                          rows={2}
                        />
                      </div>
                    )}

                    <div>
                      <label className="block text-xs font-medium text-gray-600">Default Value</label>
                      <input
                        type="text"
                        placeholder="Value to use if source is empty/null"
                        value={mapping.default_value || ''}
                        onChange={(e) => updateDataMapping(index, 'default_value', e.target.value)}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      />
                    </div>
                  </div>
                </div>
              ))}

              {(config.data_mapping || []).length === 0 && (
                <div className="text-sm text-gray-500 italic p-4 border border-dashed rounded">
                  No data mappings configured. Data will pass through unchanged.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Advanced Settings */}
        <div>
          <h4 className="text-md font-medium mb-3">Advanced Settings</h4>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Execution Delay (ms)</label>
              <input
                type="number"
                value={config.delay_ms || 0}
                onChange={(e) => updateConfig({ delay_ms: parseInt(e.target.value) })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                min="0"
              />
              <p className="text-xs text-gray-500 mt-1">Delay before executing target node</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Retry Policy</label>
              <select
                value={config.retry_policy || 'none'}
                onChange={(e) => updateConfig({ retry_policy: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="none">No retry</option>
                <option value="linear">Linear backoff</option>
                <option value="exponential">Exponential backoff</option>
                <option value="fixed">Fixed interval</option>
              </select>
            </div>

            {config.retry_policy !== 'none' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Max Retries</label>
                  <input
                    type="number"
                    value={config.max_retries || 3}
                    onChange={(e) => updateConfig({ max_retries: parseInt(e.target.value) })}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    min="1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Retry Interval (ms)</label>
                  <input
                    type="number"
                    value={config.retry_interval_ms || 1000}
                    onChange={(e) => updateConfig({ retry_interval_ms: parseInt(e.target.value) })}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    min="100"
                  />
                </div>
              </>
            )}

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={config.skip_on_error || false}
                onChange={(e) => updateConfig({ skip_on_error: e.target.checked })}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Skip on Error</label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={config.log_execution || true}
                onChange={(e) => updateConfig({ log_execution: e.target.checked })}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Log Execution</label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Tags</label>
              <input
                type="text"
                value={config.tags?.join(', ') || ''}
                onChange={(e) => updateConfig({ 
                  tags: e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean)
                })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                placeholder="tag1, tag2, tag3"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Custom Metadata (JSON)</label>
              <textarea
                value={config.metadata ? JSON.stringify(config.metadata, null, 2) : '{}'}
                onChange={(e) => {
                  try {
                    const metadata = JSON.parse(e.target.value);
                    updateConfig({ metadata });
                  } catch (error) {
                    // Handle invalid JSON
                  }
                }}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono"
                rows={3}
                placeholder='{"custom": "data"}'
              />
            </div>
          </div>
        </div>

        {/* Preview */}
        <div>
          <h4 className="text-md font-medium mb-3">Configuration Preview</h4>
          <div className="bg-gray-50 p-3 rounded">
            <pre className="text-xs text-gray-700 overflow-auto max-h-32">
              {JSON.stringify({
                source: edge.source,
                target: edge.target,
                condition: config.condition,
                data_mapping: config.data_mapping,
                priority: config.priority,
                delay_ms: config.delay_ms,
                retry_policy: config.retry_policy
              }, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};