import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Add project root to path if not already there
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from streamlit_components.react_components import activity_monitor
from streamlit_components.backend_integrated_workflow import workflow_editor_integrated
from streamlit_components.backend_integrated_agents import agent_builder_integrated
from streamlit_components.agent_chat import render_agent_chat

# Configure page
st.set_page_config(
    page_title="AI Agent Platform - Unified Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API Configuration
API_BASE = "http://localhost:8003/api"

@st.cache_data(ttl=30)
def fetch_data(endpoint):
    """Fetch data from API with caching"""
    try:
        response = requests.get(f"{API_BASE}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch {endpoint}: {e}")
        return []

def main():
    st.title("🤖 AI Agent Platform - Unified Dashboard")
    st.markdown("*React UI components embedded in Streamlit*")
    st.markdown("---")

    # Main navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🔄 Workflows", "🤖 Agents", "💬 Chat", "📈 Activities", "📊 Overview", "🔧 System"])
    
    with tab1:
        st.header("Backend-Integrated Workflow Editor")
        st.markdown("*Drag-and-drop workflow builder connected to your backend API*")
        workflow_editor_integrated(height=700)
    
    with tab2:
        st.header("Backend-Integrated Agent Builder")
        st.markdown("*Create and manage AI agents with full backend connectivity*")
        agent_builder_integrated(height=700)
    
    with tab3:
        render_agent_chat()
    
    with tab4:
        st.header("Real-time Activity Monitor")
        st.markdown("*Live activity feed with filtering and real-time updates*")
        activity_monitor(height=700)
    
    with tab5:
        st.header("Platform Overview")
        show_overview()
    
    with tab6:
        st.header("System Status")
        show_system_status()

def show_overview():
    """Show overview dashboard"""
    st.header("📊 Platform Overview")
    
    # Fetch data
    agents = fetch_data("agents")
    workflows = fetch_data("workflows")
    activities = fetch_data("activities")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Agents", len(agents))
    
    with col2:
        st.metric("Total Workflows", len(workflows))
    
    with col3:
        successful_activities = len([a for a in activities if a.get('success', True)])
        st.metric("Successful Activities", successful_activities)
    
    with col4:
        failed_activities = len(activities) - successful_activities
        st.metric("Failed Activities", failed_activities, delta_color="inverse")

    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if activities:
            # Activity timeline
            df_activities = pd.DataFrame(activities)
            df_activities['created_at'] = pd.to_datetime(df_activities['created_at'])
            df_activities['date'] = df_activities['created_at'].dt.date
            
            activity_counts = df_activities.groupby(['date', 'type']).size().reset_index(name='count')
            
            fig = px.line(
                activity_counts, 
                x='date', 
                y='count', 
                color='type',
                title="Activity Timeline"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activities data available")
    
    with col2:
        if agents:
            # Agent tools distribution
            tool_counts = {}
            for agent in agents:
                tools = agent.get('mcp_tool_permissions', [])
                for tool in tools:
                    tool_counts[tool] = tool_counts.get(tool, 0) + 1
            
            if tool_counts:
                df_tools = pd.DataFrame(list(tool_counts.items()), columns=['tool', 'count'])
                fig = px.pie(df_tools, values='count', names='tool', title="Tool Usage Distribution")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No agents data available")

# Agent management is now handled by React component in main tabs

# Workflow management is now handled by React component in main tabs

# Activity monitoring is now handled by React component in main tabs

def show_system_status():
    """Show system status"""
    st.header("🔧 System Status")
    
    # Health check
    try:
        health_response = requests.get("http://localhost:8003/health")
        if health_response.status_code == 200:
            st.success("✅ API Server: Healthy")
        else:
            st.error("❌ API Server: Unhealthy")
    except:
        st.error("❌ API Server: Unreachable")
    
    # MCP Tools status
    st.subheader("MCP Tools Status")
    tools = fetch_data("mcp-tools")
    
    if tools:
        for tool in tools:
            status_icon = "🟢" if tool.get('enabled', True) else "🔴"
            st.write(f"{status_icon} **{tool['name']}** ({tool['category']})")
            st.write(f"   - {tool['schema']['description']}")
    else:
        st.warning("No MCP tools available")
    
    # System metrics (mock data for demo)
    st.subheader("System Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("CPU Usage", "23%", "2%")
    
    with col2:
        st.metric("Memory Usage", "45%", "-1%")
    
    with col3:
        st.metric("Active Connections", "8", "2")

if __name__ == "__main__":
    main()