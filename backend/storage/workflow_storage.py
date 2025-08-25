import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
from pathlib import Path

from backend.models.workflow_enhanced import (
    EnhancedWorkflow,
    WorkflowExecutionState,
    WorkflowExecutionResult,
    WorkflowStatus
)


class WorkflowStorage:
    """Enhanced storage for workflows with support for versioning and execution history"""
    
    def __init__(self, base_path: str = "./data/workflows"):
        self.base_path = Path(base_path)
        self.workflows_path = self.base_path / "definitions"
        self.executions_path = self.base_path / "executions"
        self.checkpoints_path = self.base_path / "checkpoints"
        self.templates_path = self.base_path / "templates"
        
        # Create directories if they don't exist
        for path in [self.workflows_path, self.executions_path, 
                     self.checkpoints_path, self.templates_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # In-memory caches
        self._workflow_cache: Dict[str, EnhancedWorkflow] = {}
        self._execution_cache: Dict[str, WorkflowExecutionState] = {}
        self._version_index: Dict[str, List[str]] = {}  # workflow_id -> [versions]
    
    # Workflow Management
    
    def create_workflow(self, workflow: EnhancedWorkflow) -> EnhancedWorkflow:
        """Create a new workflow with versioning"""
        if not workflow.id:
            workflow.id = self._generate_id(workflow.name)
        
        # Add to version index
        if workflow.id not in self._version_index:
            self._version_index[workflow.id] = []
        
        self._version_index[workflow.id].append(workflow.version)
        
        # Save workflow
        self._save_workflow(workflow)
        
        # Update cache
        cache_key = f"{workflow.id}:{workflow.version}"
        self._workflow_cache[cache_key] = workflow
        
        return workflow
    
    def get_workflow(
        self,
        workflow_id: str,
        version: Optional[str] = None
    ) -> Optional[EnhancedWorkflow]:
        """Get workflow by ID and optional version"""
        # Check cache first
        if version:
            cache_key = f"{workflow_id}:{version}"
        else:
            # Get latest version
            versions = self._version_index.get(workflow_id, [])
            if not versions:
                return None
            version = sorted(versions)[-1]  # Get latest version
            cache_key = f"{workflow_id}:{version}"
        
        if cache_key in self._workflow_cache:
            return self._workflow_cache[cache_key]
        
        # Load from disk
        workflow = self._load_workflow(workflow_id, version)
        if workflow:
            self._workflow_cache[cache_key] = workflow
        
        return workflow
    
    def update_workflow(
        self,
        workflow_id: str,
        updates: Dict[str, Any],
        create_version: bool = True
    ) -> EnhancedWorkflow:
        """Update workflow, optionally creating a new version"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if create_version:
            # Create new version
            old_version = workflow.version
            version_parts = old_version.split(".")
            version_parts[-1] = str(int(version_parts[-1]) + 1)
            workflow.version = ".".join(version_parts)
            
            # Add to version index
            self._version_index[workflow_id].append(workflow.version)
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        workflow.updated_at = datetime.utcnow()
        
        # Save and update cache
        self._save_workflow(workflow)
        cache_key = f"{workflow_id}:{workflow.version}"
        self._workflow_cache[cache_key] = workflow
        
        return workflow
    
    def delete_workflow(self, workflow_id: str, version: Optional[str] = None) -> bool:
        """Delete workflow or specific version"""
        if version:
            # Delete specific version
            file_path = self._get_workflow_path(workflow_id, version)
            if file_path.exists():
                file_path.unlink()
                
                cache_key = f"{workflow_id}:{version}"
                if cache_key in self._workflow_cache:
                    del self._workflow_cache[cache_key]
                
                if workflow_id in self._version_index:
                    self._version_index[workflow_id].remove(version)
                
                return True
        else:
            # Delete all versions
            versions = self._version_index.get(workflow_id, [])
            for ver in versions:
                self.delete_workflow(workflow_id, ver)
            
            if workflow_id in self._version_index:
                del self._version_index[workflow_id]
            
            return True
        
        return False
    
    def list_workflows(self) -> List[EnhancedWorkflow]:
        """List all workflows (latest versions only)"""
        workflows = []
        
        for workflow_id in self._version_index:
            workflow = self.get_workflow(workflow_id)
            if workflow:
                workflows.append(workflow)
        
        return workflows
    
    def list_workflow_versions(self, workflow_id: str) -> List[str]:
        """List all versions of a workflow"""
        return self._version_index.get(workflow_id, [])
    
    # Execution Management
    
    def create_execution(
        self,
        execution_state: WorkflowExecutionState
    ) -> WorkflowExecutionState:
        """Create a new workflow execution record"""
        if not execution_state.execution_id:
            execution_state.execution_id = self._generate_id(
                f"{execution_state.workflow_id}_{datetime.utcnow().isoformat()}"
            )
        
        self._save_execution(execution_state)
        self._execution_cache[execution_state.execution_id] = execution_state
        
        return execution_state
    
    def update_execution(
        self,
        execution_id: str,
        updates: Dict[str, Any]
    ) -> WorkflowExecutionState:
        """Update execution state"""
        execution = self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        for key, value in updates.items():
            if hasattr(execution, key):
                setattr(execution, key, value)
        
        self._save_execution(execution)
        self._execution_cache[execution_id] = execution
        
        return execution
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecutionState]:
        """Get execution by ID"""
        if execution_id in self._execution_cache:
            return self._execution_cache[execution_id]
        
        execution = self._load_execution(execution_id)
        if execution:
            self._execution_cache[execution_id] = execution
        
        return execution
    
    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100
    ) -> List[WorkflowExecutionState]:
        """List workflow executions with optional filtering"""
        executions = []
        
        for file_path in self.executions_path.glob("*.json"):
            if len(executions) >= limit:
                break
            
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    execution = WorkflowExecutionState(**data)
                    
                    # Apply filters
                    if workflow_id and execution.workflow_id != workflow_id:
                        continue
                    
                    if status and execution.status != status:
                        continue
                    
                    executions.append(execution)
            except:
                continue
        
        # Sort by started_at descending
        executions.sort(key=lambda e: e.started_at, reverse=True)
        
        return executions[:limit]
    
    # Checkpoint Management
    
    def create_checkpoint(
        self,
        execution_id: str,
        state: WorkflowExecutionState
    ) -> str:
        """Create execution checkpoint"""
        checkpoint_id = self._generate_id(f"{execution_id}_{datetime.utcnow().isoformat()}")
        
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "execution_id": execution_id,
            "timestamp": datetime.utcnow().isoformat(),
            "state": state.model_dump()
        }
        
        file_path = self.checkpoints_path / f"{checkpoint_id}.json"
        with open(file_path, "w") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
        
        return checkpoint_id
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[WorkflowExecutionState]:
        """Load execution state from checkpoint"""
        file_path = self.checkpoints_path / f"{checkpoint_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                state_data = data["state"]
                
                # Convert string dates back to datetime
                if "started_at" in state_data:
                    state_data["started_at"] = datetime.fromisoformat(state_data["started_at"])
                if "completed_at" in state_data and state_data["completed_at"]:
                    state_data["completed_at"] = datetime.fromisoformat(state_data["completed_at"])
                if "last_checkpoint" in state_data and state_data["last_checkpoint"]:
                    state_data["last_checkpoint"] = datetime.fromisoformat(state_data["last_checkpoint"])
                
                return WorkflowExecutionState(**state_data)
        except Exception as e:
            print(f"Error loading checkpoint {checkpoint_id}: {e}")
            return None
    
    def list_checkpoints(self, execution_id: str) -> List[Dict[str, Any]]:
        """List all checkpoints for an execution"""
        checkpoints = []
        
        for file_path in self.checkpoints_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    if data.get("execution_id") == execution_id:
                        checkpoints.append({
                            "checkpoint_id": data["checkpoint_id"],
                            "timestamp": data["timestamp"],
                            "execution_id": data["execution_id"]
                        })
            except:
                continue
        
        checkpoints.sort(key=lambda c: c["timestamp"], reverse=True)
        return checkpoints
    
    # Template Management
    
    def save_template(
        self,
        workflow: EnhancedWorkflow,
        template_name: str,
        description: str = ""
    ) -> str:
        """Save workflow as a template"""
        template_id = self._generate_id(template_name)
        
        template_data = {
            "template_id": template_id,
            "template_name": template_name,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "workflow": workflow.model_dump()
        }
        
        file_path = self.templates_path / f"{template_id}.json"
        with open(file_path, "w") as f:
            json.dump(template_data, f, indent=2, default=str)
        
        return template_id
    
    def load_template(self, template_id: str) -> Optional[EnhancedWorkflow]:
        """Load workflow from template"""
        file_path = self.templates_path / f"{template_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                workflow_data = data["workflow"]
                
                # Convert string dates
                if "created_at" in workflow_data:
                    workflow_data["created_at"] = datetime.fromisoformat(workflow_data["created_at"])
                if "updated_at" in workflow_data and workflow_data["updated_at"]:
                    workflow_data["updated_at"] = datetime.fromisoformat(workflow_data["updated_at"])
                
                # Create new workflow from template
                workflow = EnhancedWorkflow(**workflow_data)
                workflow.id = None  # Reset ID so a new one is generated
                
                return workflow
        except Exception as e:
            print(f"Error loading template {template_id}: {e}")
            return None
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all workflow templates"""
        templates = []
        
        for file_path in self.templates_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    templates.append({
                        "template_id": data["template_id"],
                        "template_name": data["template_name"],
                        "description": data.get("description", ""),
                        "created_at": data["created_at"]
                    })
            except:
                continue
        
        templates.sort(key=lambda t: t["created_at"], reverse=True)
        return templates
    
    # Analytics and Metrics
    
    def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get execution metrics for a workflow"""
        executions = self.list_executions(workflow_id=workflow_id, limit=1000)
        
        if not executions:
            return {
                "workflow_id": workflow_id,
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0,
                "avg_tokens_used": 0,
                "avg_cost_usd": 0.0
            }
        
        successful = [e for e in executions if e.status == WorkflowStatus.COMPLETED]
        failed = [e for e in executions if e.status == WorkflowStatus.FAILED]
        
        durations = []
        tokens = []
        costs = []
        
        for execution in successful:
            if execution.completed_at and execution.started_at:
                duration_ms = int(
                    (execution.completed_at - execution.started_at).total_seconds() * 1000
                )
                durations.append(duration_ms)
            
            tokens.append(execution.total_tokens_used)
            costs.append(execution.total_cost_usd)
        
        return {
            "workflow_id": workflow_id,
            "total_executions": len(executions),
            "successful_executions": len(successful),
            "failed_executions": len(failed),
            "success_rate": len(successful) / len(executions) if executions else 0.0,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "avg_tokens_used": sum(tokens) / len(tokens) if tokens else 0,
            "avg_cost_usd": sum(costs) / len(costs) if costs else 0.0,
            "total_tokens_used": sum(tokens),
            "total_cost_usd": sum(costs)
        }
    
    # Private helper methods
    
    def _generate_id(self, seed: str) -> str:
        """Generate unique ID"""
        return hashlib.md5(f"{seed}_{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
    
    def _get_workflow_path(self, workflow_id: str, version: str) -> Path:
        """Get file path for workflow"""
        return self.workflows_path / f"{workflow_id}_v{version.replace('.', '_')}.json"
    
    def _save_workflow(self, workflow: EnhancedWorkflow):
        """Save workflow to disk"""
        file_path = self._get_workflow_path(workflow.id, workflow.version)
        
        with open(file_path, "w") as f:
            json.dump(workflow.model_dump(), f, indent=2, default=str)
    
    def _load_workflow(self, workflow_id: str, version: str) -> Optional[EnhancedWorkflow]:
        """Load workflow from disk"""
        file_path = self._get_workflow_path(workflow_id, version)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                
                # Convert string dates
                if "created_at" in data:
                    data["created_at"] = datetime.fromisoformat(data["created_at"])
                if "updated_at" in data and data["updated_at"]:
                    data["updated_at"] = datetime.fromisoformat(data["updated_at"])
                
                return EnhancedWorkflow(**data)
        except Exception as e:
            print(f"Error loading workflow {workflow_id} v{version}: {e}")
            return None
    
    def _save_execution(self, execution: WorkflowExecutionState):
        """Save execution to disk"""
        file_path = self.executions_path / f"{execution.execution_id}.json"
        
        with open(file_path, "w") as f:
            json.dump(execution.model_dump(), f, indent=2, default=str)
    
    def _load_execution(self, execution_id: str) -> Optional[WorkflowExecutionState]:
        """Load execution from disk"""
        file_path = self.executions_path / f"{execution_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                
                # Convert string dates
                if "started_at" in data:
                    data["started_at"] = datetime.fromisoformat(data["started_at"])
                if "completed_at" in data and data["completed_at"]:
                    data["completed_at"] = datetime.fromisoformat(data["completed_at"])
                if "last_checkpoint" in data and data["last_checkpoint"]:
                    data["last_checkpoint"] = datetime.fromisoformat(data["last_checkpoint"])
                
                return WorkflowExecutionState(**data)
        except Exception as e:
            print(f"Error loading execution {execution_id}: {e}")
            return None
    
    def cleanup_old_executions(self, days: int = 30):
        """Clean up old execution records"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        for file_path in self.executions_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    started_at = datetime.fromisoformat(data["started_at"])
                    
                    if started_at < cutoff_date:
                        file_path.unlink()
                        
                        # Remove from cache
                        execution_id = data["execution_id"]
                        if execution_id in self._execution_cache:
                            del self._execution_cache[execution_id]
            except:
                continue


# Global instance
workflow_storage = WorkflowStorage()