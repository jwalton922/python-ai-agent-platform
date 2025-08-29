import React, { useState, useEffect } from 'react';

interface VariableManagementPanelProps {
  variables: any[];
  onVariablesChange: (variables: any[]) => void;
  onClose: () => void;
}

export const VariableManagementPanel: React.FC<VariableManagementPanelProps> = ({
  variables,
  onVariablesChange,
  onClose
}) => {
  const [workflowVariables, setWorkflowVariables] = useState<any[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newVariable, setNewVariable] = useState({
    name: '',
    type: 'string',
    required: false,
    default: '',
    description: '',
    scope: 'global',
    validation: null
  });

  useEffect(() => {
    setWorkflowVariables(variables || []);
  }, [variables]);

  const addVariable = () => {
    if (!newVariable.name) {
      alert('Variable name is required');
      return;
    }

    if (workflowVariables.some(v => v.name === newVariable.name)) {
      alert('Variable name already exists');
      return;
    }

    const variable = {
      ...newVariable,
      default: newVariable.default || null,
      validation: newVariable.validation || null
    };

    const updatedVariables = [...workflowVariables, variable];
    setWorkflowVariables(updatedVariables);
    onVariablesChange(updatedVariables);
    
    setNewVariable({
      name: '',
      type: 'string',
      required: false,
      default: '',
      description: '',
      scope: 'global',
      validation: null
    });
    setShowAddForm(false);
  };

  const updateVariable = (index: number, field: string, value: any) => {
    const updatedVariables = [...workflowVariables];
    updatedVariables[index] = { ...updatedVariables[index], [field]: value };
    setWorkflowVariables(updatedVariables);
    onVariablesChange(updatedVariables);
  };

  const removeVariable = (index: number) => {
    const updatedVariables = workflowVariables.filter((_, i) => i !== index);
    setWorkflowVariables(updatedVariables);
    onVariablesChange(updatedVariables);
  };

  const duplicateVariable = (index: number) => {
    const original = workflowVariables[index];
    const duplicate = {
      ...original,
      name: `${original.name}_copy`,
    };
    const updatedVariables = [...workflowVariables, duplicate];
    setWorkflowVariables(updatedVariables);
    onVariablesChange(updatedVariables);
  };

  const importVariablesFromJSON = () => {
    const jsonInput = prompt('Paste JSON array of variables:');
    if (!jsonInput) return;

    try {
      const imported = JSON.parse(jsonInput);
      if (Array.isArray(imported)) {
        const updatedVariables = [...workflowVariables, ...imported];
        setWorkflowVariables(updatedVariables);
        onVariablesChange(updatedVariables);
      } else {
        alert('Invalid JSON format. Expected an array of variables.');
      }
    } catch (error) {
      alert('Invalid JSON format');
    }
  };

  const exportVariablesToJSON = () => {
    const json = JSON.stringify(workflowVariables, null, 2);
    navigator.clipboard.writeText(json).then(() => {
      alert('Variables copied to clipboard');
    });
  };

  const getValidationComponent = (variable: any, index: number) => {
    switch (variable.type) {
      case 'string':
        return (
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-medium text-gray-600">Min Length</label>
              <input
                type="number"
                value={variable.validation?.minLength || ''}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  minLength: e.target.value ? parseInt(e.target.value) : null
                })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600">Max Length</label>
              <input
                type="number"
                value={variable.validation?.maxLength || ''}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  maxLength: e.target.value ? parseInt(e.target.value) : null
                })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600">Pattern (Regex)</label>
              <input
                type="text"
                value={variable.validation?.pattern || ''}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  pattern: e.target.value || null
                })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm font-mono"
                placeholder="^[a-zA-Z0-9]+$"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600">Allowed Values (comma-separated)</label>
              <input
                type="text"
                value={variable.validation?.enum?.join(', ') || ''}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  enum: e.target.value ? e.target.value.split(',').map((s: string) => s.trim()) : null
                })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                placeholder="option1, option2, option3"
              />
            </div>
          </div>
        );

      case 'number':
        return (
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-medium text-gray-600">Minimum</label>
              <input
                type="number"
                value={variable.validation?.minimum || ''}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  minimum: e.target.value ? parseFloat(e.target.value) : null
                })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600">Maximum</label>
              <input
                type="number"
                value={variable.validation?.maximum || ''}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  maximum: e.target.value ? parseFloat(e.target.value) : null
                })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={variable.validation?.exclusiveMinimum || false}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  exclusiveMinimum: e.target.checked
                })}
                className="mr-2"
              />
              <label className="text-xs font-medium text-gray-600">Exclusive Minimum</label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={variable.validation?.exclusiveMaximum || false}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  exclusiveMaximum: e.target.checked
                })}
                className="mr-2"
              />
              <label className="text-xs font-medium text-gray-600">Exclusive Maximum</label>
            </div>
          </div>
        );

      case 'array':
        return (
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-medium text-gray-600">Min Items</label>
              <input
                type="number"
                value={variable.validation?.minItems || ''}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  minItems: e.target.value ? parseInt(e.target.value) : null
                })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600">Max Items</label>
              <input
                type="number"
                value={variable.validation?.maxItems || ''}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  maxItems: e.target.value ? parseInt(e.target.value) : null
                })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600">Item Type</label>
              <select
                value={variable.validation?.items?.type || 'string'}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  items: { type: e.target.value }
                })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
              >
                <option value="string">String</option>
                <option value="number">Number</option>
                <option value="boolean">Boolean</option>
                <option value="object">Object</option>
              </select>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={variable.validation?.uniqueItems || false}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  uniqueItems: e.target.checked
                })}
                className="mr-2"
              />
              <label className="text-xs font-medium text-gray-600">Unique Items</label>
            </div>
          </div>
        );

      case 'object':
        return (
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-medium text-gray-600">Required Properties (comma-separated)</label>
              <input
                type="text"
                value={variable.validation?.required?.join(', ') || ''}
                onChange={(e) => updateVariable(index, 'validation', {
                  ...variable.validation,
                  required: e.target.value ? e.target.value.split(',').map((s: string) => s.trim()) : null
                })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                placeholder="prop1, prop2, prop3"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600">JSON Schema (Advanced)</label>
              <textarea
                value={variable.validation?.properties ? JSON.stringify(variable.validation.properties, null, 2) : ''}
                onChange={(e) => {
                  try {
                    const properties = JSON.parse(e.target.value);
                    updateVariable(index, 'validation', {
                      ...variable.validation,
                      properties
                    });
                  } catch (error) {
                    // Handle invalid JSON
                  }
                }}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm font-mono"
                rows={4}
                placeholder='{"propertyName": {"type": "string"}}'
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="text-lg font-semibold">Workflow Variables</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          ✕
        </button>
      </div>
      
      <div 
        className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-6 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100" 
        style={{ maxHeight: 'calc(100vh - 80px)' }}
      >
        {/* Actions */}
        <div className="flex space-x-2">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
          >
            Add Variable
          </button>
          <button
            onClick={importVariablesFromJSON}
            className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
          >
            Import JSON
          </button>
          <button
            onClick={exportVariablesToJSON}
            className="bg-purple-500 text-white px-3 py-1 rounded text-sm hover:bg-purple-600"
          >
            Export JSON
          </button>
        </div>

        {/* Add Variable Form */}
        {showAddForm && (
          <div className="border rounded p-4 bg-gray-50">
            <h4 className="text-md font-medium mb-3">Add New Variable</h4>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={newVariable.name}
                  onChange={(e) => setNewVariable({ ...newVariable, name: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="variable_name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Type</label>
                <select
                  value={newVariable.type}
                  onChange={(e) => setNewVariable({ ...newVariable, type: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="string">String</option>
                  <option value="number">Number</option>
                  <option value="boolean">Boolean</option>
                  <option value="array">Array</option>
                  <option value="object">Object</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Scope</label>
                <select
                  value={newVariable.scope}
                  onChange={(e) => setNewVariable({ ...newVariable, scope: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="global">Global</option>
                  <option value="local">Local</option>
                  <option value="input">Input Only</option>
                  <option value="output">Output Only</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={newVariable.required}
                  onChange={(e) => setNewVariable({ ...newVariable, required: e.target.checked })}
                  className="mr-2"
                />
                <label className="text-sm font-medium text-gray-700">Required</label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Default Value</label>
                <input
                  type="text"
                  value={newVariable.default}
                  onChange={(e) => setNewVariable({ ...newVariable, default: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="Default value (optional)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={newVariable.description}
                  onChange={(e) => setNewVariable({ ...newVariable, description: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  rows={2}
                  placeholder="Describe what this variable is used for..."
                />
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={addVariable}
                  className="bg-blue-500 text-white px-4 py-2 rounded text-sm hover:bg-blue-600"
                >
                  Add Variable
                </button>
                <button
                  onClick={() => setShowAddForm(false)}
                  className="bg-gray-500 text-white px-4 py-2 rounded text-sm hover:bg-gray-600"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Variable List */}
        <div>
          <h4 className="text-md font-medium mb-3">
            Current Variables ({workflowVariables.length})
          </h4>
          
          {workflowVariables.length === 0 ? (
            <div className="text-sm text-gray-500 italic p-4 border border-dashed rounded">
              No variables defined. Add variables to pass data to workflow nodes.
            </div>
          ) : (
            <div className="space-y-4">
              {workflowVariables.map((variable, index) => (
                <div key={index} className="border rounded p-4 bg-white">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h5 className="font-medium text-gray-900">
                        {variable.name}
                        {variable.required && <span className="text-red-500 ml-1">*</span>}
                      </h5>
                      <div className="text-sm text-gray-600">
                        <span className="inline-block bg-gray-100 px-2 py-1 rounded mr-2">
                          {variable.type}
                        </span>
                        <span className="inline-block bg-blue-100 px-2 py-1 rounded">
                          {variable.scope}
                        </span>
                      </div>
                    </div>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => duplicateVariable(index)}
                        className="text-blue-500 text-xs hover:bg-blue-50 px-2 py-1 rounded"
                        title="Duplicate"
                      >
                        📋
                      </button>
                      <button
                        onClick={() => removeVariable(index)}
                        className="text-red-500 text-xs hover:bg-red-50 px-2 py-1 rounded"
                        title="Delete"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-600">Name</label>
                      <input
                        type="text"
                        value={variable.name}
                        onChange={(e) => updateVariable(index, 'name', e.target.value)}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-600">Type</label>
                      <select
                        value={variable.type}
                        onChange={(e) => updateVariable(index, 'type', e.target.value)}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      >
                        <option value="string">String</option>
                        <option value="number">Number</option>
                        <option value="boolean">Boolean</option>
                        <option value="array">Array</option>
                        <option value="object">Object</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-600">Scope</label>
                      <select
                        value={variable.scope}
                        onChange={(e) => updateVariable(index, 'scope', e.target.value)}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      >
                        <option value="global">Global</option>
                        <option value="local">Local</option>
                        <option value="input">Input Only</option>
                        <option value="output">Output Only</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-600">Default Value</label>
                      <input
                        type="text"
                        value={variable.default || ''}
                        onChange={(e) => updateVariable(index, 'default', e.target.value || null)}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      />
                    </div>
                  </div>

                  <div className="mt-3">
                    <label className="block text-xs font-medium text-gray-600">Description</label>
                    <textarea
                      value={variable.description || ''}
                      onChange={(e) => updateVariable(index, 'description', e.target.value)}
                      className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      rows={2}
                    />
                  </div>

                  <div className="flex items-center mt-2">
                    <input
                      type="checkbox"
                      checked={variable.required || false}
                      onChange={(e) => updateVariable(index, 'required', e.target.checked)}
                      className="mr-2"
                    />
                    <label className="text-xs font-medium text-gray-600">Required</label>
                  </div>

                  {/* Validation Configuration */}
                  <details className="mt-3">
                    <summary className="text-xs font-medium text-gray-600 cursor-pointer hover:text-gray-800">
                      Validation Rules
                    </summary>
                    <div className="mt-2 p-2 bg-gray-50 rounded">
                      {getValidationComponent(variable, index)}
                    </div>
                  </details>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Variable Usage Examples */}
        <div>
          <h4 className="text-md font-medium mb-3">Usage Examples</h4>
          <div className="bg-gray-50 p-3 rounded text-sm">
            <div className="space-y-2">
              <div><strong>In node expressions:</strong> <code>${"${variable_name}"}</code></div>
              <div><strong>In global context:</strong> <code>${"${global.variable_name}"}</code></div>
              <div><strong>In node output:</strong> <code>${"${node_id.variable_name}"}</code></div>
              <div><strong>In conditions:</strong> <code>${"${input.count} > 5"}</code></div>
              <div><strong>Object property:</strong> <code>${"${user.profile.email}"}</code></div>
              <div><strong>Array access:</strong> <code>${"${items[0].name}"}</code></div>
            </div>
          </div>
        </div>

        {/* Export Preview */}
        {workflowVariables.length > 0 && (
          <div>
            <h4 className="text-md font-medium mb-3">JSON Export Preview</h4>
            <div className="bg-gray-50 p-3 rounded">
              <pre className="text-xs text-gray-700 overflow-auto max-h-32">
                {JSON.stringify(workflowVariables, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};