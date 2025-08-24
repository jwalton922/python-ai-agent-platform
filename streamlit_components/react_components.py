"""Streamlit wrapper for React UI components"""
import streamlit as st
import streamlit.components.v1 as components
import os
import json
from pathlib import Path

# Get the absolute path to the frontend build directory
FRONTEND_BUILD_PATH = Path(__file__).parent.parent / "frontend" / "build"

def workflow_editor(key="workflow_editor", height=800):
    """Streamlit component for React WorkflowEditor"""
    
    # HTML template that loads the React component
    component_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Workflow Editor</title>
        <style>
            body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
                    sans-serif;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
                background: #f3f4f6;
            }}
            #react-workflow-root {{
                width: 100%;
                height: {height - 20}px;
                overflow: hidden;
            }}
        </style>
    </head>
    <body>
        <div id="react-workflow-root">
            <div style="padding: 20px; text-align: center;">
                <h3>Loading Workflow Editor...</h3>
                <p>If this message persists, please build the React frontend first.</p>
                <code>cd frontend && npm run build</code>
            </div>
        </div>
        
        <script>
            // Embedded React component for workflow editing
            window.WorkflowEditorComponent = {{
                nodes: [],
                edges: [],
                isConnecting: false,
                connectionStart: null,
                tempConnection: null,
                
                init: function() {{
                    const root = document.getElementById('react-workflow-root');
                    
                    // Create workflow editor interface
                    root.innerHTML = `
                        <div style="padding: 20px; height: 100%; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 15px;">
                                <h2 style="margin: 0; color: #374151;">Workflow Editor</h2>
                                <div>
                                    <button onclick="WorkflowEditorComponent.createWorkflow()" 
                                            style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; margin-right: 10px;">
                                        New Workflow
                                    </button>
                                    <button onclick="WorkflowEditorComponent.saveWorkflow()" 
                                            style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">
                                        Save Workflow
                                    </button>
                                </div>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: 250px 1fr; gap: 20px; height: calc(100% - 80px);">
                                <!-- Sidebar -->
                                <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px;">
                                    <h4 style="margin: 0 0 15px 0; color: #374151;">Available Agents</h4>
                                    <div id="agents-list" style="space-y: 8px;">
                                        <div style="padding: 8px; background: white; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer;" 
                                             onclick="WorkflowEditorComponent.addAgent('email-assistant')">
                                            📧 Email Assistant
                                        </div>
                                        <div style="padding: 8px; background: white; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer;" 
                                             onclick="WorkflowEditorComponent.addAgent('code-reviewer')">
                                            👨‍💻 Code Reviewer
                                        </div>
                                        <div style="padding: 8px; background: white; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer;" 
                                             onclick="WorkflowEditorComponent.addAgent('data-analyst')">
                                            📊 Data Analyst
                                        </div>
                                    </div>
                                    
                                    <h4 style="margin: 20px 0 15px 0; color: #374151;">Workflow Tools</h4>
                                    <div style="space-y: 8px;">
                                        <button onclick="WorkflowEditorComponent.executeWorkflow()" 
                                                style="width: 100%; background: #059669; color: white; border: none; padding: 8px; border-radius: 6px; cursor: pointer;">
                                            ▶️ Execute
                                        </button>
                                        <button onclick="WorkflowEditorComponent.validateWorkflow()" 
                                                style="width: 100%; background: #dc2626; color: white; border: none; padding: 8px; border-radius: 6px; cursor: pointer;">
                                            ✅ Validate
                                        </button>
                                    </div>
                                </div>
                                
                                <!-- Canvas -->
                                <div style="background: white; border: 2px dashed #d1d5db; border-radius: 8px; position: relative;">
                                    <div id="workflow-canvas" style="width: 100%; height: 100%; position: relative; overflow: auto;">
                                        <div id="workflow-empty-state" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #6b7280;">
                                            <div style="font-size: 48px; margin-bottom: 10px;">🔧</div>
                                            <h3 style="margin: 0;">Drag agents here to build your workflow</h3>
                                            <p style="margin: 5px 0 0 0;">Connect agents with edges to define execution flow</p>
                                            <p style="margin: 15px 0 0 0; font-size: 12px; background: #f3f4f6; padding: 8px; border-radius: 4px; max-width: 300px;">
                                                <strong>How to connect:</strong> Click and drag from a node's output handle (→) to another node's input handle (←)
                                            </p>
                                        </div>
                                        <svg id="workflow-connections" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1;">
                                        </svg>
                                        <div id="workflow-nodes" style="position: absolute; width: 100%; height: 100%; z-index: 2;"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    this.loadWorkflows();
                }},
                
                loadWorkflows: async function() {{
                    try {{
                        const response = await fetch('/api/workflows');
                        const workflows = await response.json();
                        console.log('Loaded workflows:', workflows);
                    }} catch (error) {{
                        console.error('Failed to load workflows:', error);
                    }}
                }},
                
                addAgent: function(agentType) {{
                    const canvas = document.getElementById('workflow-nodes');
                    const nodeId = 'node-' + Date.now();
                    
                    const nodeElement = document.createElement('div');
                    nodeElement.id = nodeId;
                    nodeElement.style.cssText = `
                        position: absolute;
                        top: 100px;
                        left: 100px;
                        width: 200px;
                        height: 80px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        cursor: move;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        user-select: none;
                        border: 2px solid #4f46e5;
                    `;
                    nodeElement.innerHTML = `
                        <div style="text-align: center;">
                            <div style="font-weight: bold;">${{agentType.replace('-', ' ').toUpperCase()}}</div>
                            <div style="font-size: 12px; opacity: 0.8;">${{nodeId}}</div>
                        </div>
                    `;
                    
                    // Make draggable
                    this.makeDraggable(nodeElement);
                    
                    canvas.appendChild(nodeElement);
                    
                    // Hide empty state
                    const emptyState = canvas.previousElementSibling;
                    if (emptyState) emptyState.style.display = 'none';
                }},
                
                makeDraggable: function(element) {{
                    let isDragging = false;
                    let dragOffset = {{ x: 0, y: 0 }};
                    
                    element.addEventListener('mousedown', (e) => {{
                        isDragging = true;
                        dragOffset.x = e.clientX - element.offsetLeft;
                        dragOffset.y = e.clientY - element.offsetTop;
                        element.style.zIndex = '1000';
                    }});
                    
                    document.addEventListener('mousemove', (e) => {{
                        if (isDragging) {{
                            element.style.left = (e.clientX - dragOffset.x) + 'px';
                            element.style.top = (e.clientY - dragOffset.y) + 'px';
                        }}
                    }});
                    
                    document.addEventListener('mouseup', () => {{
                        if (isDragging) {{
                            isDragging = false;
                            element.style.zIndex = 'auto';
                        }}
                    }});
                }},
                
                createWorkflow: function() {{
                    const name = prompt('Enter workflow name:');
                    if (name) {{
                        alert('Creating workflow: ' + name);
                        // Clear canvas
                        document.getElementById('workflow-nodes').innerHTML = '';
                    }}
                }},
                
                saveWorkflow: function() {{
                    const nodes = document.querySelectorAll('#workflow-nodes > div');
                    if (nodes.length === 0) {{
                        alert('Add some agents to the workflow first!');
                        return;
                    }}
                    alert(`Saving workflow with ${{nodes.length}} nodes`);
                }},
                
                executeWorkflow: function() {{
                    const nodes = document.querySelectorAll('#workflow-nodes > div');
                    if (nodes.length === 0) {{
                        alert('Create a workflow first!');
                        return;
                    }}
                    alert('Executing workflow...');
                }},
                
                validateWorkflow: function() {{
                    const nodes = document.querySelectorAll('#workflow-nodes > div');
                    alert(`Workflow validation: ${{nodes.length}} nodes found`);
                }}
            }};
            
            // Initialize when DOM is ready
            document.addEventListener('DOMContentLoaded', function() {{
                WorkflowEditorComponent.init();
            }});
            
            // Also initialize immediately in case DOM is already loaded
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', WorkflowEditorComponent.init);
            }} else {{
                WorkflowEditorComponent.init();
            }}
        </script>
    </body>
    </html>
    """
    
    # Use Streamlit's HTML component
    return components.html(component_html, height=height, scrolling=False)


def agent_builder(key="agent_builder", height=600):
    """Streamlit component for React AgentBuilder"""
    
    component_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Agent Builder</title>
        <style>
            body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
                    sans-serif;
                background: #f3f4f6;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            .form-label {{
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #374151;
            }}
            .form-input {{
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
            }}
            .form-textarea {{
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                min-height: 120px;
                resize: vertical;
            }}
            .btn {{
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
            }}
            .btn-primary {{
                background: #3b82f6;
                color: white;
            }}
            .btn-secondary {{
                background: #6b7280;
                color: white;
            }}
            .agent-card {{
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 16px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .tool-checkbox {{
                display: flex;
                align-items: center;
                margin-bottom: 8px;
            }}
            .tool-checkbox input {{
                margin-right: 8px;
            }}
        </style>
    </head>
    <body>
        <div style="padding: 20px; height: {height - 40}px; overflow: auto;">
            <div style="max-width: 1200px; margin: 0 auto;">
                <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 30px;">
                    <h2 style="margin: 0; color: #374151;">🤖 Agent Builder</h2>
                    <button onclick="AgentBuilder.showCreateForm()" class="btn btn-primary">
                        Create New Agent
                    </button>
                </div>
                
                <!-- Agent Creation Form (initially hidden) -->
                <div id="agent-form" style="display: none; background: white; padding: 24px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0 0 20px 0;">Create New Agent</h3>
                    
                    <div class="form-group">
                        <label class="form-label">Agent Name</label>
                        <input type="text" id="agent-name" class="form-input" placeholder="Enter agent name...">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <input type="text" id="agent-description" class="form-input" placeholder="Brief description of the agent...">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Instructions</label>
                        <textarea id="agent-instructions" class="form-textarea" placeholder="Detailed instructions for the agent..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Available Tools</label>
                        <div id="tool-checkboxes">
                            <div class="tool-checkbox">
                                <input type="checkbox" id="tool-email" value="email_tool">
                                <label for="tool-email">📧 Email Tool</label>
                            </div>
                            <div class="tool-checkbox">
                                <input type="checkbox" id="tool-slack" value="slack_tool">
                                <label for="tool-slack">💬 Slack Tool</label>
                            </div>
                            <div class="tool-checkbox">
                                <input type="checkbox" id="tool-file" value="file_tool">
                                <label for="tool-file">📁 File Tool</label>
                            </div>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 10px;">
                        <button onclick="AgentBuilder.saveAgent()" class="btn btn-primary">Save Agent</button>
                        <button onclick="AgentBuilder.hideCreateForm()" class="btn btn-secondary">Cancel</button>
                    </div>
                </div>
                
                <!-- Agents List -->
                <div id="agents-list">
                    <div style="text-align: center; padding: 40px; color: #6b7280;">
                        <div style="font-size: 48px; margin-bottom: 16px;">🤖</div>
                        <h3 style="margin: 0 0 8px 0;">No agents created yet</h3>
                        <p style="margin: 0;">Create your first AI agent to get started</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            window.AgentBuilder = {{
                agents: [],
                
                init: function() {{
                    this.loadAgents();
                }},
                
                showCreateForm: function() {{
                    document.getElementById('agent-form').style.display = 'block';
                    document.getElementById('agent-name').focus();
                }},
                
                hideCreateForm: function() {{
                    document.getElementById('agent-form').style.display = 'none';
                    this.clearForm();
                }},
                
                clearForm: function() {{
                    document.getElementById('agent-name').value = '';
                    document.getElementById('agent-description').value = '';
                    document.getElementById('agent-instructions').value = '';
                    document.querySelectorAll('#tool-checkboxes input[type="checkbox"]').forEach(cb => cb.checked = false);
                }},
                
                saveAgent: function() {{
                    const name = document.getElementById('agent-name').value.trim();
                    const description = document.getElementById('agent-description').value.trim();
                    const instructions = document.getElementById('agent-instructions').value.trim();
                    
                    if (!name || !instructions) {{
                        alert('Please fill in the agent name and instructions');
                        return;
                    }}
                    
                    const selectedTools = [];
                    document.querySelectorAll('#tool-checkboxes input[type="checkbox"]:checked').forEach(cb => {{
                        selectedTools.push(cb.value);
                    }});
                    
                    const agent = {{
                        id: 'agent-' + Date.now(),
                        name: name,
                        description: description || 'No description provided',
                        instructions: instructions,
                        mcp_tool_permissions: selectedTools,
                        trigger_conditions: ['manual'],
                        created_at: new Date().toISOString()
                    }};
                    
                    this.agents.push(agent);
                    this.renderAgents();
                    this.hideCreateForm();
                    
                    // Here you would normally save to the backend
                    console.log('Created agent:', agent);
                    alert('Agent created successfully!');
                }},
                
                loadAgents: async function() {{
                    try {{
                        const response = await fetch('/api/agents');
                        this.agents = await response.json() || [];
                        this.renderAgents();
                    }} catch (error) {{
                        console.error('Failed to load agents:', error);
                        this.renderAgents(); // Render empty state
                    }}
                }},
                
                renderAgents: function() {{
                    const container = document.getElementById('agents-list');
                    
                    if (this.agents.length === 0) {{
                        container.innerHTML = `
                            <div style="text-align: center; padding: 40px; color: #6b7280;">
                                <div style="font-size: 48px; margin-bottom: 16px;">🤖</div>
                                <h3 style="margin: 0 0 8px 0;">No agents created yet</h3>
                                <p style="margin: 0;">Create your first AI agent to get started</p>
                            </div>
                        `;
                        return;
                    }}
                    
                    let html = '';
                    this.agents.forEach(agent => {{
                        const toolsHtml = agent.mcp_tool_permissions.length > 0 
                            ? agent.mcp_tool_permissions.map(tool => `<span style="background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-right: 4px;">${{tool.replace('_tool', '')}}</span>`).join('')
                            : '<span style="color: #6b7280;">No tools assigned</span>';
                        
                        html += `
                            <div class="agent-card">
                                <div style="display: flex; justify-content: between; align-items: start; margin-bottom: 12px;">
                                    <div>
                                        <h4 style="margin: 0 0 4px 0; color: #111827;">🤖 ${{agent.name}}</h4>
                                        <p style="margin: 0; color: #6b7280; font-size: 14px;">${{agent.description}}</p>
                                    </div>
                                    <div style="display: flex; gap: 8px;">
                                        <button onclick="AgentBuilder.testAgent('${{agent.id}}')" class="btn" style="background: #10b981; color: white; font-size: 12px; padding: 4px 8px;">Test</button>
                                        <button onclick="AgentBuilder.editAgent('${{agent.id}}')" class="btn" style="background: #f59e0b; color: white; font-size: 12px; padding: 4px 8px;">Edit</button>
                                        <button onclick="AgentBuilder.deleteAgent('${{agent.id}}')" class="btn" style="background: #ef4444; color: white; font-size: 12px; padding: 4px 8px;">Delete</button>
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 12px;">
                                    <strong style="color: #374151;">Instructions:</strong>
                                    <div style="background: #f9fafb; padding: 8px; border-radius: 4px; margin-top: 4px; font-family: monospace; font-size: 12px; color: #374151;">
                                        ${{agent.instructions.substring(0, 200)}}${{agent.instructions.length > 200 ? '...' : ''}}
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 8px;">
                                    <strong style="color: #374151;">Available Tools:</strong><br>
                                    ${{toolsHtml}}
                                </div>
                                
                                <div style="font-size: 12px; color: #6b7280;">
                                    Created: ${{new Date(agent.created_at).toLocaleDateString()}} | ID: ${{agent.id}}
                                </div>
                            </div>
                        `;
                    }});
                    
                    container.innerHTML = html;
                }},
                
                testAgent: function(agentId) {{
                    alert('Testing agent: ' + agentId);
                }},
                
                editAgent: function(agentId) {{
                    alert('Editing agent: ' + agentId);
                }},
                
                deleteAgent: function(agentId) {{
                    if (confirm('Are you sure you want to delete this agent?')) {{
                        this.agents = this.agents.filter(a => a.id !== agentId);
                        this.renderAgents();
                        alert('Agent deleted');
                    }}
                }}
            }};
            
            // Initialize when DOM is ready
            document.addEventListener('DOMContentLoaded', function() {{
                AgentBuilder.init();
            }});
            
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', AgentBuilder.init);
            }} else {{
                AgentBuilder.init();
            }}
        </script>
    </body>
    </html>
    """
    
    return components.html(component_html, height=height, scrolling=False)


def activity_monitor(key="activity_monitor", height=600):
    """Streamlit component for React ActivityMonitor"""
    
    component_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Activity Monitor</title>
        <style>
            body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
                    sans-serif;
                background: #f3f4f6;
            }}
            .activity-item {{
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .activity-header {{
                display: flex;
                justify-content: between;
                align-items: center;
                margin-bottom: 8px;
            }}
            .activity-title {{
                font-weight: 600;
                color: #111827;
                margin: 0;
            }}
            .activity-time {{
                font-size: 12px;
                color: #6b7280;
            }}
            .activity-description {{
                color: #374151;
                margin: 4px 0;
            }}
            .activity-type {{
                display: inline-block;
                background: #dbeafe;
                color: #1e40af;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 500;
            }}
            .status-success {{
                color: #059669;
            }}
            .status-error {{
                color: #dc2626;
            }}
            .filter-bar {{
                background: white;
                padding: 16px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: flex;
                gap: 12px;
                align-items: center;
            }}
            .filter-select {{
                padding: 6px 10px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background: white;
            }}
        </style>
    </head>
    <body>
        <div style="padding: 20px; height: {height - 40}px; overflow: auto;">
            <div style="max-width: 1000px; margin: 0 auto;">
                <h2 style="margin: 0 0 20px 0; color: #374151;">📈 Activity Monitor</h2>
                
                <!-- Filters -->
                <div class="filter-bar">
                    <label style="font-weight: 500; color: #374151;">Filter by type:</label>
                    <select id="activity-type-filter" class="filter-select" onchange="ActivityMonitor.applyFilters()">
                        <option value="all">All Activities</option>
                        <option value="workflow_execution">Workflow Execution</option>
                        <option value="agent_execution">Agent Execution</option>
                        <option value="tool_invocation">Tool Invocation</option>
                    </select>
                    
                    <label style="font-weight: 500; color: #374151;">Status:</label>
                    <select id="activity-status-filter" class="filter-select" onchange="ActivityMonitor.applyFilters()">
                        <option value="all">All</option>
                        <option value="success">Success Only</option>
                        <option value="error">Errors Only</option>
                    </select>
                    
                    <button onclick="ActivityMonitor.refreshActivities()" 
                            style="background: #3b82f6; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">
                        🔄 Refresh
                    </button>
                </div>
                
                <!-- Activities List -->
                <div id="activities-container">
                    <div style="text-align: center; padding: 40px; color: #6b7280;">
                        <div style="font-size: 48px; margin-bottom: 16px;">📈</div>
                        <h3 style="margin: 0 0 8px 0;">Loading activities...</h3>
                        <p style="margin: 0;">Please wait while we fetch the latest activity data</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            window.ActivityMonitor = {{
                activities: [],
                filteredActivities: [],
                
                init: function() {{
                    this.loadActivities();
                    // Auto-refresh every 30 seconds
                    setInterval(() => this.loadActivities(), 30000);
                }},
                
                loadActivities: async function() {{
                    try {{
                        const response = await fetch('http://localhost:8003/api/activities/');
                        this.activities = await response.json() || [];
                        this.applyFilters();
                    }} catch (error) {{
                        console.error('Failed to load activities:', error);
                        this.renderActivities([]);
                    }}
                }},
                
                refreshActivities: function() {{
                    this.loadActivities();
                }},
                
                applyFilters: function() {{
                    const typeFilter = document.getElementById('activity-type-filter').value;
                    const statusFilter = document.getElementById('activity-status-filter').value;
                    
                    this.filteredActivities = this.activities.filter(activity => {{
                        let matchesType = typeFilter === 'all' || activity.type === typeFilter;
                        let matchesStatus = statusFilter === 'all' || 
                                          (statusFilter === 'success' && activity.success !== false) ||
                                          (statusFilter === 'error' && activity.success === false);
                        return matchesType && matchesStatus;
                    }});
                    
                    this.renderActivities(this.filteredActivities);
                }},
                
                renderActivities: function(activities) {{
                    const container = document.getElementById('activities-container');
                    
                    if (activities.length === 0) {{
                        container.innerHTML = `
                            <div style="text-align: center; padding: 40px; color: #6b7280;">
                                <div style="font-size: 48px; margin-bottom: 16px;">📈</div>
                                <h3 style="margin: 0 0 8px 0;">No activities found</h3>
                                <p style="margin: 0;">Activities will appear here as agents and workflows are executed</p>
                            </div>
                        `;
                        return;
                    }}
                    
                    let html = `
                        <div style="margin-bottom: 16px; color: #6b7280; font-size: 14px;">
                            Showing ${{activities.length}} of ${{this.activities.length}} activities
                        </div>
                    `;
                    
                    // Show latest 50 activities
                    activities.slice(0, 50).forEach(activity => {{
                        const statusIcon = activity.success !== false ? '✅' : '❌';
                        const statusClass = activity.success !== false ? 'status-success' : 'status-error';
                        const time = new Date(activity.created_at).toLocaleString();
                        
                        // Generate MCP tool input params display for tool invocations
                        let toolInputParamsHtml = '';
                        if (activity.type === 'tool_invocation' && activity.data) {{
                            const inputParams = activity.data.all_input_params || activity.data.params;
                            if (inputParams && Object.keys(inputParams).length > 0) {{
                                toolInputParamsHtml = `
                                    <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px; margin-top: 12px;">
                                        <h4 style="margin: 0 0 8px 0; color: #1e40af; font-size: 14px; font-weight: 600;">🔧 MCP Tool Input Parameters</h4>
                                        <div style="space-y: 8px;">`;
                                
                                Object.entries(inputParams).forEach(([key, value]) => {{
                                    const valueDisplay = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
                                    const truncatedValue = valueDisplay.length > 200 ? valueDisplay.substring(0, 200) + '...' : valueDisplay;
                                    
                                    toolInputParamsHtml += `
                                        <div style="margin-bottom: 8px;">
                                            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 4px;">
                                                <span style="background: #dbeafe; color: #1e40af; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600;">
                                                    ${{key}}
                                                </span>
                                                <span style="font-size: 11px; color: #3b82f6;">
                                                    ${{typeof value}} (${{String(value).length}} chars)
                                                </span>
                                            </div>
                                            <div style="background: white; padding: 6px; border-radius: 4px; border: 1px solid #e0e7ff; font-size: 12px; font-family: monospace; color: #374151; white-space: pre-wrap; overflow-x: auto;">
                                                ${{truncatedValue}}
                                            </div>
                                        </div>
                                    `;
                                }});
                                
                                // Add metadata if available
                                if (activity.data.input_params_detailed) {{
                                    toolInputParamsHtml += `
                                        <div style="border-top: 1px solid #bfdbfe; padding-top: 8px; margin-top: 8px;">
                                            <div style="display: flex; flex-wrap: wrap; gap: 4px; font-size: 11px;">
                                                <span style="background: #dbeafe; color: #1e40af; padding: 2px 6px; border-radius: 4px;">
                                                    ${{activity.data.input_params_detailed.param_count}} parameters
                                                </span>
                                                ${{activity.data.input_params_detailed.has_sensitive_data ? 
                                                    '<span style="background: #fef2f2; color: #dc2626; padding: 2px 6px; border-radius: 4px;">⚠️ Contains sensitive data</span>' : ''}}
                                                ${{activity.data.action ? 
                                                    `<span style="background: #dcfce7; color: #16a34a; padding: 2px 6px; border-radius: 4px;">Action: ${{activity.data.action}}</span>` : ''}}
                                            </div>
                                        </div>
                                    `;
                                }}
                                
                                toolInputParamsHtml += `
                                        </div>
                                    </div>
                                `;
                            }}
                        }}
                        
                        // Generate tool result display
                        let toolResultHtml = '';
                        if (activity.type === 'tool_invocation' && activity.data) {{
                            const result = activity.data.execution_result || activity.data.result;
                            if (result) {{
                                const resultDisplay = typeof result === 'object' ? JSON.stringify(result, null, 2) : String(result);
                                const truncatedResult = resultDisplay.length > 200 ? resultDisplay.substring(0, 200) + '...' : resultDisplay;
                                
                                toolResultHtml = `
                                    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px; margin-top: 12px;">
                                        <h4 style="margin: 0 0 8px 0; color: #15803d; font-size: 14px; font-weight: 600;">📤 Tool Execution Result</h4>
                                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #d4f1d4; font-size: 12px; font-family: monospace; color: #374151; white-space: pre-wrap; overflow-x: auto;">
                                            ${{truncatedResult}}
                                        </div>
                                        ${{activity.data.result_metadata ? `
                                            <div style="border-top: 1px solid #bbf7d0; padding-top: 8px; margin-top: 8px;">
                                                <div style="display: flex; flex-wrap: wrap; gap: 4px; font-size: 11px;">
                                                    <span style="background: #dcfce7; color: #16a34a; padding: 2px 6px; border-radius: 4px;">
                                                        Type: ${{activity.data.result_metadata.result_type}}
                                                    </span>
                                                    <span style="background: #dcfce7; color: #16a34a; padding: 2px 6px; border-radius: 4px;">
                                                        Size: ${{activity.data.result_metadata.result_size}} chars
                                                    </span>
                                                    ${{activity.data.result_metadata.result_is_dict && activity.data.result_metadata.result_keys ? 
                                                        `<span style="background: #dcfce7; color: #16a34a; padding: 2px 6px; border-radius: 4px;">Keys: ${{activity.data.result_metadata.result_keys.join(', ')}}</span>` : ''}}
                                                </div>
                                            </div>
                                        ` : ''}}
                                    </div>
                                `;
                            }}
                        }}
                        
                        html += `
                            <div class="activity-item">
                                <div class="activity-header">
                                    <h4 class="activity-title">
                                        ${{statusIcon}} ${{activity.title}}
                                    </h4>
                                    <div class="activity-time">${{time}}</div>
                                </div>
                                
                                <div class="activity-description">${{activity.description}}</div>
                                
                                <div style="margin: 8px 0; display: flex; gap: 8px; align-items: center;">
                                    <span class="activity-type">${{activity.type.replace('_', ' ').toUpperCase()}}</span>
                                    <span class="${{statusClass}}" style="font-weight: 500;">
                                        ${{activity.success !== false ? 'SUCCESS' : 'ERROR'}}
                                    </span>
                                </div>
                                
                                ${{activity.error ? `<div style="background: #fef2f2; color: #dc2626; padding: 8px; border-radius: 4px; margin-top: 8px; font-size: 14px;">Error: ${{activity.error}}</div>` : ''}}
                                
                                ${{toolInputParamsHtml}}
                                ${{toolResultHtml}}
                                
                                <div style="font-size: 12px; color: #6b7280; margin-top: 8px;">
                                    ${{activity.agent_id ? `Agent: ${{activity.agent_id}} | ` : ''}}
                                    ${{activity.workflow_id ? `Workflow: ${{activity.workflow_id}} | ` : ''}}
                                    ${{activity.tool_id ? `Tool: ${{activity.tool_id}} | ` : ''}}
                                    ID: ${{activity.id}}
                                </div>
                                
                                ${{Object.keys(activity.data || {{}}).length > 0 ? `
                                    <details style="margin-top: 12px;">
                                        <summary style="font-size: 12px; color: #6b7280; cursor: pointer; padding: 4px 0;">
                                            ${{activity.type === 'tool_invocation' ? 'View all technical details' : 'View details'}}
                                        </summary>
                                        <pre style="background: #f9fafb; padding: 8px; border-radius: 4px; margin-top: 4px; font-size: 11px; overflow-x: auto; white-space: pre-wrap;">
${{JSON.stringify(activity.data, null, 2)}}
                                        </pre>
                                    </details>
                                ` : ''}}
                            </div>
                        `;
                    }});
                    
                    container.innerHTML = html;
                }}
            }};
            
            // Initialize when DOM is ready
            document.addEventListener('DOMContentLoaded', function() {{
                ActivityMonitor.init();
            }});
            
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', ActivityMonitor.init);
            }} else {{
                ActivityMonitor.init();
            }}
        </script>
    </body>
    </html>
    """
    
    return components.html(component_html, height=height, scrolling=False)