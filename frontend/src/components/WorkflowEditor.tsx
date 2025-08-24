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
  NodeTypes
} from 'reactflow';
import 'reactflow/dist/style.css';
import { AgentNode } from './AgentNode';
import { WorkflowToolbar } from './WorkflowToolbar';
import * as api from '../services/api';
import { Agent, Workflow } from '../types';

const nodeTypes: NodeTypes = {
  agentNode: AgentNode,
};

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

export const WorkflowEditor: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [currentWorkflow, setCurrentWorkflow] = useState<Workflow | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

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
    }
  };

  const loadWorkflows = async () => {
    try {
      const workflowList = await api.listWorkflows();
      setWorkflows(workflowList);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    }
  };

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onAddNode = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    if (!agent) return;

    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: 'agentNode',
      position: { x: 250, y: 250 },
      data: {
        agent: agent,
        onDelete: (nodeId: string) => {
          setNodes((nds) => nds.filter((n) => n.id !== nodeId));
          setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
        }
      },
    };

    setNodes((nds) => nds.concat(newNode));
  };

  const saveWorkflow = async () => {
    if (!currentWorkflow?.name) {
      const name = prompt('Enter workflow name:');
      if (!name) return;

      try {
        const workflowData = {
          name,
          description: 'Created with visual editor',
          nodes: nodes.map(node => ({
            id: node.id,
            agent_id: node.data.agent.id,
            position: node.position,
            config: {}
          })),
          edges: edges.map(edge => ({
            id: edge.id || `${edge.source}-${edge.target}`,
            source_node_id: edge.source,
            target_node_id: edge.target,
            data_mapping: {}
          })),
          trigger_conditions: ['manual']
        };

        const newWorkflow = await api.createWorkflow(workflowData);
        setCurrentWorkflow(newWorkflow);
        setWorkflows(prev => [...prev, newWorkflow]);
        
        alert('Workflow saved successfully!');
      } catch (error) {
        console.error('Failed to save workflow:', error);
        alert('Failed to save workflow');
      }
    }
  };

  const executeWorkflow = async () => {
    if (!currentWorkflow) {
      alert('Please save the workflow first');
      return;
    }

    setIsExecuting(true);
    try {
      const result = await api.executeWorkflow(currentWorkflow.id, {});
      alert('Workflow executed successfully!');
      console.log('Execution result:', result);
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      alert('Failed to execute workflow');
    } finally {
      setIsExecuting(false);
    }
  };

  const loadWorkflow = (workflow: Workflow) => {
    const loadedNodes: Node[] = workflow.nodes.map(node => ({
      id: node.id,
      type: 'agentNode',
      position: node.position,
      data: {
        agent: agents.find(a => a.id === node.agent_id),
        onDelete: (nodeId: string) => {
          setNodes((nds) => nds.filter((n) => n.id !== nodeId));
          setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
        }
      }
    }));

    const loadedEdges: Edge[] = workflow.edges.map(edge => ({
      id: edge.id,
      source: edge.source_node_id,
      target: edge.target_node_id
    }));

    setNodes(loadedNodes);
    setEdges(loadedEdges);
    setCurrentWorkflow(workflow);
  };

  return (
    <div className="h-screen flex flex-col">
      <WorkflowToolbar 
        agents={agents}
        workflows={workflows}
        currentWorkflow={currentWorkflow}
        onAddNode={onAddNode}
        onSave={saveWorkflow}
        onExecute={executeWorkflow}
        onLoadWorkflow={loadWorkflow}
        isExecuting={isExecuting}
      />
      
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        </ReactFlow>
      </div>
    </div>
  );
};