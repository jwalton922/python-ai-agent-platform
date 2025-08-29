import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import random
import string

from backend.models.workflow_enhanced import (
    EnhancedWorkflow,
    EnhancedWorkflowNode,
    NodeType,
    WorkflowExecutionState,
    WorkflowStatus
)
from backend.workflow.executor_enhanced import enhanced_workflow_executor


class WorkflowTestRunner:
    """Test runner for workflow validation and testing"""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.mock_data: Dict[str, Any] = {}
        self.assertions: List[Dict[str, Any]] = []
    
    async def run_tests(
        self,
        workflow: EnhancedWorkflow,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run test cases against a workflow"""
        results = {
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "test_count": len(test_cases),
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "test_results": [],
            "coverage": {}
        }
        
        for test_case in test_cases:
            result = await self._run_single_test(workflow, test_case)
            results["test_results"].append(result)
            
            if result["status"] == "passed":
                results["passed"] += 1
            elif result["status"] == "failed":
                results["failed"] += 1
            else:
                results["skipped"] += 1
        
        # Calculate coverage
        results["coverage"] = self._calculate_coverage(workflow, results["test_results"])
        
        return results
    
    async def _run_single_test(
        self,
        workflow: EnhancedWorkflow,
        test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a single test case"""
        test_name = test_case.get("name", "Unnamed Test")
        test_input = test_case.get("input", {})
        expected_output = test_case.get("expected_output")
        assertions = test_case.get("assertions", [])
        mocks = test_case.get("mocks", {})
        timeout = test_case.get("timeout", 30000)
        
        result = {
            "test_name": test_name,
            "status": "running",
            "execution_time_ms": 0,
            "errors": [],
            "assertions_passed": 0,
            "assertions_failed": 0,
            "nodes_executed": []
        }
        
        try:
            start_time = datetime.utcnow()
            
            # Apply mocks
            self._apply_mocks(mocks)
            
            # Execute workflow with test input
            execution_result = await asyncio.wait_for(
                enhanced_workflow_executor.execute_workflow(
                    workflow,
                    test_input
                ),
                timeout=timeout/1000
            )
            
            end_time = datetime.utcnow()
            result["execution_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
            
            # Check assertions
            for assertion in assertions:
                if self._check_assertion(assertion, execution_result):
                    result["assertions_passed"] += 1
                else:
                    result["assertions_failed"] += 1
                    result["errors"].append(f"Assertion failed: {assertion}")
            
            # Check expected output if provided
            if expected_output:
                if not self._compare_outputs(expected_output, execution_result.output):
                    result["errors"].append("Output does not match expected")
                    result["status"] = "failed"
                else:
                    result["status"] = "passed" if result["assertions_failed"] == 0 else "failed"
            else:
                result["status"] = "passed" if result["assertions_failed"] == 0 else "failed"
            
            # Record executed nodes
            result["nodes_executed"] = list(execution_result.node_results.keys())
            
        except asyncio.TimeoutError:
            result["status"] = "failed"
            result["errors"].append(f"Test timed out after {timeout}ms")
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
        finally:
            # Clear mocks
            self._clear_mocks()
        
        return result
    
    def _apply_mocks(self, mocks: Dict[str, Any]):
        """Apply mock data for testing"""
        self.mock_data = mocks
        
        # Would implement actual mocking of:
        # - Agent responses
        # - Tool executions
        # - External API calls
        # - Human inputs
    
    def _clear_mocks(self):
        """Clear mock data"""
        self.mock_data = {}
    
    def _check_assertion(
        self,
        assertion: Dict[str, Any],
        execution_result
    ) -> bool:
        """Check if an assertion passes"""
        assertion_type = assertion.get("type")
        
        if assertion_type == "node_executed":
            node_id = assertion.get("node_id")
            return node_id in execution_result.node_results
        
        elif assertion_type == "output_contains":
            expected = assertion.get("expected")
            actual = json.dumps(execution_result.output)
            return expected in actual
        
        elif assertion_type == "status_equals":
            expected_status = assertion.get("expected")
            return execution_result.status == expected_status
        
        elif assertion_type == "token_limit":
            max_tokens = assertion.get("max_tokens")
            return execution_result.tokens_used <= max_tokens
        
        elif assertion_type == "cost_limit":
            max_cost = assertion.get("max_cost")
            return execution_result.cost_usd <= max_cost
        
        elif assertion_type == "custom":
            # Execute custom assertion function
            func = assertion.get("function")
            if callable(func):
                return func(execution_result)
        
        return False
    
    def _compare_outputs(self, expected: Any, actual: Any) -> bool:
        """Compare expected and actual outputs"""
        if isinstance(expected, dict) and isinstance(actual, dict):
            for key, value in expected.items():
                if key not in actual:
                    return False
                if not self._compare_outputs(value, actual[key]):
                    return False
            return True
        elif isinstance(expected, list) and isinstance(actual, list):
            if len(expected) != len(actual):
                return False
            for exp, act in zip(expected, actual):
                if not self._compare_outputs(exp, act):
                    return False
            return True
        else:
            return expected == actual
    
    def _calculate_coverage(
        self,
        workflow: EnhancedWorkflow,
        test_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate test coverage metrics"""
        all_nodes = set(node.id for node in workflow.nodes)
        executed_nodes = set()
        
        for result in test_results:
            executed_nodes.update(result.get("nodes_executed", []))
        
        node_coverage = len(executed_nodes) / len(all_nodes) if all_nodes else 0
        
        # Calculate edge coverage
        all_edges = set(f"{e.source_node_id}->{e.target_node_id}" for e in workflow.edges)
        # Would need to track edge execution during tests
        edge_coverage = 0  # Placeholder
        
        # Calculate branch coverage for decision nodes
        decision_nodes = [n for n in workflow.nodes if n.type == NodeType.DECISION]
        branch_coverage = 0  # Would calculate based on branches taken
        
        return {
            "node_coverage": node_coverage,
            "nodes_covered": len(executed_nodes),
            "nodes_total": len(all_nodes),
            "uncovered_nodes": list(all_nodes - executed_nodes),
            "edge_coverage": edge_coverage,
            "branch_coverage": branch_coverage
        }


class WorkflowTestGenerator:
    """Generate test cases for workflows"""
    
    @staticmethod
    def generate_test_cases(
        workflow: EnhancedWorkflow,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate test cases automatically"""
        test_cases = []
        
        # Generate happy path test
        test_cases.append(
            WorkflowTestGenerator._generate_happy_path_test(workflow)
        )
        
        # Generate edge cases
        for i in range(min(count - 1, 3)):
            test_cases.append(
                WorkflowTestGenerator._generate_edge_case_test(workflow, i)
            )
        
        # Generate error cases
        if count > 4:
            test_cases.append(
                WorkflowTestGenerator._generate_error_test(workflow)
            )
        
        return test_cases
    
    @staticmethod
    def _generate_happy_path_test(workflow: EnhancedWorkflow) -> Dict[str, Any]:
        """Generate happy path test case"""
        test_input = {}
        
        # Generate input for required variables
        for var in workflow.variables:
            if var.required:
                test_input[var.name] = WorkflowTestGenerator._generate_value(var.type)
        
        return {
            "name": "Happy Path Test",
            "description": "Test normal workflow execution",
            "input": test_input,
            "assertions": [
                {"type": "status_equals", "expected": WorkflowStatus.COMPLETED},
                {"type": "node_executed", "node_id": node.id}
                for node in workflow.nodes
            ],
            "timeout": 60000
        }
    
    @staticmethod
    def _generate_edge_case_test(
        workflow: EnhancedWorkflow,
        case_index: int
    ) -> Dict[str, Any]:
        """Generate edge case test"""
        test_input = {}
        
        # Edge cases based on index
        if case_index == 0:
            # Empty optional values
            for var in workflow.variables:
                if var.required:
                    test_input[var.name] = WorkflowTestGenerator._generate_value(var.type)
                # Skip optional values
        
        elif case_index == 1:
            # Maximum values
            for var in workflow.variables:
                test_input[var.name] = WorkflowTestGenerator._generate_max_value(var.type)
        
        elif case_index == 2:
            # Minimum values
            for var in workflow.variables:
                test_input[var.name] = WorkflowTestGenerator._generate_min_value(var.type)
        
        return {
            "name": f"Edge Case Test {case_index + 1}",
            "description": "Test edge conditions",
            "input": test_input,
            "assertions": [
                {"type": "status_equals", "expected": WorkflowStatus.COMPLETED}
            ],
            "timeout": 60000
        }
    
    @staticmethod
    def _generate_error_test(workflow: EnhancedWorkflow) -> Dict[str, Any]:
        """Generate error test case"""
        return {
            "name": "Error Handling Test",
            "description": "Test error handling",
            "input": {},  # Missing required fields
            "assertions": [
                {"type": "status_equals", "expected": WorkflowStatus.FAILED}
            ],
            "timeout": 30000
        }
    
    @staticmethod
    def _generate_value(var_type: str) -> Any:
        """Generate a value based on type"""
        if var_type == "string":
            return "test_" + "".join(random.choices(string.ascii_lowercase, k=5))
        elif var_type == "number":
            return random.randint(1, 100)
        elif var_type == "boolean":
            return random.choice([True, False])
        elif var_type == "array":
            return [WorkflowTestGenerator._generate_value("string") for _ in range(3)]
        elif var_type == "object":
            return {
                "key1": WorkflowTestGenerator._generate_value("string"),
                "key2": WorkflowTestGenerator._generate_value("number")
            }
        return None
    
    @staticmethod
    def _generate_max_value(var_type: str) -> Any:
        """Generate maximum value for type"""
        if var_type == "string":
            return "x" * 1000
        elif var_type == "number":
            return 999999
        elif var_type == "boolean":
            return True
        elif var_type == "array":
            return [WorkflowTestGenerator._generate_value("string") for _ in range(100)]
        elif var_type == "object":
            return {f"key{i}": i for i in range(100)}
        return None
    
    @staticmethod
    def _generate_min_value(var_type: str) -> Any:
        """Generate minimum value for type"""
        if var_type == "string":
            return ""
        elif var_type == "number":
            return 0
        elif var_type == "boolean":
            return False
        elif var_type == "array":
            return []
        elif var_type == "object":
            return {}
        return None


class WorkflowDebugger:
    """Debug utilities for workflows"""
    
    @staticmethod
    async def trace_execution(
        workflow: EnhancedWorkflow,
        input_data: Dict[str, Any],
        breakpoints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Trace workflow execution with breakpoints"""
        trace = {
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "input": input_data,
            "steps": [],
            "variables": {},
            "errors": []
        }
        
        # Would implement step-by-step execution with breakpoints
        # For now, return basic trace
        
        try:
            # Create custom executor with tracing
            state = WorkflowExecutionState(
                execution_id=f"debug_{datetime.utcnow().isoformat()}",
                workflow_id=workflow.id,
                workflow_version=workflow.version,
                status=WorkflowStatus.RUNNING,
                started_at=datetime.utcnow(),
                global_variables=input_data
            )
            
            # Execute each node and record trace
            execution_plan = enhanced_workflow_executor._build_execution_plan(workflow)
            
            for node_id in execution_plan:
                node = next((n for n in workflow.nodes if n.id == node_id), None)
                if not node:
                    continue
                
                # Check for breakpoint
                if breakpoints and node_id in breakpoints:
                    trace["steps"].append({
                        "node_id": node_id,
                        "type": "breakpoint",
                        "message": f"Breakpoint hit at node {node_id}"
                    })
                
                # Record step
                step = {
                    "node_id": node_id,
                    "node_type": node.type.value,
                    "node_name": node.name,
                    "input": state.global_variables.copy(),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Execute node
                executor = enhanced_workflow_executor.node_executors.get(node.type)
                if executor:
                    try:
                        result = await executor.execute(node, state.global_variables, state)
                        step["output"] = result
                        step["success"] = result.get("success", False)
                    except Exception as e:
                        step["error"] = str(e)
                        step["success"] = False
                        trace["errors"].append({
                            "node_id": node_id,
                            "error": str(e)
                        })
                
                trace["steps"].append(step)
                
                # Update variables
                trace["variables"][node_id] = state.node_outputs.get(node_id, {})
            
        except Exception as e:
            trace["errors"].append({
                "global": str(e)
            })
        
        return trace
    
    @staticmethod
    def analyze_workflow(workflow: EnhancedWorkflow) -> Dict[str, Any]:
        """Analyze workflow for potential issues"""
        issues = []
        warnings = []
        suggestions = []
        
        # Check for disconnected nodes
        connected = set()
        for edge in workflow.edges:
            connected.add(edge.source_node_id)
            connected.add(edge.target_node_id)
        
        for node in workflow.nodes:
            if node.id not in connected and len(workflow.nodes) > 1:
                issues.append(f"Node '{node.name}' ({node.id}) is disconnected")
        
        # Check for missing agent IDs
        for node in workflow.nodes:
            if node.type == NodeType.AGENT and not node.agent_id:
                issues.append(f"Agent node '{node.name}' missing agent_id")
        
        # Check for infinite loops
        loop_nodes = [n for n in workflow.nodes if n.type == NodeType.LOOP]
        for node in loop_nodes:
            if node.loop_config:
                if not node.loop_config.max_iterations:
                    warnings.append(f"Loop node '{node.name}' has no max_iterations limit")
                elif node.loop_config.max_iterations > 1000:
                    warnings.append(f"Loop node '{node.name}' has very high max_iterations")
        
        # Check for performance issues
        if len(workflow.nodes) > 50:
            suggestions.append("Consider breaking workflow into sub-workflows for better maintainability")
        
        parallel_nodes = [n for n in workflow.nodes if n.type == NodeType.PARALLEL]
        if len(parallel_nodes) > 5:
            suggestions.append("Multiple parallel nodes may impact performance")
        
        # Check timeout settings
        if workflow.settings.max_execution_time_ms > 600000:  # 10 minutes
            warnings.append("Workflow has long maximum execution time (>10 minutes)")
        
        # Check for error handling
        if not workflow.global_error_handler:
            suggestions.append("Consider adding a global error handler")
        
        error_handler_nodes = [n for n in workflow.nodes if n.type == NodeType.ERROR_HANDLER]
        if not error_handler_nodes:
            suggestions.append("No error handler nodes found")
        
        return {
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "issues": issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "stats": {
                "node_count": len(workflow.nodes),
                "edge_count": len(workflow.edges),
                "complexity": len(workflow.nodes) + len(workflow.edges),
                "has_loops": len(loop_nodes) > 0,
                "has_parallel": len(parallel_nodes) > 0,
                "has_error_handling": len(error_handler_nodes) > 0
            }
        }


class WorkflowSimulator:
    """Simulate workflow execution without running actual operations"""
    
    @staticmethod
    async def simulate(
        workflow: EnhancedWorkflow,
        input_data: Dict[str, Any],
        iterations: int = 1
    ) -> Dict[str, Any]:
        """Simulate workflow execution"""
        results = {
            "workflow_id": workflow.id,
            "iterations": iterations,
            "simulated_executions": [],
            "avg_duration_ms": 0,
            "avg_tokens": 0,
            "avg_cost": 0.0,
            "success_rate": 0.0
        }
        
        successful = 0
        total_duration = 0
        total_tokens = 0
        total_cost = 0.0
        
        for i in range(iterations):
            # Simulate single execution
            execution = await WorkflowSimulator._simulate_single(workflow, input_data)
            results["simulated_executions"].append(execution)
            
            if execution["status"] == "completed":
                successful += 1
            
            total_duration += execution["estimated_duration_ms"]
            total_tokens += execution["estimated_tokens"]
            total_cost += execution["estimated_cost"]
        
        # Calculate averages
        results["avg_duration_ms"] = total_duration / iterations
        results["avg_tokens"] = total_tokens / iterations
        results["avg_cost"] = total_cost / iterations
        results["success_rate"] = successful / iterations
        
        return results
    
    @staticmethod
    async def _simulate_single(
        workflow: EnhancedWorkflow,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate single workflow execution"""
        execution = {
            "status": "completed",
            "estimated_duration_ms": 0,
            "estimated_tokens": 0,
            "estimated_cost": 0.0,
            "nodes_executed": [],
            "potential_issues": []
        }
        
        # Estimate based on node types and counts
        for node in workflow.nodes:
            execution["nodes_executed"].append(node.id)
            
            if node.type == NodeType.AGENT:
                # Estimate agent execution
                execution["estimated_duration_ms"] += random.randint(500, 2000)
                execution["estimated_tokens"] += random.randint(100, 1000)
                execution["estimated_cost"] += random.uniform(0.001, 0.01)
            
            elif node.type == NodeType.HUMAN_IN_LOOP:
                # Human input takes longer
                execution["estimated_duration_ms"] += random.randint(5000, 30000)
                execution["potential_issues"].append(f"Node {node.id} requires human input")
            
            elif node.type == NodeType.LOOP:
                # Loops multiply execution time
                if node.loop_config:
                    iterations = min(node.loop_config.max_iterations, 10)
                    execution["estimated_duration_ms"] += 100 * iterations
            
            elif node.type == NodeType.PARALLEL:
                # Parallel execution saves time
                execution["estimated_duration_ms"] += random.randint(200, 500)
            
            else:
                # Other nodes
                execution["estimated_duration_ms"] += random.randint(10, 100)
        
        # Random chance of failure
        if random.random() < 0.1:  # 10% failure rate
            execution["status"] = "failed"
            execution["potential_issues"].append("Simulated random failure")
        
        return execution


# Global instances
workflow_test_runner = WorkflowTestRunner()
workflow_test_generator = WorkflowTestGenerator()
workflow_debugger = WorkflowDebugger()
workflow_simulator = WorkflowSimulator()