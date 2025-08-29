import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  NodeTypes,
  Panel,
  Handle,
  Position,
  MarkerType,
  ConnectionLineType
} from 'reactflow';
import 'reactflow/dist/style.css';
import * as api from '../services/api';
import { Agent } from '../types';
import { NodeConfigurationPanel } from './NodeConfigurationPanel';
import { EdgeConfigurationPanel } from './EdgeConfigurationPanel';
import { WorkflowSettingsPanel } from './WorkflowSettingsPanel';
import { VariableManagementPanel } from './VariableManagementPanel';

// Enhanced node components
const AgentNodeComponent = ({ data }: { data: any }) => (
  <div className="bg-blue-100 border-2 border-blue-300 rounded-lg p-4 min-w-[150px] relative">
    <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-blue-500" />
    <div className="font-semibold text-blue-800">🤖 Agent</div>
    <div className="text-sm text-blue-600">{data.label}</div>
    <div className="text-xs text-gray-600 mt-1">{data.agentId}</div>
    <div className="flex mt-2">
      <div className="w-2 h-2 bg-blue-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-blue-500" />
  </div>
);

const DecisionNodeComponent = ({ data }: { data: any }) => (
  <div className="bg-yellow-100 border-2 border-yellow-300 rounded-lg p-4 min-w-[150px] relative">
    <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-yellow-500" />
    <div className="font-semibold text-yellow-800">🔀 Decision</div>
    <div className="text-sm text-yellow-600">{data.label}</div>
    <div className="text-xs text-gray-600 mt-1">
      {data.branches?.length || 0} branches
    </div>
    <div className="flex mt-2">
      <div className="w-2 h-2 bg-yellow-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-yellow-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-yellow-500" />
    <Handle type="source" position={Position.Bottom} id="default" className="w-3 h-3 !bg-gray-500" />
  </div>
);

const TransformNodeComponent = ({ data }: { data: any }) => (
  <div className="bg-green-100 border-2 border-green-300 rounded-lg p-4 min-w-[150px] relative">
    <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-green-500" />
    <div className="font-semibold text-green-800">🔄 Transform</div>
    <div className="text-sm text-green-600">{data.label}</div>
    <div className="text-xs text-gray-600 mt-1">
      {data.transformations?.length || 0} transformations
    </div>
    <div className="flex mt-2">
      <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-green-500" />
  </div>
);

const LoopNodeComponent = ({ data }: { data: any }) => (
  <div className="bg-purple-100 border-2 border-purple-300 rounded-lg p-4 min-w-[150px] relative">
    <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-purple-500" />
    <div className="font-semibold text-purple-800">🔁 Loop</div>
    <div className="text-sm text-purple-600">{data.label}</div>
    <div className="text-xs text-gray-600 mt-1">
      {data.loopType} - max {data.maxIterations}
    </div>
    <div className="flex mt-2">
      <div className="w-2 h-2 bg-purple-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-purple-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-purple-500" />
    <Handle type="source" position={Position.Bottom} id="loop-body" className="w-3 h-3 !bg-purple-700" />
  </div>
);

const ParallelNodeComponent = ({ data }: { data: any }) => (
  <div className="bg-indigo-100 border-2 border-indigo-300 rounded-lg p-4 min-w-[150px] relative">
    <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-indigo-500" />
    <div className="font-semibold text-indigo-800">⚡ Parallel</div>
    <div className="text-sm text-indigo-600">{data.label}</div>
    <div className="text-xs text-gray-600 mt-1">
      {data.branches?.length || 0} branches
    </div>
    <div className="flex mt-2">
      <div className="w-2 h-2 bg-indigo-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-indigo-500 rounded-full mr-1"></div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-indigo-500" />
    {/* Multiple output handles for parallel branches */}
    <Handle type="source" position={Position.Bottom} id="branch-1" className="w-3 h-3 !bg-indigo-600" style={{ left: '25%' }} />
    <Handle type="source" position={Position.Bottom} id="branch-2" className="w-3 h-3 !bg-indigo-600" style={{ left: '75%' }} />
  </div>
);

const HumanInLoopComponent = ({ data }: { data: any }) => (
  <div className="bg-pink-100 border-2 border-pink-300 rounded-lg p-4 min-w-[150px] relative">
    <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-pink-500" />
    <div className="font-semibold text-pink-800">👤 Human</div>
    <div className="text-sm text-pink-600">{data.label}</div>
    <div className="text-xs text-gray-600 mt-1">
      Approval Required
    </div>
    <div className="flex mt-2">
      <div className="w-2 h-2 bg-pink-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-pink-500 rounded-full"></div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-pink-500" />
    <Handle type="source" position={Position.Bottom} id="rejected" className="w-3 h-3 !bg-red-500" />
  </div>
);

const StorageNodeComponent = ({ data }: { data: any }) => (
  <div className="bg-gray-100 border-2 border-gray-300 rounded-lg p-4 min-w-[150px] relative">
    <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-gray-500" />
    <div className="font-semibold text-gray-800">💾 Storage</div>
    <div className="text-sm text-gray-600">{data.label}</div>
    <div className="text-xs text-gray-600 mt-1">
      {data.operation} - {data.backend}
    </div>
    <div className="flex mt-2">
      <div className="w-2 h-2 bg-gray-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-gray-500" />
  </div>
);

const ErrorHandlerComponent = ({ data }: { data: any }) => (
  <div className="bg-red-100 border-2 border-red-300 rounded-lg p-4 min-w-[150px] relative">
    <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-red-500" />
    <div className="font-semibold text-red-800">🚨 Error Handler</div>
    <div className="text-sm text-red-600">{data.label}</div>
    <div className="text-xs text-gray-600 mt-1">
      {data.errorTypes?.length || 0} error types
    </div>
    <div className="flex mt-2">
      <div className="w-2 h-2 bg-red-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-red-500" />
    <Handle type="source" position={Position.Bottom} id="fallback" className="w-3 h-3 !bg-orange-500" />
  </div>
);

const AggregatorComponent = ({ data }: { data: any }) => (
  <div className="bg-orange-100 border-2 border-orange-300 rounded-lg p-4 min-w-[150px] relative">
    {/* Multiple input handles for aggregation */}
    <Handle type="target" position={Position.Left} id="input-1" className="w-3 h-3 !bg-orange-500" style={{ top: '30%' }} />
    <Handle type="target" position={Position.Left} id="input-2" className="w-3 h-3 !bg-orange-500" style={{ top: '70%' }} />
    <Handle type="target" position={Position.Top} id="input-3" className="w-3 h-3 !bg-orange-500" />
    <div className="font-semibold text-orange-800">📊 Aggregator</div>
    <div className="text-sm text-orange-600">{data.label}</div>
    <div className="text-xs text-gray-600 mt-1">
      Method: {data.method}
    </div>
    <div className="flex mt-2">
      <div className="w-2 h-2 bg-orange-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-orange-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-orange-500" />
  </div>
);

const ExternalTriggerComponent = ({ data }: { data: any }) => (
  <div className="bg-cyan-100 border-2 border-cyan-300 rounded-lg p-4 min-w-[150px] relative">
    <div className="font-semibold text-cyan-800">🔌 Trigger</div>
    <div className="text-sm text-cyan-600">{data.label}</div>
    <div className="text-xs text-gray-600 mt-1">
      {data.triggerType || 'Webhook'}
    </div>
    <div className="flex mt-2">
      <div className="w-2 h-2 bg-cyan-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-cyan-500 rounded-full"></div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-cyan-500" />
  </div>
);

const SubWorkflowComponent = ({ data }: { data: any }) => (
  <div className="bg-teal-100 border-2 border-teal-300 rounded-lg p-4 min-w-[150px] relative">
    <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-teal-500" />
    <div className="font-semibold text-teal-800">🔄 Sub-Workflow</div>
    <div className="text-sm text-teal-600">{data.label}</div>
    <div className="text-xs text-gray-600 mt-1">
      {data.subWorkflowId || 'Not configured'}
    </div>
    <div className="flex mt-2">
      <div className="w-2 h-2 bg-teal-500 rounded-full mr-1"></div>
      <div className="w-2 h-2 bg-teal-500 rounded-full"></div>
    </div>
    <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-teal-500" />
  </div>
);

const nodeTypes: NodeTypes = {
  agent: AgentNodeComponent,
  decision: DecisionNodeComponent,
  transform: TransformNodeComponent,
  loop: LoopNodeComponent,
  parallel: ParallelNodeComponent,
  human_in_loop: HumanInLoopComponent,
  storage: StorageNodeComponent,
  error_handler: ErrorHandlerComponent,
  aggregator: AggregatorComponent,
  external_trigger: ExternalTriggerComponent,
  sub_workflow: SubWorkflowComponent
};

// Node type definitions
const NODE_TYPE_CONFIGS = {
  agent: {
    label: 'Agent Node',
    description: 'Execute an AI agent',
    color: 'blue',
    icon: '🤖'
  },
  decision: {
    label: 'Decision Node',
    description: 'Route based on conditions',
    color: 'yellow',
    icon: '🔀'
  },
  transform: {
    label: 'Transform Node',
    description: 'Transform data',
    color: 'green',
    icon: '🔄'
  },
  loop: {
    label: 'Loop Node',
    description: 'Iterate over data',
    color: 'purple',
    icon: '🔁'
  },
  parallel: {
    label: 'Parallel Node',
    description: 'Execute branches in parallel',
    color: 'indigo',
    icon: '⚡'
  },
  human_in_loop: {
    label: 'Human Approval',
    description: 'Require human input',
    color: 'pink',
    icon: '👤'
  },
  storage: {
    label: 'Storage Node',
    description: 'Save/load data',
    color: 'gray',
    icon: '💾'
  },
  error_handler: {
    label: 'Error Handler',
    description: 'Handle errors',
    color: 'red',
    icon: '🚨'
  },
  aggregator: {
    label: 'Aggregator',
    description: 'Combine data sources',
    color: 'orange',
    icon: '📊'
  },
  external_trigger: {
    label: 'External Trigger',
    description: 'Trigger from external events',
    color: 'cyan',
    icon: '🔌'
  },
  sub_workflow: {
    label: 'Sub-Workflow',
    description: 'Execute another workflow',
    color: 'teal',
    icon: '🔄'
  }
};

// Add custom styles for better handle visibility
const customStyles = `
  .react-flow__handle {
    border: 2px solid #fff !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    transition: all 0.2s !important;
  }
  .react-flow__handle:hover {
    transform: scale(1.2) !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
  }
  .react-flow__handle-connecting {
    background: #10b981 !important;
    transform: scale(1.3) !important;
  }
  .react-flow__edge.selected {
    z-index: 1000;
  }
  .react-flow__edge.selected .react-flow__edge-path {
    stroke: #3b82f6 !important;
    stroke-width: 3px !important;
  }
`;

export const EnhancedWorkflowEditor: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [currentWorkflow, setCurrentWorkflow] = useState<any | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [showNodePanel, setShowNodePanel] = useState(true);
  const [executionResults, setExecutionResults] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedEdge, setSelectedEdge] = useState<any>(null);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [showVariablesPanel, setShowVariablesPanel] = useState(false);
  const [workflowSettings, setWorkflowSettings] = useState<any>({
    execution_mode: 'sequential',
    settings: {
      max_execution_time_ms: 300000,
      max_total_tokens: 5000,
      max_parallel_executions: 5,
      priority: 'medium',
      continue_on_error: false,
      save_intermediate_state: true,
      enable_checkpoints: true,
      checkpoint_interval_ms: 60000
    },
    monitoring: {
      log_level: 'info',
      metrics_enabled: true,
      capture_inputs: true,
      capture_outputs: true,
      capture_intermediate: false
    },
    error_handling_strategy: 'retry_then_fail',
    max_retries: 3
  });
  const [workflowVariables, setWorkflowVariables] = useState<any[]>([]);
  const [showWorkflowModal, setShowWorkflowModal] = useState(false);

  useEffect(() => {
    loadAgents();
    loadWorkflows();
  }, []);

  const loadAgents = async () => {
    try {
      const agentList = await api.listAgents();
      setAgents(agentList);
    } catch (error) {
      console.error('Failed to load agents:', error);
      console.error(error instanceof Error ? error.stack : error);
    }
  };

  const loadWorkflows = async () => {
    try {
      const response = await fetch('/api/workflows/enhanced/');
      const workflowList = await response.json();
      setWorkflows(workflowList);
    } catch (error) {
      console.error('Failed to load enhanced workflows:', error);
      console.error(error instanceof Error ? error.stack : error);
    }
  };

  const onConnect = useCallback(
    (params: Edge | Connection) => {
      const newEdge = {
        ...params,
        id: `edge_${params.source}_${params.target}_${Date.now()}`,
        data: {
          condition: '',
          data_mapping: []
        }
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setSelectedEdge(null);
  }, []);

  const onEdgeClick = useCallback((event: React.MouseEvent, edge: Edge) => {
    setSelectedEdge(edge);
    setSelectedNode(null);
  }, []);

  const updateSelectedNode = useCallback((updates: any) => {
    if (!selectedNode) return;
    
    setNodes((nds) => 
      nds.map((node) => 
        node.id === selectedNode.id 
          ? { ...node, data: { ...node.data, ...updates } }
          : node
      )
    );
    setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, ...updates } });
  }, [selectedNode, setNodes]);

  const updateSelectedEdge = useCallback((updates: any) => {
    if (!selectedEdge) return;
    
    setEdges((eds) => 
      eds.map((edge) => 
        edge.id === selectedEdge.id 
          ? { ...edge, data: { ...edge.data, ...updates }, label: updates.condition || edge.label }
          : edge
      )
    );
    setSelectedEdge({ ...selectedEdge, data: { ...selectedEdge.data, ...updates } });
  }, [selectedEdge, setEdges]);

  const addNode = (nodeType: string) => {
    const config = NODE_TYPE_CONFIGS[nodeType as keyof typeof NODE_TYPE_CONFIGS];
    const id = `${nodeType}_${Date.now()}`;
    
    const newNode: Node = {
      id,
      type: nodeType,
      position: { x: 100 + Math.random() * 300, y: 100 + Math.random() * 300 },
      data: {
        label: `${config.label} ${nodes.length + 1}`,
        nodeType: nodeType,
        agentId: nodeType === 'agent' ? agents[0]?.id : undefined,
        branches: nodeType === 'decision' ? [] : undefined,
        transformations: nodeType === 'transform' ? [] : undefined,
        loopType: nodeType === 'loop' ? 'for_each' : undefined,
        maxIterations: nodeType === 'loop' ? 10 : undefined,
        operation: nodeType === 'storage' ? 'SAVE' : undefined,
        backend: nodeType === 'storage' ? 'file' : undefined,
        errorTypes: nodeType === 'error_handler' ? ['timeout'] : undefined,
        method: nodeType === 'aggregator' ? 'MERGE' : undefined,
        triggerType: nodeType === 'external_trigger' ? 'webhook' : undefined,
        subWorkflowId: nodeType === 'sub_workflow' ? '' : undefined
      },
    };
    
    setNodes((nds) => nds.concat(newNode));
  };

  const saveWorkflow = async () => {
    if (!currentWorkflow?.name) {
      alert('Please enter a workflow name');
      return;
    }

    try {
      const workflowData = {
        id: currentWorkflow.id || `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: currentWorkflow.name,
        description: currentWorkflow.description || '',
        version: '1.0.0',
        nodes: nodes.map(node => ({
          id: node.id,
          type: node.data.nodeType,
          name: node.data.label,
          description: node.data.description || `${node.data.nodeType} node`,
          position: node.position,
          agent_id: node.data.agentId,
          instructions_override: node.data.instructionsOverride,
          instructions_append: node.data.instructionsAppend,
          condition_branches: node.data.conditionBranches,
          default_target: node.data.defaultTarget,
          transformations: node.data.transformations,
          validation_schema: node.data.validationSchema,
          loop_config: node.data.loopConfig,
          loop_body_nodes: node.data.loopBodyNodes,
          parallel_branches: node.data.parallelBranches,
          wait_strategy: node.data.waitStrategy,
          wait_count: node.data.waitCount,
          trigger_type: node.data.triggerType,
          trigger_config: node.data.triggerConfig,
          error_types: node.data.errorTypes,
          fallback_node: node.data.fallbackNode,
          aggregation_method: node.data.aggregationMethod,
          aggregation_config: node.data.aggregationConfig,
          sub_workflow_id: node.data.subWorkflowId,
          sub_workflow_version: node.data.subWorkflowVersion,
          input_mapping: node.data.inputMapping || [],
          output_mapping: node.data.outputMapping || [],
          tags: node.data.tags || [],
          metadata: node.data.metadata || {},
          config: {
            timeout_ms: node.data.timeoutMs || 120000,
            retry: node.data.retry,
            error_handling: node.data.errorHandling || 'fail',
            token_limits: node.data.tokenLimits,
            cache_results: node.data.cacheResults || false,
            cache_ttl_seconds: node.data.cacheTtlSeconds,
            agent_config: node.data.agentConfig,
            decision_config: node.data.decisionConfig,
            transform_config: node.data.transformConfig,
            loop_config: node.data.loopConfig,
            parallel_config: node.data.parallelConfig,
            human_config: node.data.humanConfig,
            storage_config: node.data.storageConfig
          }
        })),
        edges: edges.map(edge => ({
          id: edge.id,
          source_node_id: edge.source,
          target_node_id: edge.target,
          condition: edge.data?.condition || edge.label,
          data_mapping: edge.data?.data_mapping || []
        })),
        variables: workflowVariables,
        execution_mode: workflowSettings.execution_mode,
        trigger_conditions: workflowSettings.trigger_conditions || [],
        trigger_config: workflowSettings.trigger_config || {},
        global_error_handler: workflowSettings.global_error_handler,
        error_handling_strategy: workflowSettings.error_handling_strategy,
        max_retries: workflowSettings.max_retries,
        settings: workflowSettings.settings,
        monitoring: workflowSettings.monitoring,
        status: 'idle',
        tags: currentWorkflow.tags || ['enhanced', 'visual-editor']
      };

      const response = await fetch('/api/workflows/enhanced/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(workflowData),
      });

      if (response.ok) {
        const savedWorkflow = await response.json();
        setCurrentWorkflow(savedWorkflow);
        await loadWorkflows();
        alert('Workflow saved successfully!');
      } else {
        const error = await response.text();
        alert(`Failed to save workflow: ${error}`);
      }
    } catch (error) {
      console.error('Error saving workflow:', error);
      console.error(error instanceof Error ? error.stack : error);
      alert('Failed to save workflow');
    }
  };

  const executeWorkflow = async () => {
    if (!currentWorkflow?.id) {
      alert('Please save the workflow first');
      return;
    }

    setIsExecuting(true);
    setExecutionResults(null);

    try {
      const executionData = {
        input: {
          message: 'Test execution from visual editor'
        },
        debug: true,
        dry_run: false
      };

      const response = await fetch(`/api/workflows/enhanced/${currentWorkflow.id}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(executionData),
      });

      if (response.ok) {
        const result = await response.json();
        setExecutionResults(result);
        alert('Workflow executed successfully!');
      } else {
        const error = await response.text();
        alert(`Failed to execute workflow: ${error}`);
      }
    } catch (error) {
      console.error('Error executing workflow:', error);
      console.error(error instanceof Error ? error.stack : error);
      alert('Failed to execute workflow');
    } finally {
      setIsExecuting(false);
    }
  };

  const loadWorkflow = async (workflowId: string) => {
    try {
      const response = await fetch(`/api/workflows/enhanced/${workflowId}`);
      if (response.ok) {
        const workflow = await response.json();
        setCurrentWorkflow(workflow);

        // Convert workflow to React Flow format
        const flowNodes = workflow.nodes.map((node: any) => ({
          id: node.id,
          type: node.type,
          position: node.position || { x: 100, y: 100 },
          data: {
            label: node.name,
            description: node.description,
            nodeType: node.type,
            agentId: node.agent_id,
            instructionsOverride: node.instructions_override,
            instructionsAppend: node.instructions_append,
            conditionBranches: node.condition_branches,
            defaultTarget: node.default_target,
            transformations: node.transformations,
            validationSchema: node.validation_schema,
            loopConfig: node.loop_config,
            loopBodyNodes: node.loop_body_nodes,
            parallelBranches: node.parallel_branches,
            waitStrategy: node.wait_strategy,
            waitCount: node.wait_count,
            triggerType: node.trigger_type,
            triggerConfig: node.trigger_config,
            errorTypes: node.error_types,
            fallbackNode: node.fallback_node,
            aggregationMethod: node.aggregation_method,
            aggregationConfig: node.aggregation_config,
            subWorkflowId: node.sub_workflow_id,
            subWorkflowVersion: node.sub_workflow_version,
            inputMapping: node.input_mapping,
            outputMapping: node.output_mapping,
            tags: node.tags,
            metadata: node.metadata,
            // Config fields
            timeoutMs: node.config?.timeout_ms,
            errorHandling: node.config?.error_handling,
            cacheResults: node.config?.cache_results,
            cacheTtlSeconds: node.config?.cache_ttl_seconds,
            // Legacy compatibility fields
            branches: node.condition_branches || node.parallel_branches,
            loopType: node.loop_config?.type,
            maxIterations: node.loop_config?.max_iterations,
            operation: node.config?.storage_config?.operation,
            backend: node.config?.storage_config?.backend,
            method: node.aggregation_method
          }
        }));

        const flowEdges = workflow.edges.map((edge: any) => ({
          id: edge.id,
          source: edge.source_node_id,
          target: edge.target_node_id,
          label: edge.condition,
          animated: true
        }));

        setNodes(flowNodes);
        setEdges(flowEdges);
      }
    } catch (error) {
      console.error('Failed to load workflow:', error);
      console.error(error instanceof Error ? error.stack : error);
    }
  };

  const deleteWorkflow = async (workflowId: string, workflowName: string) => {
    if (!window.confirm(`Are you sure you want to delete "${workflowName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const response = await fetch(`/api/workflows/enhanced/${workflowId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await loadWorkflows();
        // Clear current workflow if it was deleted
        if (currentWorkflow?.id === workflowId) {
          setCurrentWorkflow(null);
          setNodes([]);
          setEdges([]);
        }
        alert('Workflow deleted successfully!');
      } else {
        const error = await response.text();
        alert(`Failed to delete workflow: ${error}`);
      }
    } catch (error) {
      console.error('Failed to delete workflow:', error);
      console.error(error instanceof Error ? error.stack : error);
      alert('Failed to delete workflow');
    }
  };

  // Workflow Management Modal Component
  const WorkflowManagementModal = () => {
    if (!showWorkflowModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full m-4 max-h-[80vh] overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">Manage Workflows</h2>
              <button
                onClick={() => setShowWorkflowModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          
          <div className="p-6 overflow-y-auto max-h-96">
            {workflows.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p>No workflows found</p>
                <p className="text-sm mt-1">Create your first workflow to get started</p>
              </div>
            ) : (
              <div className="space-y-3">
                {workflows.map((workflow) => (
                  <div
                    key={workflow.id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{workflow.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{workflow.description || 'No description'}</p>
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                          <span>{workflow.nodes?.length || 0} nodes</span>
                          <span>{workflow.edges?.length || 0} connections</span>
                          <span>v{workflow.version}</span>
                          {workflow.created_at && (
                            <span>Created {new Date(workflow.created_at).toLocaleDateString()}</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => {
                            loadWorkflow(workflow.id);
                            setShowWorkflowModal(false);
                          }}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        >
                          Load
                        </button>
                        <button
                          onClick={() => deleteWorkflow(workflow.id, workflow.name)}
                          className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="p-6 border-t border-gray-200 bg-gray-50">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">
                {workflows.length} workflow{workflows.length !== 1 ? 's' : ''} available
              </span>
              <button
                onClick={() => setShowWorkflowModal(false)}
                className="px-4 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="w-full h-screen flex flex-col">
      <style dangerouslySetInnerHTML={{ __html: customStyles }} />
      {/* Toolbar */}
      <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <input
            type="text"
            placeholder="Workflow name"
            className="border border-gray-300 rounded px-3 py-1"
            value={currentWorkflow?.name || ''}
            onChange={(e) => setCurrentWorkflow({
              ...currentWorkflow,
              id: currentWorkflow?.id || `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              name: e.target.value
            })}
          />
          <input
            type="text"
            placeholder="Description"
            className="border border-gray-300 rounded px-3 py-1"
            value={currentWorkflow?.description || ''}
            onChange={(e) => setCurrentWorkflow({
              ...currentWorkflow,
              id: currentWorkflow?.id || `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              description: e.target.value
            })}
          />
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowNodePanel(!showNodePanel)}
            className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
          >
            {showNodePanel ? 'Hide Nodes' : 'Add Nodes'}
          </button>
          <button
            onClick={() => setShowVariablesPanel(!showVariablesPanel)}
            className="bg-yellow-500 text-white px-3 py-1 rounded hover:bg-yellow-600"
          >
            Variables
          </button>
          <button
            onClick={() => setShowSettingsPanel(!showSettingsPanel)}
            className="bg-indigo-500 text-white px-3 py-1 rounded hover:bg-indigo-600"
          >
            Settings
          </button>
          <button
            onClick={saveWorkflow}
            className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600"
          >
            Save Workflow
          </button>
          <button
            onClick={executeWorkflow}
            disabled={isExecuting}
            className="bg-purple-500 text-white px-3 py-1 rounded hover:bg-purple-600 disabled:bg-gray-400"
          >
            {isExecuting ? 'Executing...' : 'Execute'}
          </button>
          <button
            onClick={() => setShowWorkflowModal(true)}
            className="bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-700 flex items-center space-x-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <span>Manage ({workflows.length})</span>
          </button>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* Node Panel */}
        {showNodePanel && (
          <div className="w-64 bg-gray-50 border-r border-gray-200 p-4 overflow-y-auto">
            <h3 className="font-semibold mb-4">Node Types</h3>
            <div className="space-y-2">
              {Object.entries(NODE_TYPE_CONFIGS).map(([type, config]) => (
                <button
                  key={type}
                  onClick={() => addNode(type)}
                  className="w-full text-left p-3 bg-white rounded border hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{config.icon}</span>
                    <div>
                      <div className="font-medium">{config.label}</div>
                      <div className="text-sm text-gray-600">{config.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>

          </div>
        )}

        {/* Configuration Panels */}
        {showVariablesPanel && (
          <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
            <VariableManagementPanel
              variables={workflowVariables}
              onVariablesChange={setWorkflowVariables}
              onClose={() => setShowVariablesPanel(false)}
            />
          </div>
        )}

        {showSettingsPanel && (
          <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
            <WorkflowSettingsPanel
              settings={workflowSettings}
              onSettingsChange={setWorkflowSettings}
              onClose={() => setShowSettingsPanel(false)}
            />
          </div>
        )}

        {/* Main Flow Editor */}
        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onEdgeClick={onEdgeClick}
            nodeTypes={nodeTypes}
            fitView
            className="bg-gray-100"
            defaultEdgeOptions={{
              animated: true,
              style: { strokeWidth: 2 },
              markerEnd: {
                type: MarkerType.ArrowClosed,
                color: '#374151'
              }
            }}
            connectionLineStyle={{
              strokeWidth: 2,
              stroke: '#374151'
            }}
            connectionLineType={ConnectionLineType.SmoothStep}
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
            <Controls />
            <MiniMap />
            
            {/* Execution Results Panel */}
            {executionResults && (
              <Panel position="bottom-right" className="bg-white p-4 rounded border shadow-lg max-w-md max-h-64 overflow-auto">
                <h4 className="font-semibold mb-2">Execution Results</h4>
                <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto">
                  {JSON.stringify(executionResults, null, 2)}
                </pre>
                <button
                  onClick={() => setExecutionResults(null)}
                  className="mt-2 text-sm bg-gray-500 text-white px-2 py-1 rounded hover:bg-gray-600"
                >
                  Close
                </button>
              </Panel>
            )}
          </ReactFlow>
        </div>

        {/* Right Panel - Node/Edge Configuration */}
        {(selectedNode || selectedEdge) && (
          <div className="w-80 bg-white border-l border-gray-200 h-full overflow-y-auto">
            {selectedNode && (
              <NodeConfigurationPanel
                node={selectedNode}
                agents={agents}
                onNodeUpdate={updateSelectedNode}
                onClose={() => setSelectedNode(null)}
              />
            )}
            {selectedEdge && (
              <EdgeConfigurationPanel
                edge={selectedEdge}
                nodes={nodes}
                onEdgeUpdate={updateSelectedEdge}
                onClose={() => setSelectedEdge(null)}
              />
            )}
          </div>
        )}
      </div>

      {/* Workflow Management Modal */}
      <WorkflowManagementModal />
    </div>
  );
};