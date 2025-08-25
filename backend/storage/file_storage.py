import json
import os
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from backend.models.agent import Agent, AgentCreate, AgentUpdate
from backend.models.workflow import Workflow, WorkflowCreate, WorkflowUpdate
from backend.models.workflow_enhanced import EnhancedWorkflow, WorkflowExecutionState
from backend.models.activity import Activity, ActivityCreate
from backend.models.mcp_tool import MCPToolAction


class FileStorage:
    """File-based storage implementation for persistence"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.agents_dir = self.data_dir / "agents"
        self.workflows_dir = self.data_dir / "workflows"
        self.enhanced_workflows_dir = self.data_dir / "enhanced_workflows"
        self.executions_dir = self.data_dir / "executions"
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
        self.enhanced_workflows_dir.mkdir(exist_ok=True)
        self.executions_dir.mkdir(exist_ok=True)
        
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
    
    # Enhanced workflow operations
    def create_enhanced_workflow(self, workflow: EnhancedWorkflow) -> EnhancedWorkflow:
        """Create a new enhanced workflow"""
        if not workflow.id:
            workflow.id = str(uuid.uuid4())
        
        # Set timestamps
        workflow.created_at = datetime.utcnow()
        
        # Save to file
        file_path = self.enhanced_workflows_dir / f"{workflow.id}.json"
        workflow_data = workflow.model_dump()
        
        # Convert datetime objects to strings for JSON serialization
        workflow_data = self._serialize_datetime(workflow_data)
        
        self._write_json(file_path, workflow_data)
        return workflow
    
    def get_enhanced_workflow(self, workflow_id: str) -> Optional[EnhancedWorkflow]:
        """Get enhanced workflow by ID"""
        file_path = self.enhanced_workflows_dir / f"{workflow_id}.json"
        if not file_path.exists():
            return None
        
        try:
            data = self._read_json(file_path)
            # Convert datetime strings back to datetime objects
            data = self._deserialize_datetime(data, ['created_at', 'updated_at'])
            return EnhancedWorkflow(**data)
        except Exception as e:
            print(f"Error loading enhanced workflow {workflow_id}: {e}")
            traceback.print_exc()
            return None
    
    def update_enhanced_workflow(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> Optional[EnhancedWorkflow]:
        """Update enhanced workflow"""
        workflow = self.get_enhanced_workflow(workflow_id)
        if not workflow:
            return None
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        workflow.updated_at = datetime.utcnow()
        
        # Save updated workflow
        return self.create_enhanced_workflow(workflow)
    
    def delete_enhanced_workflow(self, workflow_id: str) -> bool:
        """Delete enhanced workflow"""
        file_path = self.enhanced_workflows_dir / f"{workflow_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def list_enhanced_workflows(self) -> List[EnhancedWorkflow]:
        """List all enhanced workflows"""
        workflows = []
        for file_path in self.enhanced_workflows_dir.glob("*.json"):
            try:
                data = self._read_json(file_path)
                data = self._deserialize_datetime(data, ['created_at', 'updated_at'])
                workflow = EnhancedWorkflow(**data)
                workflows.append(workflow)
            except Exception as e:
                print(f"Error loading workflow from {file_path}: {e}")
                traceback.print_exc()
                continue
        
        return workflows
    
    # Workflow execution operations
    def create_workflow_execution(self, execution: WorkflowExecutionState) -> WorkflowExecutionState:
        """Create workflow execution record"""
        if not execution.execution_id:
            execution.execution_id = str(uuid.uuid4())
        
        file_path = self.executions_dir / f"{execution.execution_id}.json"
        execution_data = execution.model_dump()
        execution_data = self._serialize_datetime(execution_data)
        
        self._write_json(file_path, execution_data)
        return execution
    
    def get_workflow_execution(self, execution_id: str) -> Optional[WorkflowExecutionState]:
        """Get workflow execution by ID"""
        file_path = self.executions_dir / f"{execution_id}.json"
        if not file_path.exists():
            return None
        
        try:
            data = self._read_json(file_path)
            data = self._deserialize_datetime(data, ['started_at', 'completed_at', 'last_checkpoint'])
            return WorkflowExecutionState(**data)
        except Exception as e:
            print(f"Error loading execution {execution_id}: {e}")
            traceback.print_exc()
            return None
    
    def update_workflow_execution(
        self,
        execution_id: str,
        updates: Dict[str, Any]
    ) -> Optional[WorkflowExecutionState]:
        """Update workflow execution"""
        execution = self.get_workflow_execution(execution_id)
        if not execution:
            return None
        
        for key, value in updates.items():
            if hasattr(execution, key):
                setattr(execution, key, value)
        
        return self.create_workflow_execution(execution)
    
    def list_workflow_executions(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 100
    ) -> List[WorkflowExecutionState]:
        """List workflow executions"""
        executions = []
        count = 0
        
        # Sort by modification time (newest first)
        files = sorted(
            self.executions_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        for file_path in files:
            if count >= limit:
                break
            
            try:
                data = self._read_json(file_path)
                
                # Filter by workflow_id if specified
                if workflow_id and data.get("workflow_id") != workflow_id:
                    continue
                
                data = self._deserialize_datetime(data, ['started_at', 'completed_at', 'last_checkpoint'])
                execution = WorkflowExecutionState(**data)
                executions.append(execution)
                count += 1
            except Exception as e:
                print(f"Error loading execution from {file_path}: {e}")
                traceback.print_exc()
                continue
        
        return executions
    
    # Helper methods for datetime serialization
    def _serialize_datetime(self, data: Any) -> Any:
        """Convert datetime objects to ISO strings for JSON serialization"""
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {key: self._serialize_datetime(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._serialize_datetime(item) for item in data]
        else:
            return data
    
    def _deserialize_datetime(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Convert ISO string fields back to datetime objects"""
        for field in fields:
            if field in data and data[field] and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field])
                except Exception as e:
                    print(f"Failed to parse datetime field {field}: {e}")
                    traceback.print_exc()
                    pass  # Leave as string if conversion fails
        return data


# Create a global file storage instance
file_storage = FileStorage()