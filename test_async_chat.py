#!/usr/bin/env python3
"""
Test script for async chat functionality
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_async_chat():
    """Test the async chat flow"""
    
    # First, get list of agents to find a valid agent ID
    async with aiohttp.ClientSession() as session:
        print("1. Getting list of agents...")
        async with session.get(f"{BASE_URL}/api/agents/") as resp:
            if resp.status != 200:
                print(f"Failed to get agents: {resp.status}")
                return
            agents = await resp.json()
            
            if not agents:
                print("No agents found. Please create an agent first.")
                return
            
            agent_id = agents[0]["id"]
            agent_name = agents[0]["name"]
            print(f"   Using agent: {agent_name} ({agent_id})")
        
        # Start async chat
        print("\n2. Starting async chat...")
        chat_data = {
            "agent_id": agent_id,
            "message": "Hello, this is a test of async chat. What can you help me with?",
            "chat_history": []
        }
        
        async with session.post(
            f"{BASE_URL}/api/chat/async",
            json=chat_data,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                print(f"Failed to start async chat: {resp.status}")
                print(f"Error: {error_text}")
                return
            
            async_response = await resp.json()
            chat_id = async_response["chat_id"]
            print(f"   Chat ID: {chat_id}")
            print(f"   Status: {async_response['status']}")
            print(f"   Message: {async_response['message']}")
        
        # Poll for status
        print("\n3. Polling for results...")
        max_polls = 30  # 30 seconds max
        poll_count = 0
        
        while poll_count < max_polls:
            await asyncio.sleep(1)  # Wait 1 second between polls
            poll_count += 1
            
            async with session.get(f"{BASE_URL}/api/chat/async/{chat_id}/status") as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"Failed to get status: {resp.status}")
                    print(f"Error: {error_text}")
                    return
                
                status_data = await resp.json()
                
                # Show progress
                if status_data["progress"]:
                    latest_progress = status_data["progress"][-1]
                    print(f"   [{poll_count}s] {latest_progress['type']}: {latest_progress['message']}")
                
                # Check if completed
                if status_data["status"] == "completed":
                    print(f"\n4. Chat completed successfully!")
                    if status_data["result"]:
                        print(f"   Response: {status_data['result']['message'][:200]}...")
                        if status_data['result'].get('tool_calls'):
                            print(f"   Tool calls: {len(status_data['result']['tool_calls'])}")
                    break
                
                elif status_data["status"] == "failed":
                    print(f"\n4. Chat failed!")
                    print(f"   Error: {status_data.get('error', 'Unknown error')}")
                    break
                
                elif status_data["status"] == "timeout":
                    print(f"\n4. Chat timed out!")
                    break
        
        else:
            print(f"\n4. Polling timeout after {max_polls} seconds")
        
        # Cleanup
        print("\n5. Cleaning up chat session...")
        async with session.delete(f"{BASE_URL}/api/chat/async/{chat_id}") as resp:
            if resp.status == 200:
                cleanup_result = await resp.json()
                print(f"   {cleanup_result['message']}")
            else:
                print(f"   Cleanup failed: {resp.status}")

async def test_sync_vs_async():
    """Compare sync and async chat performance"""
    
    async with aiohttp.ClientSession() as session:
        # Get first agent
        async with session.get(f"{BASE_URL}/api/agents/") as resp:
            agents = await resp.json()
            if not agents:
                print("No agents found")
                return
            agent_id = agents[0]["id"]
        
        # Test sync chat
        print("Testing SYNC chat...")
        start = time.time()
        async with session.post(
            f"{BASE_URL}/api/chat/",
            json={
                "agent_id": agent_id,
                "message": "Hello sync",
                "chat_history": []
            },
            timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            sync_time = time.time() - start
            if resp.status == 200:
                result = await resp.json()
                print(f"  Sync completed in {sync_time:.2f}s")
            else:
                print(f"  Sync failed: {resp.status}")
        
        # Test async chat
        print("\nTesting ASYNC chat...")
        start = time.time()
        async with session.post(
            f"{BASE_URL}/api/chat/async",
            json={
                "agent_id": agent_id,
                "message": "Hello async",
                "chat_history": []
            }
        ) as resp:
            async_time = time.time() - start
            if resp.status == 200:
                result = await resp.json()
                print(f"  Async initiated in {async_time:.2f}s")
                print(f"  Chat ID: {result['chat_id']}")
            else:
                print(f"  Async failed: {resp.status}")

if __name__ == "__main__":
    print("=" * 60)
    print("ASYNC CHAT TEST")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Run the test
    asyncio.run(test_async_chat())
    
    print("\n" + "=" * 60)
    print("SYNC vs ASYNC COMPARISON")
    print("=" * 60)
    
    asyncio.run(test_sync_vs_async())
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)