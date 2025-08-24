"""Backend-integrated workflow editor with full API connectivity"""
import streamlit.components.v1 as components

def workflow_editor_integrated(key="workflow_editor_integrated", height=800):
    """Backend-integrated Streamlit workflow editor"""
    
    component_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Backend-Integrated Workflow Editor</title>
        <style>
            body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                background: #f3f4f6;
            }}
            #workflow-root {{ width: 100%; height: {height - 20}px; overflow: hidden; }}
            .workflow-node {{
                position: absolute;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px;
                border: 2px solid #4f46e5;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                user-select: none;
                cursor: move;
            }}
            .workflow-node:hover {{ box-shadow: 0 6px 12px rgba(0,0,0,0.15); transform: translateY(-1px); }}
            .node-handle {{
                position: absolute;
                width: 12px;
                height: 12px;
                border: 2px solid white;
                border-radius: 50%;
                cursor: crosshair;
                z-index: 10;
            }}
            .input-handle {{ left: -8px; top: 50%; transform: translateY(-50%); background: #10b981; }}
            .output-handle {{ right: -8px; top: 50%; transform: translateY(-50%); background: #3b82f6; }}
            .node-handle:hover {{ transform: translateY(-50%) scale(1.3); box-shadow: 0 2px 8px rgba(0,0,0,0.3); }}
            .connection-line {{ stroke: #6366f1; stroke-width: 2; fill: none; marker-end: url(#arrowhead); }}
            .temp-connection {{ stroke: #94a3b8; stroke-width: 2; stroke-dasharray: 5,5; fill: none; }}
            .agent-item {{
                padding: 8px;
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                cursor: pointer;
                margin-bottom: 6px;
                transition: all 0.2s;
            }}
            .agent-item:hover {{ background: #f3f4f6; border-color: #9ca3af; }}
            .workflow-item {{
                padding: 6px 10px;
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                margin-bottom: 4px;
                cursor: pointer;
                font-size: 12px;
            }}
            .workflow-item:hover {{ background: #f3f4f6; }}
            .workflow-item.active {{ background: #dbeafe; border-color: #3b82f6; }}
        </style>
    </head>
    <body>
        <div id="workflow-root">
            <div style="padding: 20px; height: 100%; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 15px;">
                    <div>
                        <h2 style="margin: 0; color: #374151;">Backend-Integrated Workflow Editor</h2>
                        <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                            Current: <span id="current-workflow-name" style="font-weight: 500;">New Workflow</span>
                        </div>
                    </div>
                    <div>
                        <button onclick="WorkflowEditor.newWorkflow()" 
                                style="background: #6b7280; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin-right: 8px; font-size: 12px;">
                            📄 New
                        </button>
                        <button onclick="WorkflowEditor.saveWorkflow()" 
                                style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">
                            💾 Save Workflow
                        </button>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 250px 1fr; gap: 20px; height: calc(100% - 80px);">
                    <!-- Sidebar -->
                    <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px;">
                        <!-- Saved Workflows -->
                        <h4 style="margin: 0 0 10px 0; color: #374151;">Saved Workflows</h4>
                        <div id="workflows-list" style="margin-bottom: 20px; max-height: 100px; overflow-y: auto;">
                            <div style="text-align: center; padding: 10px; color: #6b7280; font-size: 11px;">
                                Loading workflows...
                            </div>
                        </div>
                        
                        <!-- Available Agents -->
                        <h4 style="margin: 0 0 10px 0; color: #374151;">Available Agents</h4>
                        <div id="agents-list" style="margin-bottom: 15px; max-height: 150px; overflow-y: auto;">
                            <div style="text-align: center; padding: 20px; color: #6b7280;">
                                <div style="font-size: 20px; margin-bottom: 8px;">⏳</div>
                                <div style="font-size: 11px;">Loading agents...</div>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <button onclick="WorkflowEditor.refreshData()" 
                                    style="width: 100%; background: #6b7280; color: white; border: none; padding: 6px; border-radius: 4px; cursor: pointer; font-size: 11px;">
                                🔄 Refresh Data
                            </button>
                        </div>
                        
                        <!-- Connection Mode -->
                        <h4 style="margin: 20px 0 10px 0; color: #374151;">Tools</h4>
                        <div style="margin-bottom: 15px;">
                            <label style="display: flex; align-items: center; font-size: 12px;">
                                <input type="checkbox" id="connection-mode" onchange="WorkflowEditor.toggleConnectionMode()" style="margin-right: 6px;">
                                Easy Connect Mode
                            </label>
                            <p style="font-size: 10px; color: #6b7280; margin: 2px 0 0 14px;">Click nodes to connect</p>
                        </div>
                        
                        <!-- Actions -->
                        <div>
                            <button onclick="WorkflowEditor.executeWorkflow()" 
                                    style="width: 100%; background: #059669; color: white; border: none; padding: 6px; border-radius: 4px; cursor: pointer; margin-bottom: 6px; font-size: 12px;">
                                ▶️ Execute
                            </button>
                            <button onclick="WorkflowEditor.validateWorkflow()" 
                                    style="width: 100%; background: #dc2626; color: white; border: none; padding: 6px; border-radius: 4px; cursor: pointer; margin-bottom: 6px; font-size: 12px;">
                                ✅ Validate
                            </button>
                            <button onclick="WorkflowEditor.clearWorkflow()" 
                                    style="width: 100%; background: #6b7280; color: white; border: none; padding: 6px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                                🗑️ Clear
                            </button>
                        </div>
                    </div>
                    
                    <!-- Canvas -->
                    <div style="background: white; border: 2px dashed #d1d5db; border-radius: 8px; position: relative;">
                        <div id="workflow-canvas" style="width: 100%; height: 100%; position: relative; overflow: auto;">
                            <div id="empty-state" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #6b7280;">
                                <div style="font-size: 48px; margin-bottom: 10px;">🔧</div>
                                <h3 style="margin: 0 0 8px 0;">Drag agents here to build your workflow</h3>
                                <p style="margin: 0 0 15px 0;">Connect agents to define execution flow</p>
                                <div style="background: #f3f4f6; padding: 12px; border-radius: 6px; max-width: 350px; font-size: 11px;">
                                    <p style="margin: 0 0 6px 0;"><strong>How to connect:</strong></p>
                                    <p style="margin: 0 0 3px 0;">• Drag from blue handle (→) to green handle (←)</p>
                                    <p style="margin: 0;">• Or use Easy Connect Mode and click nodes</p>
                                </div>
                            </div>
                            
                            <!-- SVG for connections -->
                            <svg id="connections-svg" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1;">
                                <defs>
                                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                                        <polygon points="0 0, 10 3.5, 0 7" fill="#6366f1" />
                                    </marker>
                                </defs>
                            </svg>
                            
                            <!-- Nodes container -->
                            <div id="nodes-container" style="position: absolute; width: 100%; height: 100%; z-index: 2;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            window.WorkflowEditor = {{
                // Data
                nodes: [],
                edges: [],
                agents: [],
                workflows: [],
                currentWorkflowId: null,
                currentWorkflowName: 'New Workflow',
                
                // State
                isDragging: false,
                isConnecting: false,
                connectionMode: false,
                connectionStart: null,
                dragOffset: {{ x: 0, y: 0 }},
                
                // Config
                apiBase: 'http://localhost:8003/api',
                
                // Initialization
                init: function() {{
                    console.log('Backend-Integrated Workflow Editor initialized');
                    this.setupEventListeners();
                    this.refreshData();
                }},
                
                setupEventListeners: function() {{
                    const canvas = document.getElementById('workflow-canvas');
                    canvas.addEventListener('mousemove', (e) => {{
                        if (this.isConnecting && this.connectionStart) {{
                            this.updateTempConnection(e);
                        }}
                    }});
                    canvas.addEventListener('mouseup', () => {{
                        if (this.isConnecting) this.cancelConnection();
                    }});
                }},
                
                // API Functions
                async apiCall(endpoint, options = {{}}) {{
                    try {{
                        const url = this.apiBase + endpoint;
                        const response = await fetch(url, {{
                            headers: {{ 'Content-Type': 'application/json' }},
                            ...options
                        }});
                        
                        if (!response.ok) {{
                            throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                        }}
                        
                        return await response.json();
                    }} catch (error) {{
                        console.error('API call failed:', endpoint, error);
                        this.showError(`API Error: ${{error.message}}`);
                        return null;
                    }}
                }},
                
                showError: function(message) {{
                    // Create temporary error message
                    const errorDiv = document.createElement('div');
                    errorDiv.style.cssText = `
                        position: fixed; top: 20px; right: 20px; z-index: 10000;
                        background: #fef2f2; color: #dc2626; padding: 12px 16px;
                        border: 1px solid #fecaca; border-radius: 6px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        max-width: 300px; font-size: 13px;
                    `;
                    errorDiv.textContent = message;
                    document.body.appendChild(errorDiv);
                    
                    setTimeout(() => errorDiv.remove(), 5000);
                }},
                
                showSuccess: function(message) {{
                    const successDiv = document.createElement('div');
                    successDiv.style.cssText = `
                        position: fixed; top: 20px; right: 20px; z-index: 10000;
                        background: #f0fdf4; color: #166534; padding: 12px 16px;
                        border: 1px solid #bbf7d0; border-radius: 6px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        max-width: 300px; font-size: 13px;
                    `;
                    successDiv.textContent = message;
                    document.body.appendChild(successDiv);
                    
                    setTimeout(() => successDiv.remove(), 3000);
                }},
                
                // Data Loading Functions
                refreshData: function() {{
                    this.loadAgents();
                    this.loadWorkflows();
                }},
                
                async loadAgents() {{
                    const agents = await this.apiCall('/agents');
                    if (agents) {{
                        this.agents = agents;
                        this.renderAgentsList();
                    }}
                }},
                
                async loadWorkflows() {{
                    const workflows = await this.apiCall('/workflows');
                    if (workflows) {{
                        this.workflows = workflows;
                        this.renderWorkflowsList();
                    }}
                }},
                
                renderAgentsList: function() {{
                    const container = document.getElementById('agents-list');
                    
                    if (this.agents.length === 0) {{
                        container.innerHTML = `
                            <div style="text-align: center; padding: 15px; color: #6b7280; font-size: 11px;">
                                <div style="font-size: 20px; margin-bottom: 8px;">🤖</div>
                                <div>No agents found</div>
                                <div style="margin-top: 4px;">Create agents in the Agents tab first</div>
                            </div>
                        `;
                        return;
                    }}
                    
                    let html = '';
                    this.agents.forEach(agent => {{
                        const emoji = this.getAgentEmoji(agent.name);
                        html += `
                            <div class="agent-item" onclick="WorkflowEditor.addAgentNode('${{agent.id}}', '${{agent.name}}')">
                                <div style="font-weight: 500; font-size: 12px;">${{emoji}} ${{agent.name}}</div>
                                <div style="font-size: 10px; color: #6b7280; margin-top: 2px;">${{agent.description || 'No description'}}</div>
                            </div>
                        `;
                    }});
                    
                    container.innerHTML = html;
                }},
                
                renderWorkflowsList: function() {{
                    const container = document.getElementById('workflows-list');
                    
                    if (this.workflows.length === 0) {{
                        container.innerHTML = `
                            <div style="text-align: center; padding: 10px; color: #6b7280; font-size: 11px;">
                                No saved workflows
                            </div>
                        `;
                        return;
                    }}
                    
                    let html = '';
                    this.workflows.forEach(workflow => {{
                        const isActive = workflow.id === this.currentWorkflowId;
                        html += `
                            <div class="workflow-item ${{isActive ? 'active' : ''}}" 
                                 onclick="WorkflowEditor.loadWorkflowById('${{workflow.id}}')">
                                📋 ${{workflow.name}}
                            </div>
                        `;
                    }});
                    
                    container.innerHTML = html;
                }},
                
                getAgentEmoji: function(name) {{
                    const lowerName = name.toLowerCase();
                    if (lowerName.includes('email')) return '📧';
                    if (lowerName.includes('code') || lowerName.includes('review')) return '👨‍💻';
                    if (lowerName.includes('data') || lowerName.includes('analyst')) return '📊';
                    if (lowerName.includes('task') || lowerName.includes('schedule')) return '⏰';
                    if (lowerName.includes('slack') || lowerName.includes('chat')) return '💬';
                    if (lowerName.includes('file')) return '📁';
                    return '🤖';
                }},
                
                // Node Management
                addAgentNode: function(agentId, agentName) {{
                    const container = document.getElementById('nodes-container');
                    const nodeId = 'node-' + Date.now();
                    
                    const nodeDiv = document.createElement('div');
                    nodeDiv.id = nodeId;
                    nodeDiv.className = 'workflow-node';
                    nodeDiv.style.cssText = `
                        width: 180px; height: 70px;
                        left: ${{100 + Math.random() * 250}}px;
                        top: ${{80 + Math.random() * 200}}px;
                        display: flex; align-items: center; justify-content: center;
                    `;
                    
                    const emoji = this.getAgentEmoji(agentName);
                    nodeDiv.innerHTML = `
                        <div class="node-handle input-handle" data-node-id="${{nodeId}}" data-handle="input"></div>
                        <div style="text-align: center; pointer-events: none;">
                            <div style="font-weight: bold; font-size: 12px;">${{emoji}} ${{agentName}}</div>
                            <div style="font-size: 9px; opacity: 0.8;">${{nodeId.substring(5, 11)}}</div>
                        </div>
                        <div class="node-handle output-handle" data-node-id="${{nodeId}}" data-handle="output"></div>
                    `;
                    
                    this.makeNodeDraggable(nodeDiv);
                    this.addNodeConnectionHandlers(nodeDiv);
                    container.appendChild(nodeDiv);
                    
                    // Store node data with agent reference
                    this.nodes.push({{
                        id: nodeId,
                        agent_id: agentId,
                        agent_name: agentName,
                        position: {{ 
                            x: parseInt(nodeDiv.style.left), 
                            y: parseInt(nodeDiv.style.top) 
                        }}
                    }});
                    
                    document.getElementById('empty-state').style.display = 'none';
                    console.log('Added agent node:', nodeId, agentName);
                }},
                
                // Node interaction (dragging, connections) - keeping existing logic
                makeNodeDraggable: function(nodeElement) {{
                    let isDragging = false;
                    
                    nodeElement.addEventListener('mousedown', (e) => {{
                        if (e.target.classList.contains('node-handle')) return;
                        
                        if (this.connectionMode) {{
                            this.handleNodeClick(nodeElement.id);
                            return;
                        }}
                        
                        isDragging = true;
                        this.dragOffset.x = e.clientX - nodeElement.offsetLeft;
                        this.dragOffset.y = e.clientY - nodeElement.offsetTop;
                        nodeElement.style.zIndex = '1000';
                    }});
                    
                    document.addEventListener('mousemove', (e) => {{
                        if (isDragging) {{
                            const newX = Math.max(0, e.clientX - this.dragOffset.x);
                            const newY = Math.max(0, e.clientY - this.dragOffset.y);
                            
                            nodeElement.style.left = newX + 'px';
                            nodeElement.style.top = newY + 'px';
                            
                            this.updateNodePosition(nodeElement.id, newX, newY);
                            this.redrawConnections();
                        }}
                    }});
                    
                    document.addEventListener('mouseup', () => {{
                        if (isDragging) {{
                            isDragging = false;
                            nodeElement.style.zIndex = 'auto';
                        }}
                    }});
                }},
                
                addNodeConnectionHandlers: function(nodeElement) {{
                    const inputHandle = nodeElement.querySelector('.input-handle');
                    const outputHandle = nodeElement.querySelector('.output-handle');
                    
                    outputHandle.addEventListener('mousedown', (e) => {{
                        e.stopPropagation();
                        this.startConnection(nodeElement.id, 'output', e);
                    }});
                    
                    inputHandle.addEventListener('mouseup', (e) => {{
                        e.stopPropagation();
                        if (this.isConnecting) {{
                            this.endConnection(nodeElement.id, 'input');
                        }}
                    }});
                    
                    inputHandle.addEventListener('mouseenter', () => {{
                        if (this.isConnecting) {{
                            inputHandle.style.background = '#059669';
                            inputHandle.style.transform = 'translateY(-50%) scale(1.4)';
                        }}
                    }});
                    
                    inputHandle.addEventListener('mouseleave', () => {{
                        inputHandle.style.background = '#10b981';
                        inputHandle.style.transform = 'translateY(-50%) scale(1)';
                    }});
                }},
                
                // Connection handling - keeping existing connection logic but updating data structure
                startConnection: function(nodeId, handleType, e) {{
                    e.preventDefault();
                    this.isConnecting = true;
                    this.connectionStart = {{ nodeId, handleType }};
                    
                    const svg = document.getElementById('connections-svg');
                    const tempLine = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    tempLine.id = 'temp-connection';
                    tempLine.className = 'temp-connection';
                    svg.appendChild(tempLine);
                }},
                
                endConnection: function(targetNodeId, targetHandle) {{
                    if (!this.connectionStart || this.connectionStart.nodeId === targetNodeId) {{
                        this.cancelConnection();
                        return;
                    }}
                    
                    const edgeId = 'edge-' + Date.now();
                    const edge = {{
                        id: edgeId,
                        source: this.connectionStart.nodeId,
                        target: targetNodeId,
                        source_node_id: this.connectionStart.nodeId,
                        target_node_id: targetNodeId
                    }};
                    
                    this.edges.push(edge);
                    this.drawConnection(edge);
                    this.cancelConnection();
                    
                    console.log('Created connection:', edge);
                }},
                
                cancelConnection: function() {{
                    this.isConnecting = false;
                    this.connectionStart = null;
                    const tempLine = document.getElementById('temp-connection');
                    if (tempLine) tempLine.remove();
                }},
                
                updateTempConnection: function(e) {{
                    const tempLine = document.getElementById('temp-connection');
                    if (!tempLine || !this.connectionStart) return;
                    
                    const sourceNode = document.getElementById(this.connectionStart.nodeId);
                    const sourceRect = sourceNode.getBoundingClientRect();
                    const canvasRect = document.getElementById('workflow-canvas').getBoundingClientRect();
                    
                    const startX = sourceRect.right - canvasRect.left - 8;
                    const startY = sourceRect.top + sourceRect.height/2 - canvasRect.top;
                    const endX = e.clientX - canvasRect.left;
                    const endY = e.clientY - canvasRect.top;
                    
                    const path = this.createBezierPath(startX, startY, endX, endY);
                    tempLine.setAttribute('d', path);
                }},
                
                toggleConnectionMode: function() {{
                    const checkbox = document.getElementById('connection-mode');
                    this.connectionMode = checkbox.checked;
                    
                    const nodesContainer = document.getElementById('nodes-container');
                    nodesContainer.style.cursor = this.connectionMode ? 'crosshair' : 'default';
                }},
                
                handleNodeClick: function(nodeId) {{
                    if (!this.connectionMode) return;
                    
                    if (!this.connectionStart) {{
                        this.connectionStart = {{ nodeId, handleType: 'output' }};
                        const node = document.getElementById(nodeId);
                        node.style.border = '3px solid #f59e0b';
                    }} else if (this.connectionStart.nodeId !== nodeId) {{
                        const edge = {{
                            id: 'edge-' + Date.now(),
                            source: this.connectionStart.nodeId,
                            target: nodeId,
                            source_node_id: this.connectionStart.nodeId,
                            target_node_id: nodeId
                        }};
                        
                        this.edges.push(edge);
                        this.drawConnection(edge);
                        
                        const sourceNode = document.getElementById(this.connectionStart.nodeId);
                        sourceNode.style.border = '2px solid #4f46e5';
                        this.connectionStart = null;
                    }}
                }},
                
                drawConnection: function(edge) {{
                    const svg = document.getElementById('connections-svg');
                    const sourceNode = document.getElementById(edge.source || edge.source_node_id);
                    const targetNode = document.getElementById(edge.target || edge.target_node_id);
                    
                    if (!sourceNode || !targetNode) return;
                    
                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    line.id = edge.id;
                    line.className = 'connection-line';
                    
                    this.updateConnectionPath(line, sourceNode, targetNode);
                    svg.appendChild(line);
                }},
                
                updateConnectionPath: function(line, sourceNode, targetNode) {{
                    const sourceRect = sourceNode.getBoundingClientRect();
                    const targetRect = targetNode.getBoundingClientRect();
                    const canvasRect = document.getElementById('workflow-canvas').getBoundingClientRect();
                    
                    const startX = sourceRect.right - canvasRect.left - 8;
                    const startY = sourceRect.top + sourceRect.height/2 - canvasRect.top;
                    const endX = targetRect.left - canvasRect.left + 8;
                    const endY = targetRect.top + targetRect.height/2 - canvasRect.top;
                    
                    const path = this.createBezierPath(startX, startY, endX, endY);
                    line.setAttribute('d', path);
                }},
                
                createBezierPath: function(x1, y1, x2, y2) {{
                    const dx = Math.abs(x2 - x1);
                    const offset = Math.min(dx * 0.5, 100);
                    return `M ${{x1}} ${{y1}} C ${{x1 + offset}} ${{y1}}, ${{x2 - offset}} ${{y2}}, ${{x2}} ${{y2}}`;
                }},
                
                redrawConnections: function() {{
                    this.edges.forEach(edge => {{
                        const line = document.getElementById(edge.id);
                        const sourceNode = document.getElementById(edge.source || edge.source_node_id);
                        const targetNode = document.getElementById(edge.target || edge.target_node_id);
                        if (line && sourceNode && targetNode) {{
                            this.updateConnectionPath(line, sourceNode, targetNode);
                        }}
                    }});
                }},
                
                updateNodePosition: function(nodeId, x, y) {{
                    const node = this.nodes.find(n => n.id === nodeId);
                    if (node) {{
                        node.position = {{ x, y }};
                    }}
                }},
                
                // Workflow Management
                newWorkflow: function() {{
                    this.clearWorkflow();
                    this.currentWorkflowId = null;
                    this.currentWorkflowName = 'New Workflow';
                    document.getElementById('current-workflow-name').textContent = this.currentWorkflowName;
                    this.renderWorkflowsList();
                }},
                
                clearWorkflow: function() {{
                    const container = document.getElementById('nodes-container');
                    container.innerHTML = '';
                    
                    const svg = document.getElementById('connections-svg');
                    const connections = svg.querySelectorAll('.connection-line');
                    connections.forEach(conn => conn.remove());
                    
                    this.nodes = [];
                    this.edges = [];
                    this.connectionStart = null;
                    
                    document.getElementById('empty-state').style.display = 'block';
                }},
                
                async saveWorkflow() {{
                    if (this.nodes.length === 0) {{
                        this.showError('Cannot save empty workflow');
                        return;
                    }}
                    
                    let workflowName = this.currentWorkflowName;
                    if (workflowName === 'New Workflow') {{
                        workflowName = prompt('Enter workflow name:');
                        if (!workflowName) return;
                    }}
                    
                    const workflowData = {{
                        name: workflowName,
                        description: `Workflow with ${{this.nodes.length}} nodes and ${{this.edges.length}} connections`,
                        nodes: this.nodes.map(node => ({{
                            id: node.id,
                            agent_id: node.agent_id,
                            position: node.position
                        }})),
                        edges: this.edges.map(edge => ({{
                            id: edge.id,
                            source_node_id: edge.source,
                            target_node_id: edge.target
                        }}))
                    }};
                    
                    const endpoint = this.currentWorkflowId 
                        ? `/workflows/${{this.currentWorkflowId}}`
                        : '/workflows';
                    const method = this.currentWorkflowId ? 'PUT' : 'POST';
                    
                    const result = await this.apiCall(endpoint, {{
                        method: method,
                        body: JSON.stringify(workflowData)
                    }});
                    
                    if (result) {{
                        this.currentWorkflowId = result.id;
                        this.currentWorkflowName = result.name;
                        document.getElementById('current-workflow-name').textContent = this.currentWorkflowName;
                        
                        this.showSuccess(`Workflow "${{result.name}}" saved successfully!`);
                        this.loadWorkflows(); // Refresh list
                    }}
                }},
                
                async loadWorkflowById(workflowId) {{
                    const workflow = await this.apiCall(`/workflows/${{workflowId}}`);
                    if (!workflow) return;
                    
                    this.clearWorkflow();
                    this.currentWorkflowId = workflow.id;
                    this.currentWorkflowName = workflow.name;
                    document.getElementById('current-workflow-name').textContent = this.currentWorkflowName;
                    
                    // Load nodes
                    if (workflow.nodes && workflow.nodes.length > 0) {{
                        for (const nodeData of workflow.nodes) {{
                            const agent = this.agents.find(a => a.id === nodeData.agent_id);
                            if (agent) {{
                                this.addAgentNodeFromData(nodeData, agent);
                            }}
                        }}
                    }}
                    
                    // Load edges
                    if (workflow.edges && workflow.edges.length > 0) {{
                        setTimeout(() => {{ // Wait for nodes to render
                            workflow.edges.forEach(edgeData => {{
                                this.edges.push(edgeData);
                                this.drawConnection(edgeData);
                            }});
                        }}, 100);
                    }}
                    
                    this.renderWorkflowsList();
                    this.showSuccess(`Loaded workflow: ${{workflow.name}}`);
                }},
                
                addAgentNodeFromData: function(nodeData, agent) {{
                    const container = document.getElementById('nodes-container');
                    
                    const nodeDiv = document.createElement('div');
                    nodeDiv.id = nodeData.id;
                    nodeDiv.className = 'workflow-node';
                    nodeDiv.style.cssText = `
                        width: 180px; height: 70px;
                        left: ${{nodeData.position.x}}px;
                        top: ${{nodeData.position.y}}px;
                        display: flex; align-items: center; justify-content: center;
                    `;
                    
                    const emoji = this.getAgentEmoji(agent.name);
                    nodeDiv.innerHTML = `
                        <div class="node-handle input-handle" data-node-id="${{nodeData.id}}" data-handle="input"></div>
                        <div style="text-align: center; pointer-events: none;">
                            <div style="font-weight: bold; font-size: 12px;">${{emoji}} ${{agent.name}}</div>
                            <div style="font-size: 9px; opacity: 0.8;">${{nodeData.id.substring(5, 11)}}</div>
                        </div>
                        <div class="node-handle output-handle" data-node-id="${{nodeData.id}}" data-handle="output"></div>
                    `;
                    
                    this.makeNodeDraggable(nodeDiv);
                    this.addNodeConnectionHandlers(nodeDiv);
                    container.appendChild(nodeDiv);
                    
                    this.nodes.push({{
                        id: nodeData.id,
                        agent_id: agent.id,
                        agent_name: agent.name,
                        position: nodeData.position
                    }});
                    
                    document.getElementById('empty-state').style.display = 'none';
                }},
                
                async executeWorkflow() {{
                    if (this.nodes.length === 0) {{
                        this.showError('Cannot execute empty workflow');
                        return;
                    }}
                    
                    if (!this.currentWorkflowId) {{
                        this.showError('Save the workflow first before executing');
                        return;
                    }}
                    
                    const result = await this.apiCall(`/workflows/${{this.currentWorkflowId}}/execute`, {{
                        method: 'POST',
                        body: JSON.stringify({{ context: {{}} }})
                    }});
                    
                    if (result) {{
                        this.showSuccess(`Workflow executed successfully! Check the Activities tab for results.`);
                        console.log('Execution result:', result);
                    }}
                }},
                
                validateWorkflow: function() {{
                    let issues = [];
                    
                    if (this.nodes.length === 0) {{
                        issues.push('Workflow is empty');
                    }}
                    
                    // Check for isolated nodes
                    const connectedNodes = new Set();
                    this.edges.forEach(edge => {{
                        connectedNodes.add(edge.source);
                        connectedNodes.add(edge.target);
                    }});
                    
                    const isolatedNodes = this.nodes.filter(node => !connectedNodes.has(node.id));
                    if (isolatedNodes.length > 0) {{
                        issues.push(`${{isolatedNodes.length}} isolated node(s)`);
                    }}
                    
                    // Check for circular dependencies (basic check)
                    if (this.edges.length > 0 && this.hasCircularDependency()) {{
                        issues.push('Possible circular dependency detected');
                    }}
                    
                    if (issues.length === 0) {{
                        this.showSuccess('✅ Workflow validation passed!');
                    }} else {{
                        this.showError('⚠️ Workflow issues: ' + issues.join(', '));
                    }}
                }},
                
                hasCircularDependency: function() {{
                    // Simple cycle detection using DFS
                    const visited = new Set();
                    const recursionStack = new Set();
                    
                    const hasCycle = (node) => {{
                        if (recursionStack.has(node)) return true;
                        if (visited.has(node)) return false;
                        
                        visited.add(node);
                        recursionStack.add(node);
                        
                        const neighbors = this.edges.filter(e => e.source === node).map(e => e.target);
                        for (const neighbor of neighbors) {{
                            if (hasCycle(neighbor)) return true;
                        }}
                        
                        recursionStack.delete(node);
                        return false;
                    }};
                    
                    for (const node of this.nodes) {{
                        if (!visited.has(node.id) && hasCycle(node.id)) {{
                            return true;
                        }}
                    }}
                    
                    return false;
                }}
            }};
            
            // Initialize when DOM is ready
            document.addEventListener('DOMContentLoaded', WorkflowEditor.init.bind(WorkflowEditor));
            if (document.readyState !== 'loading') {{
                WorkflowEditor.init();
            }}
        </script>
    </body>
    </html>
    """
    
    return components.html(component_html, height=height, scrolling=False)