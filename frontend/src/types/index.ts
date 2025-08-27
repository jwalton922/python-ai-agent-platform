export interface Agent {
  id: string;
  name: string;
  description?: string;
  instructions: string;
  mcp_tool_permissions: string[];
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  trigger_conditions: string[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface WorkflowNode {
  id: string;
  agent_id: string;
  position: { x: number; y: number };
  config: Record<string, any>;
}

export interface WorkflowEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  condition?: string;
  data_mapping: Record<string, string>;
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  trigger_conditions: string[];
  status: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface Activity {
  id: string;
  type: string;
  agent_id?: string;
  workflow_id?: string;
  tool_id?: string;
  title: string;
  description: string;
  data: Record<string, any>;
  success: boolean;
  error?: string;
  created_at: string;
}

export interface MCPTool {
  id: string;
  name: string;
  category: string;
  schema: {
    input_schema: Record<string, any>;
    output_schema: Record<string, any>;
    description: string;
  };
  enabled: boolean;
}

// Enhanced Workflow Types
export interface EnhancedWorkflowNode {
  id: string;
  type: 'agent' | 'decision' | 'transform' | 'loop' | 'parallel' | 'storage' | 'aggregator' | 'error_handler' | 'human_in_loop' | 'sub_workflow';
  name: string;
  description?: string;
  position: { x: number; y: number };
  config?: Record<string, any>;
  agent_id?: string;
  instructions_override?: string;
  instructions_append?: string;
  condition_branches?: any[];
  loop_config?: any;
  parallel_branches?: any[];
  input_mapping?: any[];
  output_mapping?: any[];
  metadata?: Record<string, any>;
}

export interface EnhancedWorkflowEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  condition?: string;
  priority?: number;
  data_mapping?: any[];
  label?: string;
  metadata?: Record<string, any>;
}

export interface WorkflowVariable {
  name: string;
  type: string;
  required: boolean;
  default?: any;
  description?: string;
  validation?: string;
  scope?: 'global' | 'local';
}

export interface WorkflowSettings {
  max_execution_time_ms: number;
  max_total_tokens?: number;
  max_parallel_executions?: number;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  continue_on_error?: boolean;
  save_intermediate_state?: boolean;
  enable_checkpoints?: boolean;
}

export interface EnhancedWorkflow {
  id: string;
  name: string;
  description?: string;
  version: string;
  nodes: EnhancedWorkflowNode[];
  edges: EnhancedWorkflowEdge[];
  variables?: WorkflowVariable[];
  settings?: WorkflowSettings;
  trigger_conditions?: string[];
  execution_mode?: 'sequential' | 'parallel' | 'streaming' | 'batch' | 'event_driven';
  status?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}