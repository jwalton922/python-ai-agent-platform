#!/usr/bin/env python3
"""
LangGraph Agent with Planning and Step Tracking
Tracks current step in plan to prevent loops
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

# Define the graph state with step tracking
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    plan: str
    plan_steps: List[str]  # Parsed steps from the plan
    current_step: int  # Which step we're currently on
    total_steps: int  # Total number of steps
    steps_completed: List[int]  # Track which steps are done

def create_agent_graph(llm):
    """Create the LangGraph agent with planning and step tracking."""
    
    tools = [search_contacts, send_email, list_all_contacts]
    llm_with_tools = llm.bind_tools(tools)
    
    def planner(state: AgentState) -> Dict[str, Any]:
        """Create a plan and parse it into steps."""
        execution_log.append("[PLANNER] Creating execution plan")
        
        messages = state["messages"]
        
        # Create planning prompt
        planning_prompt = SystemMessage(content="""You are a planning assistant. 
Based on the user's request, create a clear step-by-step plan.

Available tools:
1. search_contacts(query) - Search for contacts by name or email
2. send_email(to_email, subject, body) - Send an email
3. list_all_contacts() - List all contacts

IMPORTANT: Format your plan as a numbered list with clear, executable steps.
Example:
1. Search for John's contact information
2. Compose an email with the meeting details
3. Send the email to John

Be specific and clear about what each step should accomplish.""")
        
        # Get the plan from LLM
        plan_messages = [planning_prompt] + list(messages)
        response = llm.invoke(plan_messages)
        plan = response.content
        
        # Parse the plan into individual steps
        import re
        # Find all numbered items in the plan
        step_pattern = r'(?:^|\n)\s*(\d+)[.)]\s*(.+?)(?=\n\s*\d+[.)]|$)'
        matches = re.findall(step_pattern, plan, re.MULTILINE | re.DOTALL)
        
        plan_steps = []
        for num, step_text in matches:
            step_text = step_text.strip()
            if step_text:
                plan_steps.append(step_text)
        
        # If no numbered steps found, treat the whole plan as one step
        if not plan_steps:
            plan_steps = [plan.strip()]
        
        execution_log.append(f"[PLAN] Created {len(plan_steps)} steps:")
        for i, step in enumerate(plan_steps, 1):
            execution_log.append(f"  Step {i}: {step[:100]}...")
        
        return {
            "messages": [AIMessage(content=f"Plan created with {len(plan_steps)} steps:\n{plan}")],
            "plan": plan,
            "plan_steps": plan_steps,
            "current_step": 1,  # Start with step 1
            "total_steps": len(plan_steps),
            "steps_completed": []
        }
    
    def agent(state: AgentState) -> Dict[str, Any]:
        """Agent that executes based on the current step in the plan."""
        current_step = state.get("current_step", 1)
        total_steps = state.get("total_steps", 1)
        plan_steps = state.get("plan_steps", [])
        steps_completed = state.get("steps_completed", [])
        
        execution_log.append(f"[AGENT] Executing step {current_step} of {total_steps}")
        
        messages = state["messages"]
        plan = state.get("plan", "")
        
        # Get the current step description
        current_step_desc = ""
        if plan_steps and 0 < current_step <= len(plan_steps):
            current_step_desc = plan_steps[current_step - 1]
            execution_log.append(f"[AGENT] Current step: {current_step_desc}")
        
        # Build the context for the agent focusing on the current step
        system_msg = SystemMessage(content=f"""You are an execution assistant. 
You are currently on STEP {current_step} of {total_steps} in the following plan:

{plan}

CURRENT STEP TO EXECUTE: Step {current_step}: {current_step_desc}

Available tools:
- search_contacts(query) - Search for contacts by name or email
- send_email(to_email, subject, body) - Send an email
- list_all_contacts() - List all contacts

IMPORTANT: 
- Focus ONLY on completing step {current_step}
- Use the appropriate tools for THIS STEP ONLY
- When sending a limerick or poem, make sure it's creative and follows the proper format
- For limericks: 5 lines with AABBA rhyme scheme

Execute the current step now.""")
        
        # Prepare messages for execution
        agent_messages = [system_msg] + list(messages)
        
        # Invoke LLM with tools
        response = llm_with_tools.invoke(agent_messages)
        
        if response.tool_calls:
            execution_log.append(f"[AGENT] Step {current_step}: Calling {len(response.tool_calls)} tool(s)")
        else:
            execution_log.append(f"[AGENT] Step {current_step}: Providing response")
            # Mark this step as completed if no tools needed
            if current_step not in steps_completed:
                steps_completed.append(current_step)
        
        return {
            "messages": [response],
            "steps_completed": steps_completed
        }
    
    def update_step_tracker(state: AgentState) -> Dict[str, Any]:
        """Update which step we're on after tool execution."""
        messages = state["messages"]
        current_step = state.get("current_step", 1)
        total_steps = state.get("total_steps", 1)
        steps_completed = state.get("steps_completed", [])
        
        # Check the last message - if it's a tool result, the step is complete
        last_message = messages[-1] if messages else None
        
        if isinstance(last_message, ToolMessage):
            # Mark current step as completed
            if current_step not in steps_completed:
                steps_completed.append(current_step)
                execution_log.append(f"[TRACKER] Step {current_step} completed")
            
            # Move to next step if available
            if current_step < total_steps:
                current_step += 1
                execution_log.append(f"[TRACKER] Moving to step {current_step}")
            else:
                execution_log.append(f"[TRACKER] All {total_steps} steps completed")
        
        return {
            "current_step": current_step,
            "steps_completed": steps_completed
        }
    
    def should_continue(state: AgentState) -> str:
        """Determine if we should continue or end."""
        messages = state["messages"]
        last_message = messages[-1]
        current_step = state.get("current_step", 1)
        total_steps = state.get("total_steps", 1)
        steps_completed = state.get("steps_completed", [])
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        # Check if all steps are completed
        if len(steps_completed) >= total_steps or current_step > total_steps:
            execution_log.append(f"[ROUTER] All steps completed ({len(steps_completed)}/{total_steps})")
            return "end"
        
        # If we have more steps to do, continue
        execution_log.append(f"[ROUTER] Continuing to next step ({current_step}/{total_steps})")
        return "continue"
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Define tool node
    tool_node = ToolNode(tools)
    
    # Add nodes
    workflow.add_node("planner", planner)
    workflow.add_node("agent", agent)
    workflow.add_node("tools", tool_node)
    workflow.add_node("step_tracker", update_step_tracker)
    
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
            "continue": "agent",  # Loop back to agent for next step
            "end": END
        }
    )
    
    # After tools, update step tracker then back to agent
    workflow.add_edge("tools", "step_tracker")
    workflow.add_edge("step_tracker", "agent")
    
    return workflow.compile()

def run_agent(prompt: str, api_key: str = None):
    """Run the agent with the given prompt."""
    global execution_log
    execution_log = []  # Reset log
    
    print("="*60)
    print("LANGGRAPH AGENT WITH STEP TRACKING")
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
        "plan": "",
        "plan_steps": [],
        "current_step": 0,
        "total_steps": 0,
        "steps_completed": []
    }
    
    # Execute the graph with recursion limit
    try:
        config = {"recursion_limit": 15}
        result = app.invoke(initial_state, config=config)
        
        print("\n📋 EXECUTION STEPS:")
        print("-"*60)
        for i, step in enumerate(execution_log, 1):
            print(f"{i}. {step}")
        
        print("\n✅ FINAL RESULT:")
        print("-"*60)
        
        # Show completion status
        total_steps = result.get("total_steps", 0)
        steps_completed = result.get("steps_completed", [])
        print(f"Completed {len(steps_completed)} of {total_steps} steps")
        
        # Show the plan steps and their status
        plan_steps = result.get("plan_steps", [])
        if plan_steps:
            print("\n📊 STEP STATUS:")
            for i, step in enumerate(plan_steps, 1):
                status = "✅" if i in steps_completed else "⏳"
                print(f"  {status} Step {i}: {step[:80]}...")
        
        # Extract final response
        final_messages = result.get("messages", [])
        
        print("\n💬 AGENT RESPONSES:")
        print("-"*60)
        # Find AI messages that aren't tool calls
        for msg in final_messages:
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                print(msg.content[:500])
                if len(msg.content) > 500:
                    print("...")
            elif isinstance(msg, ToolMessage):
                # Show tool results
                print(f"Tool Result: {msg.content[:200]}")
                if len(msg.content) > 200:
                    print("...")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)

def main():
    """Main function with example prompts."""
    
    example_prompts = [
        "Send a limerick about hackathons to charlie",
        "Find Alice's email address and send her a message about our meeting tomorrow at 3pm",
        "List all contacts and send a welcome email to everyone named John"
    ]
    
    print("\n🤖 LangGraph Agent with Step Tracking\n")
    print("This agent:")
    print("  • Creates a numbered plan")
    print("  • Tracks which step it's currently executing")
    print("  • Prevents loops by focusing on one step at a time")
    print("  • Shows step-by-step progress\n")
    
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