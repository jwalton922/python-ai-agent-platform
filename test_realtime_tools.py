#!/usr/bin/env python3
"""
Test script to demonstrate real-time tool call display in async chat
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_realtime_tool_display():
    """Test that tool calls appear in real-time during async chat"""
    
    async with aiohttp.ClientSession() as session:
        print("=" * 60)
        print("REAL-TIME TOOL CALL DISPLAY TEST")
        print("=" * 60)
        print(f"Testing against: {BASE_URL}")
        print(f"Started at: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Get agents
        print("1. Getting agents...")
        async with session.get(f"{BASE_URL}/api/agents/") as resp:
            if resp.status != 200:
                print(f"❌ Failed to get agents: {resp.status}")
                return
            agents = await resp.json()
            
            # Find an agent with email_tool permission
            email_agent = None
            for agent in agents:
                if 'email_tool' in agent.get('mcp_tool_permissions', []):
                    email_agent = agent
                    break
            
            if not email_agent:
                print("❌ No agent found with email_tool permission")
                print("   Creating an email agent...")
                
                # Create email agent
                async with session.post(
                    f"{BASE_URL}/api/agents/",
                    json={
                        "name": "Email Test Agent",
                        "instructions": "You help users send emails. Always use the email tool when asked to send emails.",
                        "mcp_tool_permissions": ["email_tool"]
                    }
                ) as resp:
                    if resp.status == 200:
                        email_agent = await resp.json()
                        print(f"   ✅ Created email agent: {email_agent['name']}")
                    else:
                        print(f"   ❌ Failed to create agent: {resp.status}")
                        return
            else:
                print(f"   ✅ Found email agent: {email_agent['name']}")
        
        # Start async chat requesting an email
        print("\n2. Starting async chat with email request...")
        chat_data = {
            "agent_id": email_agent["id"],
            "message": "Please send an email to test@example.com with subject 'Test Email' and body 'This is a test email from the async chat system'",
            "chat_history": []
        }
        
        async with session.post(
            f"{BASE_URL}/api/chat/async",
            json=chat_data
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                print(f"❌ Failed to start async chat: {resp.status}")
                print(f"   Error: {error_text}")
                return
            
            async_response = await resp.json()
            chat_id = async_response["chat_id"]
            print(f"   ✅ Chat started: {chat_id}")
        
        # Poll for status and show real-time tool updates
        print("\n3. Polling for real-time tool execution updates...")
        print("   Watching for tool calls to appear before completion...")
        
        max_polls = 20
        poll_count = 0
        tool_calls_seen = []
        
        while poll_count < max_polls:
            await asyncio.sleep(1)
            poll_count += 1
            
            async with session.get(f"{BASE_URL}/api/chat/async/{chat_id}/status") as resp:
                if resp.status != 200:
                    print(f"❌ Failed to get status: {resp.status}")
                    break
                
                status_data = await resp.json()
                
                # Look for new tool calls in progress
                if status_data["progress"]:
                    for step in status_data["progress"]:
                        if "tool_call" in step:
                            tool_call = step["tool_call"]
                            tool_key = f"{tool_call['tool']}-{tool_call['action']}-{step['type']}"
                            
                            if tool_key not in tool_calls_seen:
                                tool_calls_seen.append(tool_key)
                                
                                if step["type"] == "tool_execution_start":
                                    print(f"   📧 TOOL STARTED: {tool_call['tool']} - {tool_call['action']}")
                                    print(f"      Params: {tool_call['params']}")
                                elif step["type"] == "tool_execution_complete":
                                    print(f"   ✅ TOOL COMPLETED: {tool_call['tool']} - {tool_call['action']}")
                                    print(f"      Result: {tool_call['result']}")
                                elif step["type"] == "tool_execution_error":
                                    print(f"   ❌ TOOL FAILED: {tool_call['tool']} - {tool_call['action']}")
                                    print(f"      Error: {tool_call['error']}")
                
                # Show general progress
                if status_data["progress"]:
                    latest_step = status_data["progress"][-1]
                    if "tool_call" not in latest_step:
                        print(f"   [{poll_count}s] {latest_step['message']}")
                
                # Check completion
                if status_data["status"] == "completed":
                    print(f"\n4. ✅ Chat completed!")
                    break
                elif status_data["status"] == "failed":
                    print(f"\n4. ❌ Chat failed: {status_data.get('error')}")
                    break
                elif status_data["status"] == "timeout":
                    print(f"\n4. ⏰ Chat timed out")
                    break
        
        else:
            print(f"\n4. ⏰ Test timed out after {max_polls} seconds")
        
        # Summary
        print(f"\n5. Summary:")
        print(f"   Tool calls detected: {len([k for k in tool_calls_seen if 'start' in k])}")
        print(f"   Tool completions: {len([k for k in tool_calls_seen if 'complete' in k])}")
        print(f"   Tool errors: {len([k for k in tool_calls_seen if 'error' in k])}")
        
        if len([k for k in tool_calls_seen if 'start' in k]) > 0:
            print("   ✅ SUCCESS: Tool calls appeared in real-time!")
        else:
            print("   ❌ ISSUE: No tool calls detected in progress")
        
        # Cleanup
        try:
            await session.delete(f"{BASE_URL}/api/chat/async/{chat_id}")
        except:
            pass

async def main():
    """Run the test"""
    await test_realtime_tool_display()
    
    print("\n" + "=" * 60)
    print("UI TESTING INSTRUCTIONS")
    print("=" * 60)
    print("To test in the UI:")
    print("1. Go to http://localhost:3000 or http://localhost:8000/app")
    print("2. Navigate to Agent Chat")
    print("3. Select an agent with email_tool permission")
    print("4. Toggle to 'Async' mode (purple button)")
    print("5. Send: 'Please send an email to test@example.com'")
    print("6. Watch for:")
    print("   - Yellow box appears immediately (tool starting)")
    print("   - After ~6 seconds, yellow becomes green (tool completed)")
    print("   - Parameters and results are shown in expandable sections")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())