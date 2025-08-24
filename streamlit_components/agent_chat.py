import streamlit as st
import requests
from typing import List, Dict, Any
from streamlit_chat import message
import hashlib

# Backend API URL
API_BASE_URL = "http://localhost:8003/api"

def render_agent_chat():
    """Render the agent chat interface using streamlit-chat"""
    st.subheader("🤖 Agent Chat")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = {}
    if 'input_counter' not in st.session_state:
        st.session_state.input_counter = 0
    
    # Fetch available agents
    agents = fetch_agents()
    
    if not agents:
        st.warning("No agents available. Please create an agent first.")
        return
    
    # Agent selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        agent_options = {f"{agent['name']} ({agent['id'][:8]})": agent for agent in agents}
        selected_agent_display = st.selectbox(
            "Select an agent to chat with:",
            options=list(agent_options.keys()),
            key="agent_selector"
        )
        selected_agent = agent_options[selected_agent_display]
        agent_id = selected_agent['id']
    
    with col2:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            if agent_id in st.session_state.messages:
                st.session_state.messages[agent_id] = []
            st.rerun()
    
    # Initialize messages for this agent if needed
    if agent_id not in st.session_state.messages:
        st.session_state.messages[agent_id] = []
    
    # Display agent info
    with st.expander(f"ℹ️ Agent Info: {selected_agent['name']}", expanded=False):
        st.write(f"**Instructions:** {selected_agent['instructions']}")
        if selected_agent.get('mcp_tool_permissions'):
            st.write(f"**Available Tools:** {', '.join(selected_agent['mcp_tool_permissions'])}")
        else:
            st.write("**Available Tools:** None")
    
    st.markdown("---")
    
    # Create container for chat messages
    chat_container = st.container()
    
    # Display chat history using streamlit-chat
    with chat_container:
        for i, msg in enumerate(st.session_state.messages[agent_id]):
            # Create a unique key for each message
            msg_key = f"{agent_id}_{i}_{hashlib.md5(msg['content'].encode()).hexdigest()[:8]}"
            
            if msg['role'] == 'user':
                message(msg['content'], is_user=True, key=msg_key)
            else:
                message(msg['content'], is_user=False, key=msg_key, avatar_style="bottts", seed=selected_agent['name'])
                
                # Show tool calls if any
                if msg.get('tool_calls'):
                    with st.expander("🔧 Tool Usage", expanded=False):
                        for tool_call in msg['tool_calls']:
                            if tool_call.get('success'):
                                st.success(f"✅ **{tool_call.get('tool', 'Unknown')}** - {tool_call.get('action', '')}")
                                if tool_call.get('result'):
                                    st.code(str(tool_call['result'])[:500], language="json")
                            else:
                                st.error(f"❌ **{tool_call.get('tool', 'Unknown')}** - {tool_call.get('error', 'Unknown error')}")
    
    # Input section
    st.markdown("### 💬 Send a Message")
    
    # Create input columns
    col1, col2 = st.columns([5, 1])
    
    with col1:
        # Use a dynamic key to force clear after submission
        user_input = st.text_input(
            "Type your message:",
            key=f"user_input_{agent_id}_{st.session_state.input_counter}",
            placeholder="Type your message here and press Enter or click Send...",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("📤 Send", use_container_width=True)
    
    # Example buttons
    examples_container = st.container()
    with examples_container:
        cols = st.columns(4)
        example_clicked = None
        
        with cols[0]:
            if 'email_tool' in selected_agent.get('mcp_tool_permissions', []):
                if st.button("📧 Email Example", use_container_width=True):
                    example_clicked = "Can you help me read my emails?"
        
        with cols[1]:
            if 'slack_tool' in selected_agent.get('mcp_tool_permissions', []):
                if st.button("💬 Slack Example", use_container_width=True):
                    example_clicked = "Can you post a message to our team channel?"
        
        with cols[2]:
            if 'file_tool' in selected_agent.get('mcp_tool_permissions', []):
                if st.button("📁 File Example", use_container_width=True):
                    example_clicked = "Can you help me read a file?"
        
        with cols[3]:
            if st.button("👋 Hello", use_container_width=True):
                example_clicked = "Hello, how can you help me?"
    
    # Process input
    message_to_send = user_input if (send_button or user_input) else example_clicked
    
    if message_to_send and message_to_send.strip():
        # Add user message
        st.session_state.messages[agent_id].append({
            'role': 'user',
            'content': message_to_send.strip()
        })
        
        # Show spinner while getting response
        with st.spinner("🤔 Thinking..."):
            # Send to backend
            response = send_chat_message(
                agent_id, 
                message_to_send.strip(),
                st.session_state.messages[agent_id]
            )
            
            if response and response.get('success', False):
                # Add assistant response
                st.session_state.messages[agent_id].append({
                    'role': 'assistant',
                    'content': response.get('message', 'I couldn\'t generate a response.'),
                    'tool_calls': response.get('tool_calls', [])
                })
            else:
                # Add error message
                error_msg = response.get('error', 'Unknown error') if response else 'Connection error'
                st.session_state.messages[agent_id].append({
                    'role': 'assistant',
                    'content': f'Sorry, I encountered an error: {error_msg}'
                })
        
        # Increment counter to clear input
        st.session_state.input_counter += 1
        
        # Rerun to show new messages
        st.rerun()


def fetch_agents() -> List[Dict[str, Any]]:
    """Fetch all agents from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/agents/")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching agents: {str(e)}")
        return []


def send_chat_message(agent_id: str, message: str, chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Send a chat message to the backend"""
    try:
        # Prepare chat history for API (exclude current message)
        api_history = []
        for msg in chat_history[:-1]:  # Skip the last message we just added
            api_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        payload = {
            "agent_id": agent_id,
            "message": message,
            "chat_history": api_history
        }
        
        response = requests.post(
            f"{API_BASE_URL}/chat/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"API Error: {response.status_code}",
                "message": "I encountered an error processing your request."
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout",
            "message": "The request took too long. Please try again."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "I encountered an error connecting to the server."
        }


if __name__ == "__main__":
    render_agent_chat()