"""Backend-integrated agent builder with full API connectivity"""
import streamlit.components.v1 as components

def agent_builder_integrated(key="agent_builder_integrated", height=700):
    """Backend-integrated Streamlit agent builder"""
    
    component_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Backend-Integrated Agent Builder</title>
        <style>
            body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                background: #f3f4f6;
            }}
            #agent-root {{ width: 100%; height: {height - 40}px; overflow: auto; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-label {{ display: block; margin-bottom: 5px; font-weight: 600; color: #374151; }}
            .form-input {{ width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }}
            .form-textarea {{ width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; min-height: 120px; resize: vertical; }}
            .btn {{ padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500; }}
            .btn-primary {{ background: #3b82f6; color: white; }}
            .btn-secondary {{ background: #6b7280; color: white; }}
            .btn-success {{ background: #10b981; color: white; }}
            .btn-danger {{ background: #ef4444; color: white; }}
            .agent-card {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .tool-checkbox {{ display: flex; align-items: center; margin-bottom: 8px; }}
            .tool-checkbox input {{ margin-right: 8px; }}
            .success-message, .error-message {{ 
                position: fixed; top: 20px; right: 20px; z-index: 10000;
                padding: 12px 16px; border-radius: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                max-width: 300px; font-size: 13px;
            }}
            .success-message {{ background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }}
            .error-message {{ background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }}
        </style>
    </head>
    <body>
        <div id="agent-root">
            <div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                    <h2 style="margin: 0; color: #374151;">🤖 Backend-Integrated Agent Builder</h2>
                    <div>
                        <button onclick="AgentBuilder.refreshAgents()" class="btn btn-secondary" style="margin-right: 10px;">
                            🔄 Refresh
                        </button>
                        <button onclick="AgentBuilder.showCreateForm()" class="btn btn-primary">
                            Create New Agent
                        </button>
                    </div>
                </div>
                
                <!-- Agent Creation Form (initially hidden) -->
                <div id="agent-form" style="display: none; background: white; padding: 24px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0 0 20px 0;">Create New Agent</h3>
                    
                    <div class="form-group">
                        <label class="form-label">Agent Name *</label>
                        <input type="text" id="agent-name" class="form-input" placeholder="Enter agent name..." required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <input type="text" id="agent-description" class="form-input" placeholder="Brief description of the agent...">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Instructions *</label>
                        <textarea id="agent-instructions" class="form-textarea" placeholder="Detailed instructions for the agent..." required></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Available Tools</label>
                        <div id="tool-checkboxes">
                            <div class="tool-checkbox">
                                <input type="checkbox" id="tool-email" value="email_tool">
                                <label for="tool-email">📧 Email Tool - Send and read emails</label>
                            </div>
                            <div class="tool-checkbox">
                                <input type="checkbox" id="tool-slack" value="slack_tool">
                                <label for="tool-slack">💬 Slack Tool - Post and read Slack messages</label>
                            </div>
                            <div class="tool-checkbox">
                                <input type="checkbox" id="tool-file" value="file_tool">
                                <label for="tool-file">📁 File Tool - Read, write, and list files</label>
                            </div>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 10px;">
                        <button onclick="AgentBuilder.saveAgent()" class="btn btn-success">💾 Save Agent</button>
                        <button onclick="AgentBuilder.hideCreateForm()" class="btn btn-secondary">Cancel</button>
                    </div>
                </div>
                
                <!-- Agents List -->
                <div id="agents-list">
                    <div style="text-align: center; padding: 40px; color: #6b7280;">
                        <div style="font-size: 48px; margin-bottom: 16px;">⏳</div>
                        <h3 style="margin: 0 0 8px 0;">Loading agents...</h3>
                        <p style="margin: 0;">Please wait while we fetch your agents from the backend</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            window.AgentBuilder = {{
                agents: [],
                apiBase: 'http://localhost:8003/api',
                
                init: function() {{
                    console.log('Backend-Integrated Agent Builder initialized');
                    this.loadAgents();
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
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-message';
                    errorDiv.textContent = message;
                    document.body.appendChild(errorDiv);
                    setTimeout(() => errorDiv.remove(), 5000);
                }},
                
                showSuccess: function(message) {{
                    const successDiv = document.createElement('div');
                    successDiv.className = 'success-message';
                    successDiv.textContent = message;
                    document.body.appendChild(successDiv);
                    setTimeout(() => successDiv.remove(), 3000);
                }},
                
                // Data Loading
                async loadAgents() {{
                    const agents = await this.apiCall('/agents');
                    if (agents) {{
                        this.agents = agents;
                        this.renderAgents();
                    }}
                }},
                
                refreshAgents: function() {{
                    this.loadAgents();
                }},
                
                // Form Management
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
                
                // Agent Management
                async saveAgent() {{
                    const name = document.getElementById('agent-name').value.trim();
                    const description = document.getElementById('agent-description').value.trim();
                    const instructions = document.getElementById('agent-instructions').value.trim();
                    
                    if (!name || !instructions) {{
                        this.showError('Please fill in the agent name and instructions');
                        return;
                    }}
                    
                    const selectedTools = [];
                    document.querySelectorAll('#tool-checkboxes input[type="checkbox"]:checked').forEach(cb => {{
                        selectedTools.push(cb.value);
                    }});
                    
                    const agentData = {{
                        name: name,
                        description: description || 'No description provided',
                        instructions: instructions,
                        mcp_tool_permissions: selectedTools,
                        trigger_conditions: ['manual']
                    }};
                    
                    const savedAgent = await this.apiCall('/agents', {{
                        method: 'POST',
                        body: JSON.stringify(agentData)
                    }});
                    
                    if (savedAgent) {{
                        this.agents.push(savedAgent);
                        this.renderAgents();
                        this.hideCreateForm();
                        this.showSuccess(`Agent "${{savedAgent.name}}" created successfully!`);
                        console.log('Created agent:', savedAgent);
                    }}
                }},
                
                async deleteAgent(agentId) {{
                    if (!confirm('Are you sure you want to delete this agent?')) {{
                        return;
                    }}
                    
                    const result = await this.apiCall(`/agents/${{agentId}}`, {{
                        method: 'DELETE'
                    }});
                    
                    if (result !== null) {{ // DELETE might return empty response
                        this.agents = this.agents.filter(a => a.id !== agentId);
                        this.renderAgents();
                        this.showSuccess('Agent deleted successfully');
                    }}
                }},
                
                async testAgent(agentId) {{
                    const agent = this.agents.find(a => a.id === agentId);
                    if (!agent) return;
                    
                    // Simple test - just show agent details
                    const testPrompt = prompt(`Test agent "${{agent.name}}" with a message:`, 'Hello, please introduce yourself.');
                    if (!testPrompt) return;
                    
                    this.showSuccess(`Testing agent "${{agent.name}}" - check the Activities tab for results`);
                    console.log(`Testing agent ${{agentId}} with prompt:`, testPrompt);
                    
                    // In a real implementation, you might execute the agent with a test workflow
                }},
                
                editAgent: function(agentId) {{
                    // For now, just show agent details
                    const agent = this.agents.find(a => a.id === agentId);
                    if (!agent) return;
                    
                    alert(`Edit Agent: ${{agent.name}}\\n\\nID: ${{agent.id}}\\nDescription: ${{agent.description}}\\n\\nEdit functionality coming soon!`);
                }},
                
                // Rendering
                renderAgents: function() {{
                    const container = document.getElementById('agents-list');
                    
                    if (this.agents.length === 0) {{
                        container.innerHTML = `
                            <div style="text-align: center; padding: 40px; color: #6b7280;">
                                <div style="font-size: 48px; margin-bottom: 16px;">🤖</div>
                                <h3 style="margin: 0 0 8px 0;">No agents found</h3>
                                <p style="margin: 0;">Create your first AI agent to get started</p>
                            </div>
                        `;
                        return;
                    }}
                    
                    let html = `
                        <div style="margin-bottom: 20px;">
                            <h3 style="margin: 0 0 10px 0; color: #374151;">Your Agents (${{this.agents.length}})</h3>
                            <p style="margin: 0; color: #6b7280; font-size: 14px;">Manage your AI agents and their configurations</p>
                        </div>
                    `;
                    
                    this.agents.forEach(agent => {{
                        const toolsHtml = agent.mcp_tool_permissions && agent.mcp_tool_permissions.length > 0
                            ? agent.mcp_tool_permissions.map(tool => {{
                                const toolName = tool.replace('_tool', '');
                                const emoji = toolName === 'email' ? '📧' : toolName === 'slack' ? '💬' : '📁';
                                return `<span style="background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px;">${{emoji}} ${{toolName}}</span>`;
                            }}).join('')
                            : '<span style="color: #6b7280;">No tools assigned</span>';
                        
                        const createdDate = agent.created_at ? new Date(agent.created_at).toLocaleDateString() : 'Unknown';
                        
                        html += `
                            <div class="agent-card">
                                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                                    <div>
                                        <h4 style="margin: 0 0 4px 0; color: #111827;">🤖 ${{agent.name}}</h4>
                                        <p style="margin: 0; color: #6b7280; font-size: 14px;">${{agent.description || 'No description'}}</p>
                                    </div>
                                    <div style="display: flex; gap: 8px;">
                                        <button onclick="AgentBuilder.testAgent('${{agent.id}}')" 
                                                class="btn btn-success" 
                                                style="font-size: 12px; padding: 4px 8px;">
                                            Test
                                        </button>
                                        <button onclick="AgentBuilder.editAgent('${{agent.id}}')" 
                                                class="btn btn-secondary" 
                                                style="font-size: 12px; padding: 4px 8px;">
                                            Edit
                                        </button>
                                        <button onclick="AgentBuilder.deleteAgent('${{agent.id}}')" 
                                                class="btn btn-danger" 
                                                style="font-size: 12px; padding: 4px 8px;">
                                            Delete
                                        </button>
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 12px;">
                                    <strong style="color: #374151;">Instructions:</strong>
                                    <div style="background: #f9fafb; padding: 8px; border-radius: 4px; margin-top: 4px; font-family: monospace; font-size: 12px; color: #374151; max-height: 100px; overflow-y: auto;">
                                        ${{agent.instructions}}
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 8px;">
                                    <strong style="color: #374151;">Available Tools:</strong><br>
                                    <div style="margin-top: 4px;">${{toolsHtml}}</div>
                                </div>
                                
                                <div style="font-size: 12px; color: #6b7280;">
                                    Created: ${{createdDate}} | ID: ${{agent.id}}
                                </div>
                            </div>
                        `;
                    }});
                    
                    container.innerHTML = html;
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