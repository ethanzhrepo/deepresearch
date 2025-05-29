"""
Planner agent for DeepResearch system.
Specialized agent for multi-capability planning and tool selection.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from utils.logger import LoggerMixin
from llm.base import LLMWrapper
from agents.task_splitter import ResearchTask, TaskType
from mcp.planner import MCPPlanner, CapabilityType, ExecutionPlan


class PlanningStrategy(Enum):
    """Planning strategies for different scenarios."""
    SEQUENTIAL = "sequential"      # Execute tasks one by one
    PARALLEL = "parallel"          # Execute independent tasks in parallel
    ADAPTIVE = "adaptive"          # Adapt strategy based on task dependencies
    PRIORITY_BASED = "priority"    # Execute based on task priority


@dataclass
class PlannerConfig:
    """Configuration for planner agent."""
    default_strategy: PlanningStrategy = PlanningStrategy.ADAPTIVE
    max_parallel_tasks: int = 3
    enable_dynamic_replanning: bool = True
    resource_optimization: bool = True
    fallback_enabled: bool = True


class PlannerAgent(LoggerMixin):
    """
    Multi-capability planning agent.
    Orchestrates research tasks using various tools and capabilities.
    """
    
    def __init__(self, llm_wrapper: LLMWrapper, config: PlannerConfig = None):
        """
        Initialize planner agent.
        
        Args:
            llm_wrapper: LLM wrapper for planning decisions
            config: Configuration for planning behavior
        """
        self.llm = llm_wrapper
        self.config = config or PlannerConfig()
        self.mcp_planner = MCPPlanner()
        self.active_plans = {}
        self.execution_history = []
    
    async def create_execution_plan(
        self, 
        tasks: List[ResearchTask],
        constraints: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        Create comprehensive execution plan for research tasks.
        
        Args:
            tasks: List of research tasks to plan
            constraints: Optional execution constraints
        
        Returns:
            Detailed execution plan
        """
        self.log_info(f"Creating execution plan for {len(tasks)} tasks")
        
        try:
            # Analyze task requirements and dependencies
            task_analysis = await self._analyze_tasks(tasks)
            
            # Determine optimal capabilities for each task
            capability_mapping = await self._map_tasks_to_capabilities(tasks, task_analysis)
            
            # Create execution plan using MCP
            execution_plan = await self.mcp_planner.create_plan(
                tasks=tasks,
                capability_mapping=capability_mapping,
                constraints=constraints or {},
                strategy=self.config.default_strategy.value
            )
            
            # Optimize plan for resource efficiency
            if self.config.resource_optimization:
                execution_plan = await self._optimize_plan(execution_plan)
            
            self.log_info(f"Created execution plan with {len(execution_plan.execution_steps)} steps")
            return execution_plan
            
        except Exception as e:
            self.log_error(f"Failed to create execution plan: {e}")
            # Return fallback plan
            return await self._create_fallback_plan(tasks)
    
    async def _analyze_tasks(self, tasks: List[ResearchTask]) -> Dict[str, Any]:
        """Analyze tasks to understand requirements and complexity."""
        
        analysis = {
            "task_types": {},
            "complexity_scores": {},
            "resource_requirements": {},
            "dependency_graph": {},
            "estimated_duration": 0
        }
        
        # Count task types
        for task in tasks:
            task_type = task.task_type.value
            analysis["task_types"][task_type] = analysis["task_types"].get(task_type, 0) + 1
        
        # Analyze each task
        for task in tasks:
            # Complexity scoring
            complexity = await self._calculate_task_complexity(task)
            analysis["complexity_scores"][task.id] = complexity
            
            # Resource requirements
            resources = await self._estimate_resource_requirements(task)
            analysis["resource_requirements"][task.id] = resources
            
            # Dependencies
            analysis["dependency_graph"][task.id] = task.dependencies
            
            # Duration estimation
            analysis["estimated_duration"] += task.estimated_time
        
        self.log_debug(f"Task analysis completed: {analysis['task_types']}")
        return analysis
    
    async def _calculate_task_complexity(self, task: ResearchTask) -> float:
        """Calculate complexity score for a task."""
        
        # Base complexity by task type
        type_complexity = {
            TaskType.SEARCH: 0.3,
            TaskType.ANALYSIS: 0.7,
            TaskType.SYNTHESIS: 0.9,
            TaskType.VERIFICATION: 0.5,
            TaskType.COMPARISON: 0.6,
            TaskType.CASE_STUDY: 0.8
        }
        
        base_score = type_complexity.get(task.task_type, 0.5)
        
        # Adjust based on keywords count (more keywords = more complex)
        keyword_factor = min(len(task.keywords) * 0.1, 0.3)
        
        # Adjust based on dependencies
        dependency_factor = min(len(task.dependencies) * 0.05, 0.2)
        
        # Adjust based on estimated time
        time_factor = min(task.estimated_time / 60.0 * 0.1, 0.2)
        
        complexity = base_score + keyword_factor + dependency_factor + time_factor
        return min(complexity, 1.0)
    
    async def _estimate_resource_requirements(self, task: ResearchTask) -> Dict[str, Any]:
        """Estimate resource requirements for a task."""
        
        requirements = {
            "cpu_intensive": False,
            "network_required": True,
            "memory_usage": "low",
            "external_apis": [],
            "tools_needed": []
        }
        
        # Determine requirements based on task type
        if task.task_type == TaskType.SEARCH:
            requirements["external_apis"] = ["search_engine"]
            requirements["tools_needed"] = ["web_search"]
            
        elif task.task_type == TaskType.ANALYSIS:
            requirements["cpu_intensive"] = True
            requirements["memory_usage"] = "medium"
            requirements["tools_needed"] = ["python_executor", "data_analysis"]
            
        elif task.task_type == TaskType.SYNTHESIS:
            requirements["memory_usage"] = "high"
            requirements["tools_needed"] = ["content_synthesis"]
            
        elif task.task_type == TaskType.VERIFICATION:
            requirements["external_apis"] = ["search_engine", "fact_check"]
            requirements["tools_needed"] = ["web_search", "verification"]
            
        elif task.task_type == TaskType.COMPARISON:
            requirements["memory_usage"] = "medium"
            requirements["tools_needed"] = ["comparison_analysis"]
            
        elif task.task_type == TaskType.CASE_STUDY:
            requirements["external_apis"] = ["search_engine"]
            requirements["tools_needed"] = ["web_search", "case_analysis"]
        
        return requirements
    
    async def _map_tasks_to_capabilities(
        self, 
        tasks: List[ResearchTask],
        task_analysis: Dict[str, Any]
    ) -> Dict[str, List[CapabilityType]]:
        """Map tasks to required capabilities."""
        
        capability_mapping = {}
        
        for task in tasks:
            capabilities = []
            
            # Map based on task type
            if task.task_type == TaskType.SEARCH:
                capabilities.extend([CapabilityType.SEARCH, CapabilityType.LLM])
                
            elif task.task_type == TaskType.ANALYSIS:
                capabilities.extend([CapabilityType.SCRIPT, CapabilityType.LLM])
                
            elif task.task_type == TaskType.SYNTHESIS:
                capabilities.append(CapabilityType.LLM)
                
            elif task.task_type == TaskType.VERIFICATION:
                capabilities.extend([CapabilityType.SEARCH, CapabilityType.LLM])
                
            elif task.task_type == TaskType.COMPARISON:
                capabilities.extend([CapabilityType.LLM, CapabilityType.SEARCH])
                
            elif task.task_type == TaskType.CASE_STUDY:
                capabilities.extend([CapabilityType.SEARCH, CapabilityType.BROWSER, CapabilityType.LLM])
            
            # Add additional capabilities based on complexity
            complexity = task_analysis["complexity_scores"].get(task.id, 0.5)
            if complexity > 0.7:
                if CapabilityType.SCRIPT not in capabilities:
                    capabilities.append(CapabilityType.SCRIPT)
            
            capability_mapping[task.id] = capabilities
        
        return capability_mapping
    
    async def _optimize_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Optimize execution plan for better resource utilization."""
        
        self.log_info("Optimizing execution plan")
        
        # Group tasks that can be executed in parallel
        optimized_steps = []
        current_batch = []
        
        for step in plan.execution_steps:
            # Check if step can be batched with current batch
            can_batch = True
            
            # Check resource conflicts
            for existing_step in current_batch:
                if self._has_resource_conflict(step, existing_step):
                    can_batch = False
                    break
            
            # Check batch size limit
            if len(current_batch) >= self.config.max_parallel_tasks:
                can_batch = False
            
            if can_batch:
                current_batch.append(step)
            else:
                if current_batch:
                    optimized_steps.append(current_batch)
                current_batch = [step]
        
        # Add remaining batch
        if current_batch:
            optimized_steps.append(current_batch)
        
        # Update plan with optimized steps
        plan.execution_steps = optimized_steps
        plan.estimated_duration = self._calculate_optimized_duration(optimized_steps)
        
        self.log_info(f"Optimized plan: {len(optimized_steps)} batches")
        return plan
    
    def _has_resource_conflict(self, step1: Dict[str, Any], step2: Dict[str, Any]) -> bool:
        """Check if two execution steps have resource conflicts."""
        
        # Check if both require exclusive resources
        exclusive_resources = ["browser", "file_system"]
        
        step1_resources = step1.get("required_resources", [])
        step2_resources = step2.get("required_resources", [])
        
        for resource in exclusive_resources:
            if resource in step1_resources and resource in step2_resources:
                return True
        
        # Check API rate limits
        step1_apis = step1.get("required_apis", [])
        step2_apis = step2.get("required_apis", [])
        
        common_apis = set(step1_apis) & set(step2_apis)
        if common_apis:
            # Same API used - potential rate limit conflict
            return True
        
        return False
    
    def _calculate_optimized_duration(self, optimized_steps: List[List[Dict[str, Any]]]) -> int:
        """Calculate total duration for optimized execution plan."""
        
        total_duration = 0
        
        for batch in optimized_steps:
            # For parallel execution, duration is the maximum in the batch
            batch_duration = max(
                step.get("estimated_time", 30) for step in batch
            )
            total_duration += batch_duration
        
        return total_duration
    
    async def _create_fallback_plan(self, tasks: List[ResearchTask]) -> ExecutionPlan:
        """Create simple fallback execution plan."""
        
        self.log_warning("Creating fallback execution plan")
        
        execution_steps = []
        for task in tasks:
            step = {
                "task_id": task.id,
                "capabilities": [CapabilityType.LLM],
                "estimated_time": task.estimated_time,
                "required_resources": [],
                "required_apis": []
            }
            execution_steps.append([step])  # Each task in its own batch
        
        return ExecutionPlan(
            plan_id=f"fallback_{len(tasks)}",
            tasks=tasks,
            execution_steps=execution_steps,
            estimated_duration=sum(task.estimated_time for task in tasks),
            strategy="sequential",
            metadata={"fallback": True}
        )
    
    async def execute_plan(
        self, 
        plan: ExecutionPlan,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Execute the research plan.
        
        Args:
            plan: Execution plan to run
            progress_callback: Optional callback for progress updates
        
        Returns:
            Execution results
        """
        self.log_info(f"Executing plan {plan.plan_id}")
        
        execution_results = {
            "plan_id": plan.plan_id,
            "status": "running",
            "completed_tasks": [],
            "failed_tasks": [],
            "results": {},
            "start_time": None,
            "end_time": None
        }
        
        try:
            import time
            execution_results["start_time"] = time.time()
            
            # Execute plan using MCP
            results = await self.mcp_planner.execute_plan(plan, progress_callback)
            
            execution_results["results"] = results
            execution_results["status"] = "completed"
            execution_results["end_time"] = time.time()
            
            # Update execution history
            self.execution_history.append(execution_results)
            
            self.log_info(f"Plan execution completed successfully")
            return execution_results
            
        except Exception as e:
            self.log_error(f"Plan execution failed: {e}")
            execution_results["status"] = "failed"
            execution_results["error"] = str(e)
            execution_results["end_time"] = time.time()
            
            return execution_results
    
    async def replan_if_needed(
        self, 
        current_plan: ExecutionPlan,
        execution_context: Dict[str, Any]
    ) -> Optional[ExecutionPlan]:
        """
        Replan if current plan is not working well.
        
        Args:
            current_plan: Current execution plan
            execution_context: Current execution context and results
        
        Returns:
            New plan if replanning is needed, None otherwise
        """
        if not self.config.enable_dynamic_replanning:
            return None
        
        # Check if replanning is needed
        should_replan = await self._should_replan(current_plan, execution_context)
        
        if should_replan:
            self.log_info("Replanning due to execution issues")
            
            # Get remaining tasks
            remaining_tasks = self._get_remaining_tasks(current_plan, execution_context)
            
            # Create new plan with lessons learned
            constraints = self._extract_constraints_from_context(execution_context)
            new_plan = await self.create_execution_plan(remaining_tasks, constraints)
            
            return new_plan
        
        return None
    
    async def _should_replan(
        self, 
        plan: ExecutionPlan, 
        context: Dict[str, Any]
    ) -> bool:
        """Determine if replanning is necessary."""
        
        # Check failure rate
        total_tasks = len(context.get("completed_tasks", [])) + len(context.get("failed_tasks", []))
        failed_tasks = len(context.get("failed_tasks", []))
        
        if total_tasks > 0:
            failure_rate = failed_tasks / total_tasks
            if failure_rate > 0.3:  # More than 30% failure rate
                return True
        
        # Check if execution is taking too long
        if context.get("start_time"):
            import time
            elapsed_time = time.time() - context["start_time"]
            if elapsed_time > plan.estimated_duration * 2:  # Taking twice as long
                return True
        
        # Check resource availability
        if context.get("resource_issues", False):
            return True
        
        return False
    
    def _get_remaining_tasks(
        self, 
        plan: ExecutionPlan, 
        context: Dict[str, Any]
    ) -> List[ResearchTask]:
        """Get list of remaining tasks to execute."""
        
        completed_task_ids = set(context.get("completed_tasks", []))
        failed_task_ids = set(context.get("failed_tasks", []))
        processed_task_ids = completed_task_ids | failed_task_ids
        
        remaining_tasks = [
            task for task in plan.tasks 
            if task.id not in processed_task_ids
        ]
        
        return remaining_tasks
    
    def _extract_constraints_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract execution constraints from context."""
        
        constraints = {}
        
        # Add constraints based on failures
        if context.get("failed_tasks"):
            constraints["avoid_capabilities"] = []
            # Analyze failed tasks to avoid problematic capabilities
            
        # Add resource constraints
        if context.get("resource_issues"):
            constraints["max_parallel_tasks"] = max(1, self.config.max_parallel_tasks - 1)
        
        # Add time constraints
        if context.get("time_pressure"):
            constraints["prioritize_speed"] = True
        
        return constraints
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get statistics about past executions."""
        
        if not self.execution_history:
            return {"total_executions": 0}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(
            1 for exec_result in self.execution_history 
            if exec_result["status"] == "completed"
        )
        
        avg_duration = sum(
            exec_result.get("end_time", 0) - exec_result.get("start_time", 0)
            for exec_result in self.execution_history
            if exec_result.get("start_time") and exec_result.get("end_time")
        ) / total_executions if total_executions > 0 else 0
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "average_duration": avg_duration,
            "last_execution": self.execution_history[-1] if self.execution_history else None
        } 