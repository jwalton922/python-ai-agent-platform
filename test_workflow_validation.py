#!/usr/bin/env python3
"""
Direct test of workflow creation to debug validation issues
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.mcp.tools.workflow_tool import workflow_tool

async def test_workflow_creation():
    """Test complex workflow creation and capture all debug output"""
    
    print("🧪 Starting workflow validation test...")
    
    # Test parameters that should trigger complex workflow generation
    test_params = {
        "action": "create",
        "instructions": "Create a workflow to categorize customer email by sentiment. If the sentiment is negative and the customer is high value, send me a slack message. Summarize all other customer emails by the sentiment",
        "workflow_name": "Validation Test Workflow",
        "use_available_agents": True
    }
    
    try:
        print("🔧 Calling workflow tool...")
        result = await workflow_tool.execute(test_params)
        
        print(f"\n📋 Result Summary:")
        print(f"   Success: {result.get('success')}")
        if result.get('success'):
            print(f"   Workflow ID: {result.get('workflow_id')}")
            print(f"   Node Count: {result.get('node_count')}")
            print(f"   Edge Count: {result.get('edge_count')}")
        else:
            print(f"   Error: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow_creation())