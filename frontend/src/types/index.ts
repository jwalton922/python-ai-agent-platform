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