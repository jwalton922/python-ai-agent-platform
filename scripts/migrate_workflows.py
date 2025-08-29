"""
Migration script to convert legacy workflows to enhanced format
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from backend.models.workflow import Workflow
from backend.models.workflow_enhanced import (
    EnhancedWorkflow,
    EnhancedWorkflowNode,
    EnhancedWorkflowEdge,
    NodeType,
    ExecutionMode,
    WorkflowSettings,
    WorkflowMonitoring,
    WorkflowVariable
)
from backend.storage.file_storage import file_storage


class WorkflowMigrator:
    """Migrate legacy workflows to enhanced format"""
    
    def __init__(self):
        self.migration_log = []
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }
    
    def migrate_all_workflows(self, dry_run: bool = True) -> Dict[str, Any]:
        """Migrate all legacy workflows to enhanced format"""
        print(f"Starting workflow migration (dry_run={dry_run})")
        
        # Get all legacy workflows
        legacy_workflows = file_storage.list_workflows()
        
        print(f"Found {len(legacy_workflows)} legacy workflows to migrate")
        
        migrated_workflows = []
        
        for workflow in legacy_workflows:
            try:
                self.stats["processed"] += 1
                
                # Check if already migrated
                existing_enhanced = file_storage.get_enhanced_workflow(workflow.id)
                if existing_enhanced:
                    print(f"Workflow {workflow.id} already migrated, skipping")
                    self.stats["skipped"] += 1
                    continue
                
                # Migrate workflow
                enhanced_workflow = self._migrate_single_workflow(workflow)
                
                if not dry_run:
                    # Save migrated workflow
                    saved_workflow = file_storage.create_enhanced_workflow(enhanced_workflow)
                    migrated_workflows.append(saved_workflow)
                
                self.stats["successful"] += 1
                self._log_migration(workflow.id, "SUCCESS", f"Migrated to enhanced format")
                
                print(f"✓ Migrated workflow: {workflow.name} ({workflow.id})")
                
            except Exception as e:
                self.stats["failed"] += 1
                error_msg = str(e)
                self._log_migration(workflow.id, "ERROR", error_msg)
                print(f"✗ Failed to migrate workflow {workflow.id}: {error_msg}")
        
        # Generate migration report
        report = self._generate_migration_report(migrated_workflows, dry_run)
        
        return report
    
    def _migrate_single_workflow(self, legacy_workflow: Workflow) -> EnhancedWorkflow:
        """Migrate a single legacy workflow"""
        
        # Migrate nodes
        enhanced_nodes = []
        for node in legacy_workflow.nodes:
            enhanced_node = EnhancedWorkflowNode(
                id=node.id,
                type=NodeType.AGENT,  # Legacy workflows only had agent nodes
                name=f"Agent {node.id}",
                description=f"Migrated agent node",
                position=node.position if hasattr(node, 'position') else {"x": 100, "y": 100},
                agent_id=node.agent_id,
                config=node.config if hasattr(node, 'config') else {}
            )
            enhanced_nodes.append(enhanced_node)
        
        # Migrate edges
        enhanced_edges = []
        for edge in legacy_workflow.edges:
            enhanced_edge = EnhancedWorkflowEdge(
                id=edge.id,
                source_node_id=edge.source_node_id,
                target_node_id=edge.target_node_id,
                condition=edge.condition if hasattr(edge, 'condition') else None,
                data_mapping=[]  # Legacy workflows didn't have data mapping
            )
            enhanced_edges.append(enhanced_edge)
        
        # Create enhanced workflow
        enhanced_workflow = EnhancedWorkflow(
            id=legacy_workflow.id,
            name=legacy_workflow.name,
            description=legacy_workflow.description or "Migrated from legacy workflow",
            version="2.0.0",  # Mark as migrated
            nodes=enhanced_nodes,
            edges=enhanced_edges,
            variables=[],  # Legacy workflows didn't have variables
            execution_mode=ExecutionMode.SEQUENTIAL,
            trigger_conditions=legacy_workflow.trigger_conditions if hasattr(legacy_workflow, 'trigger_conditions') else [],
            settings=WorkflowSettings(
                max_execution_time_ms=300000,  # Default 5 minutes
                max_total_tokens=5000
            ),
            monitoring=WorkflowMonitoring(
                metrics_enabled=True,
                capture_inputs=True,
                capture_outputs=True
            ),
            status=legacy_workflow.status if hasattr(legacy_workflow, 'status') else "idle",
            tags=["migrated", "legacy"] + (legacy_workflow.metadata.get("tags", []) if legacy_workflow.metadata else []),
            metadata={
                **legacy_workflow.metadata,
                "migration": {
                    "migrated_at": datetime.utcnow().isoformat(),
                    "original_version": "1.0.0",
                    "migration_tool": "WorkflowMigrator v1.0"
                }
            } if legacy_workflow.metadata else {
                "migration": {
                    "migrated_at": datetime.utcnow().isoformat(),
                    "original_version": "1.0.0",
                    "migration_tool": "WorkflowMigrator v1.0"
                }
            }
        )
        
        # Copy timestamps if available
        if hasattr(legacy_workflow, 'created_at'):
            enhanced_workflow.created_at = legacy_workflow.created_at
        if hasattr(legacy_workflow, 'updated_at'):
            enhanced_workflow.updated_at = legacy_workflow.updated_at
        
        return enhanced_workflow
    
    def _log_migration(self, workflow_id: str, status: str, message: str):
        """Log migration activity"""
        self.migration_log.append({
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "message": message
        })
    
    def _generate_migration_report(self, migrated_workflows: List[EnhancedWorkflow], dry_run: bool) -> Dict[str, Any]:
        """Generate migration report"""
        
        report = {
            "migration_summary": {
                "timestamp": datetime.utcnow().isoformat(),
                "dry_run": dry_run,
                "statistics": self.stats,
                "success_rate": self.stats["successful"] / max(self.stats["processed"], 1) * 100
            },
            "migrated_workflows": [
                {
                    "id": wf.id,
                    "name": wf.name,
                    "node_count": len(wf.nodes),
                    "edge_count": len(wf.edges),
                    "has_variables": len(wf.variables) > 0,
                    "execution_mode": wf.execution_mode.value,
                    "tags": wf.tags
                }
                for wf in migrated_workflows
            ],
            "migration_log": self.migration_log,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate post-migration recommendations"""
        recommendations = []
        
        if self.stats["failed"] > 0:
            recommendations.append(f"Review {self.stats['failed']} failed migrations and resolve issues manually")
        
        if self.stats["successful"] > 0:
            recommendations.append("Test migrated workflows before deploying to production")
            recommendations.append("Consider adding variables and enhanced features to migrated workflows")
            recommendations.append("Update any external references to use enhanced workflow APIs")
        
        recommendations.extend([
            "Back up original workflows before deleting them",
            "Monitor enhanced workflows for proper functionality",
            "Consider creating workflow templates for common patterns"
        ])
        
        return recommendations
    
    def validate_migration(self, workflow_id: str) -> Dict[str, Any]:
        """Validate a migrated workflow"""
        try:
            # Get both versions
            legacy_workflow = file_storage.get_workflow(workflow_id)
            enhanced_workflow = file_storage.get_enhanced_workflow(workflow_id)
            
            if not legacy_workflow:
                return {"valid": False, "error": "Legacy workflow not found"}
            
            if not enhanced_workflow:
                return {"valid": False, "error": "Enhanced workflow not found"}
            
            # Compare key attributes
            validation_results = {
                "valid": True,
                "checks": {
                    "id_match": legacy_workflow.id == enhanced_workflow.id,
                    "name_match": legacy_workflow.name == enhanced_workflow.name,
                    "node_count_match": len(legacy_workflow.nodes) == len(enhanced_workflow.nodes),
                    "edge_count_match": len(legacy_workflow.edges) == len(enhanced_workflow.edges),
                    "has_migration_metadata": "migration" in enhanced_workflow.metadata
                }
            }
            
            # Check if all validations passed
            validation_results["valid"] = all(validation_results["checks"].values())
            
            return validation_results
            
        except Exception as e:
            return {"valid": False, "error": str(e)}


def create_setup_script():
    """Create a setup script for the enhanced workflow system"""
    setup_script = """
#!/bin/bash

# Enhanced Workflow System Setup Script

echo "Setting up Enhanced Workflow System..."

# Create required directories
echo "Creating directories..."
mkdir -p data/enhanced_workflows
mkdir -p data/executions
mkdir -p data/checkpoints
mkdir -p data/templates
mkdir -p logs

# Install Python dependencies (if needed)
echo "Checking Python dependencies..."
python -m pip install -r requirements.txt

# Run migrations
echo "Running workflow migrations..."
python scripts/migrate_workflows.py --run

# Create sample workflows and templates
echo "Creating sample workflows..."
python examples/workflows/sample_workflows.py

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start the server: python run.py"
echo "2. Visit http://localhost:8000 to access the interface"
echo "3. Check the enhanced workflows tab to see migrated workflows"
echo "4. Review migration report at: migration_report.json"
"""
    
    with open("setup_enhanced_workflows.sh", "w") as f:
        f.write(setup_script)
    
    # Make executable
    import os
    os.chmod("setup_enhanced_workflows.sh", 0o755)
    
    print("Created setup script: setup_enhanced_workflows.sh")


def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate legacy workflows to enhanced format")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without saving")
    parser.add_argument("--run", action="store_true", help="Perform actual migration")
    parser.add_argument("--validate", type=str, help="Validate specific workflow migration")
    parser.add_argument("--setup", action="store_true", help="Create setup script")
    
    args = parser.parse_args()
    
    migrator = WorkflowMigrator()
    
    if args.setup:
        create_setup_script()
        return
    
    if args.validate:
        result = migrator.validate_migration(args.validate)
        print(f"Validation result for workflow {args.validate}:")
        print(json.dumps(result, indent=2))
        return
    
    # Perform migration
    dry_run = not args.run
    
    if dry_run:
        print("Performing DRY RUN - no changes will be saved")
        print("Use --run flag to perform actual migration")
        print()
    
    # Run migration
    report = migrator.migrate_all_workflows(dry_run=dry_run)
    
    # Save report
    report_file = f"migration_report_{'dry_run' if dry_run else 'actual'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    print(f"Total workflows processed: {report['migration_summary']['statistics']['processed']}")
    print(f"Successfully migrated: {report['migration_summary']['statistics']['successful']}")
    print(f"Failed migrations: {report['migration_summary']['statistics']['failed']}")
    print(f"Skipped (already migrated): {report['migration_summary']['statistics']['skipped']}")
    print(f"Success rate: {report['migration_summary']['success_rate']:.1f}%")
    print(f"Report saved to: {report_file}")
    
    if report['migration_summary']['recommendations']:
        print("\nRECOMMENDations:")
        for rec in report['migration_summary']['recommendations']:
            print(f"- {rec}")


if __name__ == "__main__":
    main()