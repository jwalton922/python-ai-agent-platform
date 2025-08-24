"""Enhanced workflow editor with node connections"""
import streamlit.components.v1 as components

def workflow_editor_with_connections(key="workflow_editor_enhanced", height=800):
    """Enhanced Streamlit component for React WorkflowEditor with connections"""
    
    component_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Enhanced Workflow Editor</title>
        <style>
            body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
                    sans-serif;
                background: #f3f4f6;
            }}
            #workflow-root {{
                width: 100%;
                height: {height - 20}px;
                overflow: hidden;
            }}
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
            .workflow-node:hover {{
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
                transform: translateY(-1px);
            }}
            .node-handle {{
                position: absolute;
                width: 12px;
                height: 12px;
                border: 2px solid white;
                border-radius: 50%;
                cursor: crosshair;
                z-index: 10;
            }}
            .input-handle {{
                left: -8px;
                top: 50%;
                transform: translateY(-50%);
                background: #10b981;
            }}
            .output-handle {{
                right: -8px;
                top: 50%;
                transform: translateY(-50%);
                background: #3b82f6;
            }}
            .node-handle:hover {{
                transform: translateY(-50%) scale(1.3);
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
            .connection-line {{
                stroke: #6366f1;
                stroke-width: 2;
                fill: none;
                marker-end: url(#arrowhead);
            }}
            .temp-connection {{
                stroke: #94a3b8;
                stroke-width: 2;
                stroke-dasharray: 5,5;
                fill: none;
            }}
        </style>
    </head>
    <body>
        <div id="workflow-root">
            <div style="padding: 20px; height: 100%; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 15px;">
                    <h2 style="margin: 0; color: #374151;">Enhanced Workflow Editor</h2>
                    <div>
                        <button onclick="WorkflowEditor.clearWorkflow()" 
                                style="background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; margin-right: 10px;">
                            Clear All
                        </button>
                        <button onclick="WorkflowEditor.saveWorkflow()" 
                                style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">
                            Save Workflow
                        </button>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 250px 1fr; gap: 20px; height: calc(100% - 80px);">
                    <!-- Sidebar -->
                    <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px;">
                        <h4 style="margin: 0 0 15px 0; color: #374151;">Available Agents</h4>
                        <div id="agents-list" style="margin-bottom: 8px;">
                            <div style="text-align: center; padding: 20px; color: #6b7280;">
                                <div style="font-size: 24px; margin-bottom: 8px;">⏳</div>
                                <div style="font-size: 12px;">Loading agents...</div>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <button onclick="WorkflowEditor.refreshAgents()" 
                                    style="width: 100%; background: #6b7280; color: white; border: none; padding: 6px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                                🔄 Refresh Agents
                            </button>
                        </div>
                        
                        <h4 style="margin: 20px 0 15px 0; color: #374151;">Connection Mode</h4>
                        <div style="margin-bottom: 15px;">
                            <label style="display: flex; align-items: center; font-size: 14px;">
                                <input type="checkbox" id="connection-mode" onchange="WorkflowEditor.toggleConnectionMode()" style="margin-right: 8px;">
                                Enable Connection Mode
                            </label>
                            <p style="font-size: 11px; color: #6b7280; margin: 4px 0 0 20px;">Check this to connect nodes by clicking them in sequence</p>
                        </div>
                        
                        <h4 style="margin: 20px 0 15px 0; color: #374151;">Actions</h4>
                        <div>
                            <button onclick="WorkflowEditor.executeWorkflow()" 
                                    style="width: 100%; background: #059669; color: white; border: none; padding: 8px; border-radius: 6px; cursor: pointer; margin-bottom: 8px;">
                                ▶️ Execute
                            </button>
                            <button onclick="WorkflowEditor.validateWorkflow()" 
                                    style="width: 100%; background: #dc2626; color: white; border: none; padding: 8px; border-radius: 6px; cursor: pointer;">
                                ✅ Validate
                            </button>
                        </div>
                    </div>
                    
                    <!-- Canvas -->
                    <div style="background: white; border: 2px dashed #d1d5db; border-radius: 8px; position: relative;">
                        <div id="workflow-canvas" style="width: 100%; height: 100%; position: relative; overflow: auto;">
                            <div id="empty-state" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #6b7280;">
                                <div style="font-size: 48px; margin-bottom: 10px;">🔧</div>
                                <h3 style="margin: 0 0 8px 0;">Drag agents here to build your workflow</h3>
                                <p style="margin: 0 0 15px 0;">Connect agents with edges to define execution flow</p>
                                <div style="background: #f3f4f6; padding: 12px; border-radius: 6px; max-width: 350px; font-size: 12px;">
                                    <p style="margin: 0 0 8px 0;"><strong>Two ways to connect nodes:</strong></p>
                                    <p style="margin: 0 0 4px 0;">1. <strong>Handle Mode:</strong> Drag from blue output handle (→) to green input handle (←)</p>
                                    <p style="margin: 0;">2. <strong>Connection Mode:</strong> Enable connection mode and click nodes in sequence</p>
                                </div>
                            </div>
                            
                            <!-- SVG for connections -->
                            <svg id="connections-svg" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1;">
                                <defs>
                                    <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                                            refX="9" refY="3.5" orient="auto">
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
                nodes: [],
                edges: [],
                isDragging: false,
                isConnecting: false,
                connectionMode: false,
                connectionStart: null,
                dragOffset: {{ x: 0, y: 0 }},
                
                init: function() {{
                    console.log('Enhanced Workflow Editor initialized');
                    this.setupEventListeners();
                }},
                
                setupEventListeners: function() {{
                    const canvas = document.getElementById('workflow-canvas');
                    
                    // Handle mouse events for temporary connection drawing
                    canvas.addEventListener('mousemove', (e) => {{
                        if (this.isConnecting && this.connectionStart) {{
                            this.updateTempConnection(e);
                        }}
                    }});
                    
                    canvas.addEventListener('mouseup', () => {{
                        if (this.isConnecting) {{
                            this.cancelConnection();
                        }}
                    }});
                }},
                
                addAgent: function(agentType) {{
                    const container = document.getElementById('nodes-container');
                    const nodeId = 'node-' + Date.now();
                    
                    // Create node element
                    const nodeDiv = document.createElement('div');
                    nodeDiv.id = nodeId;
                    nodeDiv.className = 'workflow-node';
                    nodeDiv.style.cssText = `
                        width: 180px;
                        height: 70px;
                        left: ${{100 + Math.random() * 250}}px;
                        top: ${{80 + Math.random() * 200}}px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    `;
                    
                    nodeDiv.innerHTML = `
                        <!-- Input Handle -->
                        <div class="node-handle input-handle" 
                             data-node-id="${{nodeId}}" 
                             data-handle="input"></div>
                        
                        <!-- Node Content -->
                        <div style="text-align: center; pointer-events: none;">
                            <div style="font-weight: bold; font-size: 13px;">${{agentType.replace('-', ' ').toUpperCase()}}</div>
                            <div style="font-size: 10px; opacity: 0.8;">${{nodeId.substring(5, 11)}}</div>
                        </div>
                        
                        <!-- Output Handle -->
                        <div class="node-handle output-handle" 
                             data-node-id="${{nodeId}}" 
                             data-handle="output"></div>
                    `;
                    
                    // Add event listeners
                    this.makeNodeDraggable(nodeDiv);
                    this.addNodeConnectionHandlers(nodeDiv);
                    
                    container.appendChild(nodeDiv);
                    
                    // Store node data
                    this.nodes.push({{
                        id: nodeId,
                        type: agentType,
                        x: parseInt(nodeDiv.style.left),
                        y: parseInt(nodeDiv.style.top)
                    }});
                    
                    // Hide empty state
                    const emptyState = document.getElementById('empty-state');
                    if (emptyState) emptyState.style.display = 'none';
                    
                    console.log('Added node:', nodeId, agentType);
                }},
                
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
                            const newX = e.clientX - this.dragOffset.x;
                            const newY = e.clientY - this.dragOffset.y;
                            
                            nodeElement.style.left = Math.max(0, newX) + 'px';
                            nodeElement.style.top = Math.max(0, newY) + 'px';
                            
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
                    
                    // Output handle - start connection
                    outputHandle.addEventListener('mousedown', (e) => {{
                        e.stopPropagation();
                        this.startConnection(nodeElement.id, 'output', e);
                    }});
                    
                    // Input handle - end connection
                    inputHandle.addEventListener('mouseup', (e) => {{
                        e.stopPropagation();
                        if (this.isConnecting) {{
                            this.endConnection(nodeElement.id, 'input');
                        }}
                    }});
                    
                    // Hover effects
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
                
                startConnection: function(nodeId, handleType, e) {{
                    e.preventDefault();
                    this.isConnecting = true;
                    this.connectionStart = {{ nodeId, handleType }};
                    
                    console.log('Starting connection from:', nodeId);
                    
                    // Create temporary connection line
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
                    
                    // Create edge
                    const edgeId = 'edge-' + Date.now();
                    const edge = {{
                        id: edgeId,
                        source: this.connectionStart.nodeId,
                        target: targetNodeId,
                        sourceHandle: this.connectionStart.handleType,
                        targetHandle: targetHandle
                    }};
                    
                    this.edges.push(edge);
                    this.drawConnection(edge);
                    this.cancelConnection();
                    
                    console.log('Created connection:', edge);
                }},
                
                cancelConnection: function() {{
                    this.isConnecting = false;
                    this.connectionStart = null;
                    
                    // Remove temporary connection line
                    const tempLine = document.getElementById('temp-connection');
                    if (tempLine) {{
                        tempLine.remove();
                    }}
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
                    if (this.connectionMode) {{
                        nodesContainer.style.cursor = 'crosshair';
                        console.log('Connection mode enabled');
                    }} else {{
                        nodesContainer.style.cursor = 'default';
                        this.connectionStart = null;
                        console.log('Connection mode disabled');
                    }}
                }},
                
                handleNodeClick: function(nodeId) {{
                    if (!this.connectionMode) return;
                    
                    if (!this.connectionStart) {{
                        // Start connection
                        this.connectionStart = {{ nodeId, handleType: 'output' }};
                        const node = document.getElementById(nodeId);
                        node.style.border = '3px solid #f59e0b';
                        console.log('Selected source node:', nodeId);
                    }} else if (this.connectionStart.nodeId !== nodeId) {{
                        // End connection
                        const edgeId = 'edge-' + Date.now();
                        const edge = {{
                            id: edgeId,
                            source: this.connectionStart.nodeId,
                            target: nodeId,
                            sourceHandle: 'output',
                            targetHandle: 'input'
                        }};
                        
                        this.edges.push(edge);
                        this.drawConnection(edge);
                        
                        // Reset visual feedback
                        const sourceNode = document.getElementById(this.connectionStart.nodeId);
                        sourceNode.style.border = '2px solid #4f46e5';
                        
                        this.connectionStart = null;
                        console.log('Created connection:', edge);
                    }}
                }},
                
                drawConnection: function(edge) {{
                    const svg = document.getElementById('connections-svg');
                    const sourceNode = document.getElementById(edge.source);
                    const targetNode = document.getElementById(edge.target);
                    
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
                    const dy = Math.abs(y2 - y1);
                    const offset = Math.min(dx * 0.5, 100);
                    
                    return `M ${{x1}} ${{y1}} C ${{x1 + offset}} ${{y1}}, ${{x2 - offset}} ${{y2}}, ${{x2}} ${{y2}}`;
                }},
                
                redrawConnections: function() {{
                    this.edges.forEach(edge => {{
                        const line = document.getElementById(edge.id);
                        const sourceNode = document.getElementById(edge.source);
                        const targetNode = document.getElementById(edge.target);
                        
                        if (line && sourceNode && targetNode) {{
                            this.updateConnectionPath(line, sourceNode, targetNode);
                        }}
                    }});
                }},
                
                updateNodePosition: function(nodeId, x, y) {{
                    const node = this.nodes.find(n => n.id === nodeId);
                    if (node) {{
                        node.x = x;
                        node.y = y;
                    }}
                }},
                
                clearWorkflow: function() {{
                    // Clear nodes
                    const container = document.getElementById('nodes-container');
                    container.innerHTML = '';
                    
                    // Clear connections
                    const svg = document.getElementById('connections-svg');
                    const connections = svg.querySelectorAll('.connection-line');
                    connections.forEach(conn => conn.remove());
                    
                    // Reset data
                    this.nodes = [];
                    this.edges = [];
                    this.connectionStart = null;
                    
                    // Show empty state
                    const emptyState = document.getElementById('empty-state');
                    if (emptyState) emptyState.style.display = 'block';
                    
                    console.log('Workflow cleared');
                }},
                
                saveWorkflow: function() {{
                    const workflow = {{
                        nodes: this.nodes,
                        edges: this.edges,
                        created: new Date().toISOString()
                    }};
                    
                    console.log('Saving workflow:', workflow);
                    alert(`Workflow saved with ${{this.nodes.length}} nodes and ${{this.edges.length}} connections`);
                }},
                
                executeWorkflow: function() {{
                    if (this.nodes.length === 0) {{
                        alert('Create a workflow first!');
                        return;
                    }}
                    
                    console.log('Executing workflow with', this.nodes.length, 'nodes and', this.edges.length, 'edges');
                    alert(`Executing workflow with ${{this.nodes.length}} nodes...`);
                }},
                
                validateWorkflow: function() {{
                    let issues = [];
                    
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
                    
                    if (issues.length === 0) {{
                        alert('✅ Workflow validation passed!');
                    }} else {{
                        alert('⚠️ Workflow issues found:\\n- ' + issues.join('\\n- '));
                    }}
                    
                    console.log('Validation result:', issues);
                }}
            }};
            
            // Initialize when DOM is ready
            document.addEventListener('DOMContentLoaded', function() {{
                WorkflowEditor.init();
            }});
            
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', WorkflowEditor.init);
            }} else {{
                WorkflowEditor.init();
            }}
        </script>
    </body>
    </html>
    """
    
    return components.html(component_html, height=height, scrolling=False)