"""
Task splitting agent for DeepResearch system.
Specialized agent for breaking down research sections into actionable subtasks.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from utils.logger import LoggerMixin
from utils.json_utils import ResearchOutline, Section, SubSection
from llm.base import LLMWrapper


class TaskType(Enum):
    """Types of research tasks."""
    SEARCH = "search"           # Web search task
    ANALYSIS = "analysis"       # Data analysis task
    SYNTHESIS = "synthesis"     # Content synthesis task
    VERIFICATION = "verification"  # Fact verification task
    COMPARISON = "comparison"   # Comparative analysis task
    CASE_STUDY = "case_study"   # Case study research task


@dataclass
class ResearchTask:
    """Individual research task."""
    id: str
    title: str
    description: str
    task_type: TaskType
    priority: int  # 1-5, 5 being highest
    estimated_time: int  # in minutes
    dependencies: List[str]  # IDs of dependent tasks
    keywords: List[str]
    expected_output: str
    section_id: str
    subsection_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TaskSplitConfig:
    """Configuration for task splitting."""
    max_tasks_per_section: int = 5
    max_tasks_per_subsection: int = 3
    include_verification_tasks: bool = True
    include_synthesis_tasks: bool = True
    task_granularity: str = "medium"  # fine, medium, coarse


class TaskSplitter(LoggerMixin):
    """
    Specialized agent for splitting research sections into actionable tasks.
    Creates detailed task plans for content generation.
    """
    
    def __init__(self, llm_wrapper: LLMWrapper, config: TaskSplitConfig = None):
        """
        Initialize task splitter.
        
        Args:
            llm_wrapper: LLM wrapper for task generation
            config: Configuration for task splitting
        """
        self.llm = llm_wrapper
        self.config = config or TaskSplitConfig()
    
    async def split_outline_into_tasks(self, outline: ResearchOutline) -> List[ResearchTask]:
        """
        Split research outline into actionable tasks.
        
        Args:
            outline: Research outline to split
        
        Returns:
            List of research tasks
        """
        self.log_info(f"Splitting outline '{outline.title}' into tasks")
        
        all_tasks = []
        task_counter = 1
        
        try:
            for i, section in enumerate(outline.sections):
                section_id = f"section_{i+1}"
                
                # Generate section-level tasks
                section_tasks = await self._generate_section_tasks(
                    section, section_id, task_counter
                )
                all_tasks.extend(section_tasks)
                task_counter += len(section_tasks)
                
                # Generate subsection-level tasks
                for j, subsection in enumerate(section.subsections):
                    subsection_id = f"subsection_{j+1}"
                    subsection_tasks = await self._generate_subsection_tasks(
                        subsection, section, section_id, subsection_id, task_counter
                    )
                    all_tasks.extend(subsection_tasks)
                    task_counter += len(subsection_tasks)
            
            # Add synthesis and verification tasks
            if self.config.include_synthesis_tasks:
                synthesis_tasks = await self._generate_synthesis_tasks(outline, task_counter)
                all_tasks.extend(synthesis_tasks)
                task_counter += len(synthesis_tasks)
            
            if self.config.include_verification_tasks:
                verification_tasks = await self._generate_verification_tasks(outline, task_counter)
                all_tasks.extend(verification_tasks)
            
            self.log_info(f"Generated {len(all_tasks)} tasks from outline")
            return all_tasks
            
        except Exception as e:
            self.log_error(f"Task splitting failed: {e}")
            return []
    
    async def _generate_section_tasks(
        self, 
        section: Section, 
        section_id: str, 
        start_counter: int
    ) -> List[ResearchTask]:
        """Generate tasks for a research section."""
        
        system_prompt = f"""
        你是一个研究任务规划专家。请为给定的研究章节生成具体的研究任务。
        
        任务类型包括:
        - search: 网络搜索任务
        - analysis: 数据分析任务
        - synthesis: 内容综合任务
        - verification: 事实验证任务
        - comparison: 对比分析任务
        - case_study: 案例研究任务
        
        任务粒度: {self.config.task_granularity}
        最大任务数: {self.config.max_tasks_per_section}
        
        请以JSON格式返回任务列表:
        {{
            "tasks": [
                {{
                    "title": "任务标题",
                    "description": "详细描述需要完成的具体工作",
                    "task_type": "search|analysis|synthesis|verification|comparison|case_study",
                    "priority": 1-5,
                    "estimated_time": 30,
                    "keywords": ["关键词1", "关键词2"],
                    "expected_output": "期望的输出结果描述"
                }}
            ]
        }}
        """
        
        user_prompt = f"""
        章节信息:
        - 标题: {section.title}
        - 描述: {section.description}
        - 关键词: {', '.join(section.keywords)}
        - 预估字数: {section.estimated_length}
        
        请为这个章节生成具体的研究任务。
        """
        
        try:
            response = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.5
            )
            
            if response.is_success:
                import json
                try:
                    task_data = json.loads(response.content)
                    tasks = []
                    
                    for i, task_info in enumerate(task_data.get("tasks", [])):
                        task = ResearchTask(
                            id=f"task_{start_counter + i}",
                            title=task_info.get("title", ""),
                            description=task_info.get("description", ""),
                            task_type=TaskType(task_info.get("task_type", "search")),
                            priority=task_info.get("priority", 3),
                            estimated_time=task_info.get("estimated_time", 30),
                            dependencies=[],
                            keywords=task_info.get("keywords", []),
                            expected_output=task_info.get("expected_output", ""),
                            section_id=section_id
                        )
                        tasks.append(task)
                    
                    self.log_debug(f"Generated {len(tasks)} tasks for section: {section.title}")
                    return tasks
                    
                except json.JSONDecodeError as e:
                    self.log_error(f"Failed to parse task JSON: {e}")
                    
        except Exception as e:
            self.log_error(f"Error generating section tasks: {e}")
        
        # Fallback: create basic search task
        return [
            ResearchTask(
                id=f"task_{start_counter}",
                title=f"研究{section.title}",
                description=f"收集关于{section.title}的相关信息和资料",
                task_type=TaskType.SEARCH,
                priority=3,
                estimated_time=30,
                dependencies=[],
                keywords=section.keywords,
                expected_output=f"关于{section.title}的详细信息和分析",
                section_id=section_id
            )
        ]
    
    async def _generate_subsection_tasks(
        self,
        subsection: SubSection,
        parent_section: Section,
        section_id: str,
        subsection_id: str,
        start_counter: int
    ) -> List[ResearchTask]:
        """Generate tasks for a research subsection."""
        
        system_prompt = f"""
        你是一个研究任务规划专家。请为给定的研究子章节生成具体的研究任务。
        
        任务要求:
        - 任务应该具体、可执行
        - 考虑与上级章节的关联性
        - 最大任务数: {self.config.max_tasks_per_subsection}
        - 任务粒度: {self.config.task_granularity}
        
        请以JSON格式返回任务列表。
        """
        
        user_prompt = f"""
        上级章节: {parent_section.title}
        子章节信息:
        - 标题: {subsection.title}
        - 描述: {subsection.description}
        - 关键词: {', '.join(subsection.keywords)}
        - 预估字数: {subsection.estimated_length}
        
        请为这个子章节生成具体的研究任务。
        """
        
        try:
            response = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
                temperature=0.5
            )
            
            if response.is_success:
                import json
                try:
                    task_data = json.loads(response.content)
                    tasks = []
                    
                    for i, task_info in enumerate(task_data.get("tasks", [])):
                        task = ResearchTask(
                            id=f"task_{start_counter + i}",
                            title=task_info.get("title", ""),
                            description=task_info.get("description", ""),
                            task_type=TaskType(task_info.get("task_type", "search")),
                            priority=task_info.get("priority", 2),
                            estimated_time=task_info.get("estimated_time", 20),
                            dependencies=[],
                            keywords=task_info.get("keywords", []),
                            expected_output=task_info.get("expected_output", ""),
                            section_id=section_id,
                            subsection_id=subsection_id
                        )
                        tasks.append(task)
                    
                    return tasks
                    
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            self.log_error(f"Error generating subsection tasks: {e}")
        
        # Fallback task
        return [
            ResearchTask(
                id=f"task_{start_counter}",
                title=f"研究{subsection.title}",
                description=f"收集关于{subsection.title}的具体信息",
                task_type=TaskType.SEARCH,
                priority=2,
                estimated_time=20,
                dependencies=[],
                keywords=subsection.keywords,
                expected_output=f"关于{subsection.title}的详细内容",
                section_id=section_id,
                subsection_id=subsection_id
            )
        ]
    
    async def _generate_synthesis_tasks(
        self, 
        outline: ResearchOutline, 
        start_counter: int
    ) -> List[ResearchTask]:
        """Generate synthesis tasks for combining research results."""
        
        tasks = []
        
        # Overall synthesis task
        synthesis_task = ResearchTask(
            id=f"task_{start_counter}",
            title="整体内容综合",
            description="将各章节研究结果综合成连贯的报告",
            task_type=TaskType.SYNTHESIS,
            priority=4,
            estimated_time=60,
            dependencies=[],  # Will be set based on all section tasks
            keywords=outline.keywords,
            expected_output="完整的研究报告草稿",
            section_id="synthesis"
        )
        tasks.append(synthesis_task)
        
        return tasks
    
    async def _generate_verification_tasks(
        self, 
        outline: ResearchOutline, 
        start_counter: int
    ) -> List[ResearchTask]:
        """Generate verification tasks for fact-checking."""
        
        tasks = []
        
        # Fact verification task
        verification_task = ResearchTask(
            id=f"task_{start_counter}",
            title="事实验证",
            description="验证研究内容中的关键事实和数据",
            task_type=TaskType.VERIFICATION,
            priority=3,
            estimated_time=45,
            dependencies=[],
            keywords=["事实验证", "数据核实"],
            expected_output="验证报告和修正建议",
            section_id="verification"
        )
        tasks.append(verification_task)
        
        return tasks
    
    def optimize_task_dependencies(self, tasks: List[ResearchTask]) -> List[ResearchTask]:
        """
        Optimize task dependencies for efficient execution.
        
        Args:
            tasks: List of research tasks
        
        Returns:
            Tasks with optimized dependencies
        """
        self.log_info("Optimizing task dependencies")
        
        # Group tasks by type and section
        task_groups = {}
        for task in tasks:
            key = (task.section_id, task.task_type)
            if key not in task_groups:
                task_groups[key] = []
            task_groups[key].append(task)
        
        # Set dependencies based on logical flow
        for task in tasks:
            if task.task_type == TaskType.SYNTHESIS:
                # Synthesis tasks depend on all search and analysis tasks
                dependencies = [
                    t.id for t in tasks 
                    if t.task_type in [TaskType.SEARCH, TaskType.ANALYSIS] 
                    and t.section_id != "synthesis"
                ]
                task.dependencies = dependencies
            
            elif task.task_type == TaskType.VERIFICATION:
                # Verification depends on synthesis
                dependencies = [
                    t.id for t in tasks 
                    if t.task_type == TaskType.SYNTHESIS
                ]
                task.dependencies = dependencies
            
            elif task.task_type == TaskType.ANALYSIS:
                # Analysis depends on search tasks in the same section
                dependencies = [
                    t.id for t in tasks 
                    if t.task_type == TaskType.SEARCH 
                    and t.section_id == task.section_id
                ]
                task.dependencies = dependencies
        
        self.log_info(f"Optimized dependencies for {len(tasks)} tasks")
        return tasks
    
    def get_task_execution_order(self, tasks: List[ResearchTask]) -> List[List[ResearchTask]]:
        """
        Get optimal execution order for tasks.
        
        Args:
            tasks: List of research tasks
        
        Returns:
            List of task batches that can be executed in parallel
        """
        # Simple topological sort for task scheduling
        remaining_tasks = tasks.copy()
        execution_batches = []
        
        while remaining_tasks:
            # Find tasks with no unresolved dependencies
            ready_tasks = []
            completed_task_ids = set()
            
            # Collect IDs of completed tasks
            for batch in execution_batches:
                completed_task_ids.update(task.id for task in batch)
            
            for task in remaining_tasks:
                unresolved_deps = [
                    dep for dep in task.dependencies 
                    if dep not in completed_task_ids
                ]
                if not unresolved_deps:
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Break circular dependencies by taking highest priority task
                ready_tasks = [max(remaining_tasks, key=lambda t: t.priority)]
            
            execution_batches.append(ready_tasks)
            for task in ready_tasks:
                remaining_tasks.remove(task)
        
        self.log_info(f"Created {len(execution_batches)} execution batches")
        return execution_batches 