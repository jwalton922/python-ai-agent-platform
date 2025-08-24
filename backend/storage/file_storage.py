import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from backend.models.agent import Agent, AgentCreate, AgentUpdate
from backend.models.workflow import Workflow, WorkflowCreate, WorkflowUpdate
from backend.models.activity import Activity, ActivityCreate
from backend.models.mcp_tool import MCPToolAction


class FileStorage:
    """File-based storage implementation for persistence"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.agents_dir = self.data_dir / "agents"
        self.workflows_dir = self.data_dir / "workflows"
        self.activities_file = self.data_dir / "activities.json"
        self.tool_actions_file = self.data_dir / "tool_actions.json"
        
        # Create directories if they don't exist
        self._init_storage()
        
        # Load existing data
        self._load_data()
    
    def _init_storage(self):
        """Initialize storage directories and files"""
        self.data_dir.mkdir(exist_ok=True)
        self.agents_dir.mkdir(exist_ok=True)
        self.workflows_dir.mkdir(exist_ok=True)
        
        # Create empty files if they don't exist
        if not self.activities_file.exists():
            self._write_json(self.activities_file, [])
        
        if not self.tool_actions_file.exists():
            self._write_json(self.tool_actions_file, [])
    
    def _load_data(self):
        """Load existing data from files"""
        # Activities and tool actions are loaded on demand to avoid memory issues
        pass
    
    def _read_json(self, file_path: Path) -> Any:
        """Read JSON from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def _write_json(self, file_path: Path, data: Any):
        """Write JSON to file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _get_agent_file(self, agent_id: str) -> Path:
        """Get the file path for an agent"""
        return self.agents_dir / f"{agent_id}.json"
    
    def _get_workflow_file(self, workflow_id: str) -> Path:
        """Get the file path for a workflow"""
        return self.workflows_dir / f"{workflow_id}.json"
    
    # Agent operations
    def create_agent(self, agent_data: AgentCreate) -> Agent:
        """Create a new agent"""
        agent_id = str(uuid.uuid4())
        agent = Agent(
            id=agent_id,
            created_at=datetime.utcnow(),
            **agent_data.model_dump()
        )
        
        # Save to file
        self._write_json(self._get_agent_file(agent_id), agent.model_dump())
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID"""
        agent_data = self._read_json(self._get_agent_file(agent_id))
        if agent_data:
            return Agent(**agent_data)
        return None
    
    def list_agents(self) -> List[Agent]:
        """List all agents"""
        agents = []
        for agent_file in self.agents_dir.glob("*.json"):
            agent_data = self._read_json(agent_file)
            if agent_data:
                agents.append(Agent(**agent_data))
        return agents
    
    def update_agent(self, agent_id: str, agent_update: AgentUpdate) -> Optional[Agent]:
        """Update an agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        # Update fields
        update_data = agent_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)
        
        agent.updated_at = datetime.utcnow()
        
        # Save to file
        self._write_json(self._get_agent_file(agent_id), agent.model_dump())
        return agent
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        agent_file = self._get_agent_file(agent_id)
        if agent_file.exists():
            agent_file.unlink()
            return True
        return False
    
    # Workflow operations
    def create_workflow(self, workflow_data: WorkflowCreate) -> Workflow:
        """Create a new workflow"""
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            id=workflow_id,
            created_at=datetime.utcnow(),
            **workflow_data.model_dump()
        )
        
        # Save to file
        self._write_json(self._get_workflow_file(workflow_id), workflow.model_dump())
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID"""
        workflow_data = self._read_json(self._get_workflow_file(workflow_id))
        if workflow_data:
            return Workflow(**workflow_data)
        return None
    
    def list_workflows(self) -> List[Workflow]:
        """List all workflows"""
        workflows = []
        for workflow_file in self.workflows_dir.glob("*.json"):
            workflow_data = self._read_json(workflow_file)
            if workflow_data:
                workflows.append(Workflow(**workflow_data))
        return workflows
    
    def update_workflow(self, workflow_id: str, workflow_update: WorkflowUpdate) -> Optional[Workflow]:
        """Update a workflow"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        # Update fields
        update_data = workflow_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workflow, field, value)
        
        workflow.updated_at = datetime.utcnow()
        
        # Save to file
        self._write_json(self._get_workflow_file(workflow_id), workflow.model_dump())
        return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        workflow_file = self._get_workflow_file(workflow_id)
        if workflow_file.exists():
            workflow_file.unlink()
            return True
        return False
    
    # Activity operations
    def create_activity(self, activity_data: ActivityCreate) -> Activity:
        """Create a new activity"""
        # Load existing activities
        activities = self._read_json(self.activities_file) or []
        
        # Create new activity
        activity_id = str(uuid.uuid4())
        activity = Activity(
            id=activity_id,
            created_at=datetime.utcnow(),
            **activity_data.model_dump()
        )
        
        # Add to list and save
        activities.append(activity.model_dump())
        
        # Keep only last 1000 activities to prevent file from growing too large
        if len(activities) > 1000:
            activities = activities[-1000:]
        
        self._write_json(self.activities_file, activities)
        return activity
    
    def list_activities(self, limit: int = 100, offset: int = 0) -> List[Activity]:
        """List recent activities with pagination support"""
        activities_data = self._read_json(self.activities_file) or []
        
        # Reverse to show newest first
        activities_data = list(reversed(activities_data))
        
        # Apply offset and limit
        start = offset
        end = offset + limit if limit else None
        paginated_activities = activities_data[start:end]
        
        # Convert to Activity objects
        activities = [Activity(**data) for data in paginated_activities]
        return activities
    
    def get_activities_by_agent(self, agent_id: str, limit: int = 50) -> List[Activity]:
        """Get activities for a specific agent"""
        all_activities = self.list_activities(limit=500)  # Get more to filter
        agent_activities = [a for a in all_activities if a.agent_id == agent_id]
        return agent_activities[:limit]
    
    def get_activities_by_workflow(self, workflow_id: str, limit: int = 50) -> List[Activity]:
        """Get activities for a specific workflow"""
        all_activities = self.list_activities(limit=500)  # Get more to filter
        workflow_activities = [a for a in all_activities if a.workflow_id == workflow_id]
        return workflow_activities[:limit]
    
    # Tool action operations
    def create_tool_action(self, action_data: dict) -> MCPToolAction:
        """Create a new tool action record"""
        # Load existing actions
        actions = self._read_json(self.tool_actions_file) or []
        
        # Create new action
        action_id = str(uuid.uuid4())
        action = MCPToolAction(
            id=action_id,
            created_at=datetime.utcnow(),
            **action_data
        )
        
        # Add to list and save
        actions.append(action.model_dump())
        
        # Keep only last 500 tool actions
        if len(actions) > 500:
            actions = actions[-500:]
        
        self._write_json(self.tool_actions_file, actions)
        return action
    
    def list_tool_actions(self, limit: int = 50) -> List[MCPToolAction]:
        """List recent tool actions"""
        actions_data = self._read_json(self.tool_actions_file) or []
        
        # Return most recent actions
        recent_actions = actions_data[-limit:] if limit else actions_data
        
        # Convert to MCPToolAction objects and reverse to show newest first
        actions = [MCPToolAction(**data) for data in recent_actions]
        return list(reversed(actions))


# Create a global file storage instance
file_storage = FileStorage()