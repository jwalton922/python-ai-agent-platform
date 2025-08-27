"""
Agent-Workflow Integration Module
Allows agents to create workflows through the chat interface
"""

from typing import Dict, Any, Optional
import re
from backend.storage.file_storage import file_storage as storage


async def detect_workflow_request(message: str) -> bool:
    """
    Detect if a message is requesting workflow creation
    
    Returns True if the message contains workflow creation keywords
    """
    workflow_keywords = [
        'create workflow',
        'generate workflow',
        'build workflow',
        'make a workflow',
        'design workflow',
        'workflow that',
        'workflow to',
        'workflow for'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in workflow_keywords)


def extract_workflow_instructions(message: str) -> str:
    """
    Extract workflow instructions from a chat message
    
    Returns cleaned instructions for workflow generation
    """
    # Remove common prefixes
    patterns = [
        r'(?i)^(please\s+)?create\s+(a\s+)?workflow\s+(that\s+|to\s+|for\s+)?',
        r'(?i)^(please\s+)?generate\s+(a\s+)?workflow\s+(that\s+|to\s+|for\s+)?',
        r'(?i)^(please\s+)?build\s+(a\s+)?workflow\s+(that\s+|to\s+|for\s+)?',
        r'(?i)^(please\s+)?make\s+(a\s+)?workflow\s+(that\s+|to\s+|for\s+)?',
        r'(?i)^(please\s+)?design\s+(a\s+)?workflow\s+(that\s+|to\s+|for\s+)?',
    ]
    
    instructions = message
    for pattern in patterns:
        instructions = re.sub(pattern, '', instructions)
    
    # Clean up any remaining artifacts
    instructions = instructions.strip()
    if not instructions:
        instructions = message  # Fall back to original if nothing remains
    
    return instructions


async def enhance_agent_for_workflow_creation(agent_id: str) -> Dict[str, Any]:
    """
    Enhance an agent's instructions to handle workflow creation
    
    Returns the updated agent configuration
    """
    agent = storage.get_agent(agent_id)
    if not agent:
        return {"error": "Agent not found"}
    
    # Check if agent already has workflow creation instructions
    if 'workflow creation' in agent.instructions.lower():
        return {"message": "Agent already has workflow creation capabilities"}
    
    # Enhance instructions
    workflow_instructions = """

WORKFLOW CREATION CAPABILITY:
When a user asks you to create or generate a workflow, follow these steps:
1. Understand the workflow requirements from the user's request
2. Identify the key tasks and their sequence
3. Determine which agents or tools are needed for each task
4. Create a structured workflow with appropriate nodes and connections
5. Return the workflow configuration in a clear format

Example workflow creation triggers:
- "Create a workflow that..."
- "Generate a workflow for..."
- "Build a workflow to..."
- "Make a workflow that can..."

When creating workflows, consider:
- Breaking down complex tasks into smaller nodes
- Using appropriate node types (agent, decision, loop, parallel, etc.)
- Setting proper error handling and retry strategies
- Defining clear input and output variables
- Adding meaningful descriptions for each node
"""
    
    # Update agent instructions
    updated_instructions = agent.instructions + workflow_instructions
    
    # Store the update (this would normally update the agent in storage)
    # For now, return the enhanced configuration
    return {
        "agent_id": agent_id,
        "enhanced": True,
        "workflow_creation_enabled": True,
        "instructions_preview": workflow_instructions[:200] + "..."
    }


async def process_workflow_generation_response(
    agent_response: str,
    original_instructions: str,
    agent_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process an agent's response that might contain workflow configuration
    
    Returns workflow data if found, or original response
    """
    # Check if response contains JSON workflow structure
    import json
    
    try:
        # Look for JSON block in response
        json_match = re.search(r'\{[\s\S]*\}', agent_response)
        if json_match:
            workflow_data = json.loads(json_match.group(0))
            
            # Validate it looks like a workflow
            if 'nodes' in workflow_data or 'name' in workflow_data:
                return {
                    "type": "workflow_generated",
                    "workflow_data": workflow_data,
                    "instructions": original_instructions,
                    "agent_id": agent_id,
                    "message": "I've created a workflow based on your requirements. You can now save and use this workflow."
                }
    except json.JSONDecodeError:
        pass
    
    # Return original response if no workflow found
    return {
        "type": "chat_response",
        "message": agent_response
    }