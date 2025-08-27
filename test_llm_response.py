#!/usr/bin/env python3
"""
Test the LLM response generation to debug JSON parsing
"""

import asyncio
import sys
import os
import json
import re

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.llm.factory import LLMFactory
from backend.llm.base import LLMMessage, LLMRole

async def test_llm_response():
    """Test LLM response generation and JSON parsing"""
    
    print("🧪 Testing LLM response generation...")
    
    # Create the same prompt that the workflow tool uses
    instructions = "Create a workflow to categorize customer email by sentiment. If the sentiment is negative and the customer is high value, send me a slack message. Summarize all other customer emails by the sentiment"
    
    # Get available agents
    from backend.storage.file_storage import file_storage as storage
    agents = storage.list_agents()
    available_agents = [
        {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "capabilities": agent.mcp_tool_permissions
        }
        for agent in agents
    ]
    
    agents_info = ""
    if available_agents:
        agents_list = "\n".join([
            f"- {agent['name']} (ID: {agent['id']}): {agent.get('description', 'No description')}"
            for agent in available_agents
        ])
        agents_info = f"\nAvailable agents for the workflow:\n{agents_list}"
    
    prompt = f"""Generate a detailed, multi-node workflow structure based on the following instructions:

Instructions: {instructions}
{agents_info}

IMPORTANT: Create a comprehensive workflow with multiple nodes and proper flow control. Break down complex tasks into separate nodes.

Node Types and When to Use:
- "agent": Use for AI processing tasks (sentiment analysis, summarization, etc.)
- "decision": Use for conditional logic and branching (if sentiment is negative, if customer is high value, etc.)
- "transform": Use for data transformation, filtering, or formatting
- "loop": Use for processing multiple items (each email, each customer, etc.)
- "parallel": Use when tasks can run simultaneously
- "storage": Use for saving/retrieving data
- "aggregator": Use for combining results from multiple sources

External Triggers (add to trigger_conditions):
- For "once a day": ["schedule:daily"]
- For "when email comes in": ["email:received"]
- For "when file uploaded": ["file:uploaded"]
- For "webhook": ["webhook:received"]

Please provide a JSON structure with the following format:
{{
    "name": "Workflow name",
    "description": "Brief description",
    "trigger_conditions": ["trigger1", "trigger2"],
    "nodes": [
        {{
            "id": "unique_id",
            "type": "agent|decision|transform|loop|parallel|storage|aggregator",
            "name": "Node name",
            "description": "Node description",
            "agent_id": "agent_id (if type is agent)",
            "instructions": "Specific instructions for this node",
            "condition_expression": "condition for decision nodes",
            "branches": [
                {{"name": "positive", "condition": "sentiment == 'positive'", "target": "positive_handler"}},
                {{"name": "negative", "condition": "sentiment == 'negative'", "target": "negative_handler"}}
            ],
            "config": {{
                "timeout_ms": 30000,
                "error_handling": "fail|continue|fallback"
            }}
        }}
    ],
    "edges": [
        {{
            "source": "source_node_id",
            "target": "target_node_id",
            "condition": "optional condition (e.g., sentiment == 'negative' && customer_value == 'high')"
        }}
    ],
    "variables": [
        {{
            "name": "variable_name",
            "type": "string|number|boolean|object|array",
            "required": true,
            "default": null,
            "description": "Variable description"
        }}
    ]
}}

EXAMPLE for email sentiment analysis:
1. Start with a trigger node or email input
2. Create an agent node for sentiment analysis
3. Add a decision node to check sentiment
4. Create separate branches for positive/negative sentiment
5. Add another decision node for customer value (if negative)
6. Create specific action nodes (slack message, summary generation)
7. Connect all nodes with proper edges and conditions

Generate a complete, multi-node workflow structure that accomplishes: {instructions}"""
    
    print(f"🔧 Creating LLM provider...")
    llm_provider = LLMFactory.create_provider("mock_anthropic")
    
    print(f"🔧 Sending prompt to LLM...")
    messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
    response = await llm_provider.generate(messages)
    
    print(f"📝 LLM Response Length: {len(response.content)}")
    print(f"📝 First 500 chars: {response.content[:500]}...")
    
    # Try to parse JSON like the workflow tool does
    print(f"\n🔧 Testing JSON extraction...")
    json_match = re.search(r'\{[\s\S]*\}', response.content)
    if json_match:
        json_str = json_match.group(0)
        print(f"✅ Found JSON block (length: {len(json_str)})")
        
        try:
            parsed_data = json.loads(json_str)
            print(f"✅ JSON parsing successful!")
            print(f"   Name: {parsed_data.get('name')}")
            print(f"   Nodes: {len(parsed_data.get('nodes', []))}")
            print(f"   Edges: {len(parsed_data.get('edges', []))}")
            print(f"   Triggers: {parsed_data.get('trigger_conditions', [])}")
            
            # Show node details
            for i, node in enumerate(parsed_data.get('nodes', [])):
                print(f"   Node {i+1}: {node.get('name')} ({node.get('type')})")
                
            return parsed_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"🔍 Raw JSON: {json_str[:1000]}...")
    else:
        print(f"❌ No JSON block found in response")
        print(f"🔍 Full response: {response.content}")
    
    return None

if __name__ == "__main__":
    result = asyncio.run(test_llm_response())
    if result:
        print(f"\n🎉 Successfully parsed workflow with {len(result.get('nodes', []))} nodes!")
    else:
        print(f"\n❌ Failed to parse workflow data")