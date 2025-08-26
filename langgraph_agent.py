#!/usr/bin/env python3
"""
LangGraph Agent with Planning and Execution
"""

import json
from typing import Any, Dict, List, Literal, TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import operator
import os
from datetime import datetime

# Mock contact database
CONTACTS = {
    "john_smith": {"name": "John Smith", "email": "john.smith@example.com"},
    "jane_doe": {"name": "Jane Doe", "email": "jane.doe@example.com"},
    "bob_wilson": {"name": "Bob Wilson", "email": "bob.wilson@example.com"},
    "alice_johnson": {"name": "Alice Johnson", "email": "alice.j@example.com"},
    "charlie_brown": {"name": "Charlie Brown", "email": "charlie.b@example.com"}
}

# Track execution steps
execution_log = []

@tool
def search_contacts(query: str) -> str:
    """Search for contacts by name or email. Returns matching contacts."""
    execution_log.append(f"[TOOL] Searching contacts for: '{query}'")
    
    query_lower = query.lower()
    matches = []
    
    for contact_id, contact in CONTACTS.items():
        if (query_lower in contact["name"].lower() or 
            query_lower in contact["email"].lower()):
            matches.append(contact)
    
    if matches:
        result = f"Found {len(matches)} contact(s):\n"
        for contact in matches:
            result += f"- {contact['name']} ({contact['email']})\n"
    else:
        result = f"No contacts found matching '{query}'"
    
    execution_log.append(f"[RESULT] {result}")
    return result

@tool
def send_email(to_email: str, subject: str, body: str) -> str:
    """Send an email to the specified address. (Simulated - no actual email sent)"""
    execution_log.append(f"[TOOL] Sending email to: {to_email}")
    
    # Simulate email sending
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = (f"Email successfully sent!\n"
              f"To: {to_email}\n"
              f"Subject: {subject}\n"
              f"Body: {body[:100]}{'...' if len(body) > 100 else ''}\n"
              f"Sent at: {timestamp}")
    
    execution_log.append(f"[RESULT] Email sent to {to_email} with subject '{subject}'")
    return result

@tool
def list_all_contacts() -> str:
    """List all available contacts in the system."""
    execution_log.append("[TOOL] Listing all contacts")
    
    result = f"Total contacts: {len(CONTACTS)}\n"
    for contact in CONTACTS.values():
        result += f"- {contact['name']} ({contact['email']})\n"
    
    execution_log.append(f"[RESULT] Listed {len(CONTACTS)} contacts")
    return result

# Define the graph state using new annotation style
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    plan: str

def create_agent_graph(llm):
    """Create the LangGraph agent with planning and execution capabilities."""
    
    tools = [search_contacts, send_email, list_all_contacts]
    llm_with_tools = llm.bind_tools(tools)
    
    def planner(state: AgentState) -> Dict[str, Any]:
        """Create a plan based on the user's request."""
        execution_log.append("[PLANNER] Creating execution plan")
        
        messages = state["messages"]
        
        # Create planning prompt
        planning_prompt = SystemMessage(content="""You are a planning assistant. 
Based on the user's request, create a clear step-by-step plan.

Available tools:
1. search_contacts(query) - Search for contacts by name or email
2. send_email(to_email, subject, body) - Send an email
3. list_all_contacts() - List all contacts

Provide a concise plan with numbered steps.""")
        
        # Get the plan from LLM
        plan_messages = [planning_prompt] + list(messages)
        response = llm.invoke(plan_messages)
        plan = response.content
        
        execution_log.append(f"[PLAN] {plan}")
        
        return {
            "messages": [AIMessage(content=f"Plan created:\n{plan}")],
            "plan": plan
        }
    
    def agent(state: AgentState) -> Dict[str, Any]:
        """Agent that executes based on the plan."""
        execution_log.append("[AGENT] Executing with tools")
        
        messages = state["messages"]
        plan = state.get("plan", "")
        
        # Build the context for the agent
        system_msg = SystemMessage(content=f"""You are an execution assistant. 
Execute this plan step by step using the available tools:

{plan}

Available tools:
- search_contacts(query) - Search for contacts by name or email
- send_email(to_email, subject, body) - Send an email
- list_all_contacts() - List all contacts

Important: When sending a limerick or poem, make sure it's creative and follows the proper format.
For limericks: 5 lines with AABBA rhyme scheme.

Call the necessary tools to complete the task.""")
        
        # Prepare messages for execution
        agent_messages = [system_msg] + list(messages)
        
        # Invoke LLM with tools
        response = llm_with_tools.invoke(agent_messages)
        
        if response.tool_calls:
            execution_log.append(f"[AGENT] Calling {len(response.tool_calls)} tool(s)")
        else:
            execution_log.append("[AGENT] Providing response")
        
        return {"messages": [response]}
    
    def should_continue(state: AgentState) -> str:
        """Determine if we should continue or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        # Otherwise, we're done
        return "end"
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Define tool node
    tool_node = ToolNode(tools)
    
    # Add nodes
    workflow.add_node("planner", planner)
    workflow.add_node("agent", agent)
    workflow.add_node("tools", tool_node)
    
    # Set the entry point
    workflow.set_entry_point("planner")
    
    # Add edges
    workflow.add_edge("planner", "agent")
    
    # Add conditional edges from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # After tools, go back to agent
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

def run_agent(prompt: str, api_key: str = None):
    """Run the agent with the given prompt."""
    global execution_log
    execution_log = []  # Reset log
    
    print("="*60)
    print("LANGGRAPH AGENT EXECUTION")
    print("="*60)
    print(f"\n📝 USER PROMPT: {prompt}\n")
    print("-"*60)
    
    # Initialize LLM
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ Error: OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        return
    
    llm = ChatOpenAI(temperature=0, api_key=api_key)
    
    # Create and run the agent
    app = create_agent_graph(llm)
    
    initial_state = {
        "messages": [HumanMessage(content=prompt)],
        "plan": ""
    }
    
    # Execute the graph with recursion limit
    try:
        config = {"recursion_limit": 10}
        result = app.invoke(initial_state, config=config)
        
        print("\n📋 EXECUTION STEPS:")
        print("-"*60)
        for i, step in enumerate(execution_log, 1):
            print(f"{i}. {step}")
        
        print("\n✅ FINAL RESULT:")
        print("-"*60)
        
        # Extract final response
        final_messages = result.get("messages", [])
        
        # Find the last AI message that's not a tool call
        for msg in reversed(final_messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                print(msg.content)
                break
            elif isinstance(msg, ToolMessage):
                # Show tool results if they're the final output
                print(f"Tool Result: {msg.content}")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
    
    print("\n" + "="*60)

def main():
    """Main function with example prompts."""
    
    # Example prompts
    example_prompts = [
        "Send a limerick about hackathons to charlie"
    ]
    
    print("\n🤖 LangGraph Agent with Planning and Tool Execution\n")
    print("This agent can:")
    print("  • Search and list contacts")
    print("  • Send emails (simulated)")
    print("  • Create and execute multi-step plans\n")
    
    print("Example prompts:")
    for i, prompt in enumerate(example_prompts, 1):
        print(f"  {i}. {prompt}")
    
    print("\nEnter 'quit' to exit")
    print("-"*60)
    
    while True:
        try:
            user_input = input("\n👤 Enter your prompt: ").strip()
        except EOFError:
            # Handle piped input
            import sys
            user_input = sys.stdin.read().strip()
            if user_input:
                run_agent(user_input)
            break
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye! 👋")
            break
        
        if user_input:
            run_agent(user_input)
        else:
            print("Please enter a prompt or 'quit' to exit.")

if __name__ == "__main__":
    main()