from typing import Dict, List, Optional
import uuid
from datetime import datetime
from backend.models.agent import Agent, AgentCreate, AgentUpdate
from backend.models.workflow import Workflow, WorkflowCreate, WorkflowUpdate, WorkflowExecution
from backend.models.activity import Activity, ActivityCreate
from backend.models.mcp_tool import MCPToolAction


class InMemoryStorage:
    """Simple in-memory storage for development and testing"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.workflow_executions: Dict[str, WorkflowExecution] = {}
        self.activities: Dict[str, Activity] = {}
        self.mcp_tool_actions: Dict[str, MCPToolAction] = {}
    
    # Agent operations
    def create_agent(self, agent_data: AgentCreate) -> Agent:
        agent_id = str(uuid.uuid4())
        agent = Agent(id=agent_id, **agent_data.dict())
        self.agents[agent_id] = agent
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Agent]:
        return list(self.agents.values())
    
    def update_agent(self, agent_id: str, agent_update: AgentUpdate) -> Optional[Agent]:
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        update_data = agent_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(agent, field, value)
        
        return agent
    
    def delete_agent(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    # Workflow operations
    def create_workflow(self, workflow_data: WorkflowCreate) -> Workflow:
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(id=workflow_id, **workflow_data.dict())
        self.workflows[workflow_id] = workflow
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Workflow]:
        return list(self.workflows.values())
    
    def update_workflow(self, workflow_id: str, workflow_update: WorkflowUpdate) -> Optional[Workflow]:
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        update_data = workflow_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(workflow, field, value)
        
        return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            return True
        return False
    
    # Activity operations
    def create_activity(self, activity_data: ActivityCreate) -> Activity:
        activity_id = str(uuid.uuid4())
        activity = Activity(id=activity_id, **activity_data.dict())
        self.activities[activity_id] = activity
        return activity
    
    def list_activities(self, limit: int = 100, offset: int = 0) -> List[Activity]:
        activities = sorted(self.activities.values(), key=lambda x: x.created_at, reverse=True)
        return activities[offset:offset + limit]


# Global storage instance
storage = InMemoryStorage()