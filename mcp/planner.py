"""
Multi-Capability Planning (MCP) system for DeepResearch.
Provides intelligent task planning and execution coordination.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from utils.logger import LoggerMixin
from config import config


class TaskType(Enum):
    """Types of tasks that can be executed."""
    SEARCH = "search"
    LLM_GENERATION = "llm_generation"
    CODE_EXECUTION = "code_execution"
    BROWSER_AUTOMATION = "browser_automation"
    BROWSER_USE = "browser_use"  # AI-powered browser automation
    FILE_OPERATION = "file_operation"
    DATA_ANALYSIS = "data_analysis"


class TaskStatus(Enum):
    """Status of task execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStrategy(Enum):
    """Execution strategies for task planning."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"
    PRIORITY = "priority"


@dataclass
class ExecutionStep:
    """Individual execution step in a plan."""
    step_id: str
    task_type: TaskType
    description: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1
    estimated_duration: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class ExecutionPlan:
    """Complete execution plan for a research task."""
    plan_id: str
    topic: str
    steps: List[ExecutionStep]
    strategy: ExecutionStrategy
    estimated_total_duration: float
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING


@dataclass
class ExecutionResult:
    """Result of plan execution."""
    plan_id: str
    success: bool
    total_duration: float
    completed_steps: int
    failed_steps: int
    results: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


class MCPPlanner(LoggerMixin):
    """
    Multi-Capability Planner for intelligent task orchestration.
    """
    
    def __init__(self, 
                 search_manager=None, 
                 code_runner=None, 
                 tool_registry=None,
                 resource_manager=None):
        """
        Initialize MCP planner with dependency injection support.
        
        Args:
            search_manager: SearchEngineManager instance (optional)
            code_runner: CodeRunner instance (optional)
            tool_registry: ToolRegistry instance (optional)
            resource_manager: ResourceManager instance (optional)
        """
        self.plans: Dict[str, ExecutionPlan] = {}
        self.execution_history: List[ExecutionResult] = []
        
        # 使用依赖注入或回退到默认初始化
        if search_manager or code_runner or tool_registry or resource_manager:
            # 使用注入的依赖
            self._initialize_with_dependencies(
                search_manager, code_runner, tool_registry, resource_manager
            )
        else:
            # 回退到传统初始化（向后兼容）
            self._initialize_tools()
        
        # 初始化异步工具执行器
        self._initialize_async_executor()
        
        # 配置
        self.max_concurrent_tasks = config.mcp.execution.batch_size
        self.timeout_per_batch = config.mcp.execution.timeout_per_batch
        self.failure_threshold = config.mcp.execution.failure_threshold
    
    def _initialize_with_dependencies(self, search_manager, code_runner, tool_registry, resource_manager):
        """
        Initialize with injected dependencies.
        
        Args:
            search_manager: SearchEngineManager instance
            code_runner: CodeRunner instance
            tool_registry: ToolRegistry instance
            resource_manager: ResourceManager instance
        """
        try:
            # 使用注入的依赖或从服务容器获取
            from utils.service_container import get_service_container
            container = get_service_container()
            
            self.search_manager = search_manager or container.get("search_manager")
            self.code_runner = code_runner or container.get("code_runner")
            self.tool_registry = tool_registry or container.get("tool_registry")
            self.resource_manager = resource_manager or container.get("resource_manager")
            
            # 初始化 LLM 包装器
            self._initialize_llm_wrappers()
            
            # 验证工具配置
            self._validate_tool_configs()
            
            self.log_info("MCP tools initialized with dependency injection")
            
        except Exception as e:
            self.log_error(f"Failed to initialize MCP tools with dependencies: {e}")
            # 回退到传统初始化
            self._initialize_tools()
    
    def _initialize_tools(self):
        """初始化工具管理器。"""
        try:
            # 搜索管理器 - 使用搜索工具配置
            try:
                from search.search_engine import SearchEngineManager
                search_config = getattr(config.tools, 'search_tool', None)
                # SearchEngineManager 从全局配置读取，不需要传递参数
                self.search_manager = SearchEngineManager()
                if search_config:
                    self.log_debug(f"Search manager initialized with config: enabled={getattr(search_config, 'enabled', True)}")
                else:
                    self.log_debug("Search manager initialized with default config")
            except ImportError as e:
                self.log_warning(f"Failed to import SearchEngineManager: {e}")
                self.search_manager = None
            
            # 代码执行器 - 使用代码工具配置
            try:
                from tools.code_executor import CodeRunner
                code_config = getattr(config.tools, 'code_tool', None)
                # CodeRunner 从全局配置读取，不需要传递参数
                self.code_runner = CodeRunner()
                if code_config:
                    self.log_debug(f"Code runner initialized with config: environment={getattr(code_config, 'execution_environment', 'default')}, sandbox={getattr(code_config, 'enable_sandbox', True)}")
                else:
                    self.log_debug("Code runner initialized with default config")
            except ImportError as e:
                self.log_warning(f"Failed to import CodeRunner: {e}")
                self.code_runner = None
            
            # 工具注册表
            try:
                from tools.tool_registry import ToolRegistry
                self.tool_registry = ToolRegistry()
                self.log_debug("Tool registry initialized")
            except ImportError as e:
                self.log_error(f"Failed to import ToolRegistry: {e}")
                self.tool_registry = None
            
            # 初始化 LLM 包装器
            self._initialize_llm_wrappers()
            
            # 验证工具配置
            self._validate_tool_configs()
            
            # 初始化异步执行器
            self._initialize_async_executor()
            
            self.log_info("MCP tools initialized successfully")
            
        except Exception as e:
            self.log_error(f"Failed to initialize MCP tools: {e}")
            import traceback
            self.log_debug(f"Traceback: {traceback.format_exc()}")
    
    def _initialize_llm_wrappers(self):
        """初始化 LLM 包装器。"""
        try:
            from llm.base import LLMWrapper
            from llm.openai import OpenAIWrapper
            from llm.claude import ClaudeWrapper
            from llm.gemini import GeminiWrapper
            from llm.ollama import OllamaWrapper
            from llm.deepseek import DeepSeekWrapper
            
            self.llm_wrappers = {}
            for provider in ['openai', 'claude', 'gemini', 'ollama', 'deepseek']:
                try:
                    llm_config = config.get_llm_config(provider)
                    if provider == "openai":
                        self.llm_wrappers[provider] = OpenAIWrapper(llm_config)
                    elif provider == "claude":
                        self.llm_wrappers[provider] = ClaudeWrapper(llm_config)
                    elif provider == "gemini":
                        self.llm_wrappers[provider] = GeminiWrapper(llm_config)
                    elif provider == "ollama":
                        self.llm_wrappers[provider] = OllamaWrapper(llm_config)
                    elif provider == "deepseek":
                        self.llm_wrappers[provider] = DeepSeekWrapper(llm_config)
                    self.log_debug(f"Initialized {provider} LLM wrapper")
                except Exception as e:
                    self.log_warning(f"Failed to initialize {provider}: {e}")
            
            self.log_debug(f"Initialized {len(self.llm_wrappers)} LLM wrappers")
            
        except Exception as e:
            self.log_error(f"Failed to initialize LLM wrappers: {e}")
            self.llm_wrappers = {}
    
    def _validate_tool_configs(self):
        """验证工具配置的一致性。"""
        try:
            # 验证代码执行器配置
            code_config = getattr(config.tools, 'code_tool', None)
            if code_config and hasattr(self.code_runner, 'environment'):
                expected_env = getattr(code_config, 'execution_environment', None)
                if expected_env:
                    actual_env = self.code_runner.environment.value if hasattr(self.code_runner.environment, 'value') else str(self.code_runner.environment)
                    if actual_env != expected_env:
                        self.log_warning(f"Code runner environment mismatch: expected {expected_env}, got {actual_env}")
                    else:
                        self.log_debug(f"Code runner environment validated: {actual_env}")
            
            # 验证搜索配置
            search_config = getattr(config.tools, 'search_tool', None)
            if search_config:
                enabled = getattr(search_config, 'enabled', True)
                if not enabled:
                    self.log_warning("Search tool is disabled in configuration")
                else:
                    self.log_debug("Search tool is enabled")
            
            # 验证浏览器配置
            browser_config = getattr(config.tools, 'browser_tool', None)
            if browser_config:
                enabled = getattr(browser_config, 'enabled', True)
                if not enabled:
                    self.log_warning("Browser tool is disabled in configuration")
                else:
                    self.log_debug("Browser tool is enabled")
            
            # 验证 LLM 配置
            llm_providers = list(self.llm_wrappers.keys())
            if llm_providers:
                self.log_debug(f"Available LLM providers: {llm_providers}")
            else:
                self.log_warning("No LLM providers available")
            
            self.log_debug("Tool configuration validation completed")
            
        except Exception as e:
            self.log_error(f"Tool configuration validation failed: {e}")
            import traceback
            self.log_debug(f"Validation traceback: {traceback.format_exc()}")
    
    def _initialize_async_executor(self):
        """初始化异步工具执行器。"""
        try:
            # 使用 ToolRegistry 管理的异步执行器
            self.async_executor = self.tool_registry.get_async_executor()
            self.log_debug("Async tool executor initialized via ToolRegistry")
        except Exception as e:
            self.log_error(f"Failed to initialize async executor: {e}")
            self.async_executor = None
    
    def create_research_plan(
        self,
        topic: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        Create a comprehensive research plan.
        
        Args:
            topic: Research topic
            requirements: Additional requirements
        
        Returns:
            ExecutionPlan for the research task
        """
        plan_id = f"research_{int(time.time())}"
        requirements = requirements or {}
        
        steps = []
        step_counter = 1
        
        # 1. 初始搜索步骤
        search_step = ExecutionStep(
            step_id=f"step_{step_counter}",
            task_type=TaskType.SEARCH,
            description=f"搜索关于 '{topic}' 的信息",
            parameters={
                "query": topic,
                "max_results": requirements.get("search_results", 10),
                "engines": ["duckduckgo", "google", "bing"]
            },
            priority=1,
            estimated_duration=30.0
        )
        steps.append(search_step)
        step_counter += 1
        
        # 2. 生成研究提纲
        outline_step = ExecutionStep(
            step_id=f"step_{step_counter}",
            task_type=TaskType.LLM_GENERATION,
            description="生成研究提纲",
            parameters={
                "task": "outline_generation",
                "topic": topic,
                "max_sections": requirements.get("max_sections", 5),
                "language": requirements.get("language", "zh-CN")
            },
            dependencies=[search_step.step_id],
            priority=2,
            estimated_duration=45.0
        )
        steps.append(outline_step)
        step_counter += 1
        
        # 3. 深度搜索各个章节
        for i in range(requirements.get("max_sections", 5)):
            section_search_step = ExecutionStep(
                step_id=f"step_{step_counter}",
                task_type=TaskType.SEARCH,
                description=f"搜索第 {i+1} 章节的详细信息",
                parameters={
                    "query": f"{topic} section {i+1}",
                    "max_results": 5,
                    "section_index": i
                },
                dependencies=[outline_step.step_id],
                priority=3,
                estimated_duration=20.0
            )
            steps.append(section_search_step)
            step_counter += 1
        
        # 4. 生成各章节内容
        section_dependencies = [s.step_id for s in steps if s.task_type == TaskType.SEARCH and "section" in s.description]
        
        for i in range(requirements.get("max_sections", 5)):
            content_step = ExecutionStep(
                step_id=f"step_{step_counter}",
                task_type=TaskType.LLM_GENERATION,
                description=f"生成第 {i+1} 章节内容",
                parameters={
                    "task": "content_generation",
                    "section_index": i,
                    "topic": topic,
                    "language": requirements.get("language", "zh-CN")
                },
                dependencies=section_dependencies,
                priority=4,
                estimated_duration=60.0
            )
            steps.append(content_step)
            step_counter += 1
        
        # 5. 数据分析（如果需要）
        if requirements.get("include_analysis", False):
            analysis_step = ExecutionStep(
                step_id=f"step_{step_counter}",
                task_type=TaskType.DATA_ANALYSIS,
                description="分析研究数据",
                parameters={
                    "analysis_type": "statistical",
                    "topic": topic
                },
                dependencies=[s.step_id for s in steps if s.task_type == TaskType.LLM_GENERATION],
                priority=5,
                estimated_duration=40.0
            )
            steps.append(analysis_step)
            step_counter += 1
        
        # 6. 最终报告生成
        final_step = ExecutionStep(
            step_id=f"step_{step_counter}",
            task_type=TaskType.LLM_GENERATION,
            description="生成最终研究报告",
            parameters={
                "task": "final_report",
                "topic": topic,
                "format": requirements.get("format", "markdown")
            },
            dependencies=[s.step_id for s in steps if s.task_type == TaskType.LLM_GENERATION and "content" in s.description],
            priority=6,
            estimated_duration=50.0
        )
        steps.append(final_step)
        
        # 计算总预估时间
        total_duration = sum(step.estimated_duration for step in steps)
        
        plan = ExecutionPlan(
            plan_id=plan_id,
            topic=topic,
            steps=steps,
            strategy=ExecutionStrategy.ADAPTIVE,
            estimated_total_duration=total_duration
        )
        
        self.plans[plan_id] = plan
        self.log_info(f"Created research plan {plan_id} with {len(steps)} steps")
        
        return plan
    
    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionResult:
        """
        Execute a research plan.
        
        Args:
            plan: ExecutionPlan to execute
        
        Returns:
            ExecutionResult with execution details
        """
        self.log_info(f"Starting execution of plan {plan.plan_id}")
        start_time = time.time()
        
        plan.status = TaskStatus.RUNNING
        results = {}
        errors = []
        completed_steps = 0
        failed_steps = 0
        
        try:
            if plan.strategy == ExecutionStrategy.SEQUENTIAL:
                # 顺序执行
                for step in plan.steps:
                    if self._check_dependencies(step, results):
                        result = await self._execute_step(step, results)
                        if result["success"]:
                            completed_steps += 1
                            results[step.step_id] = result
                        else:
                            failed_steps += 1
                            errors.append(f"Step {step.step_id}: {result.get('error', 'Unknown error')}")
                            
                            # 检查失败阈值
                            if failed_steps / len(plan.steps) > self.failure_threshold:
                                self.log_error("Failure threshold exceeded, stopping execution")
                                break
            
            elif plan.strategy == ExecutionStrategy.PARALLEL:
                # 并行执行
                await self._execute_parallel(plan, results, errors)
                completed_steps = len([r for r in results.values() if r.get("success")])
                failed_steps = len([r for r in results.values() if not r.get("success")])
            
            elif plan.strategy == ExecutionStrategy.ADAPTIVE:
                # 自适应执行
                await self._execute_adaptive(plan, results, errors)
                completed_steps = len([r for r in results.values() if r.get("success")])
                failed_steps = len([r for r in results.values() if not r.get("success")])
            
            plan.status = TaskStatus.COMPLETED if failed_steps == 0 else TaskStatus.FAILED
            
        except Exception as e:
            self.log_error(f"Plan execution failed: {e}")
            plan.status = TaskStatus.FAILED
            errors.append(str(e))
        
        total_duration = time.time() - start_time
        
        execution_result = ExecutionResult(
            plan_id=plan.plan_id,
            success=failed_steps == 0,
            total_duration=total_duration,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            results=results,
            errors=errors
        )
        
        self.execution_history.append(execution_result)
        self.log_info(f"Plan execution completed: {completed_steps} success, {failed_steps} failed")
        
        return execution_result
    
    async def _execute_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single step with retry logic.
        
        Args:
            step: ExecutionStep to execute
            context: Execution context with previous results
        
        Returns:
            Step execution result
        """
        step.start_time = datetime.now()
        step.status = TaskStatus.RUNNING
        
        for attempt in range(step.max_retries + 1):
            try:
                self.log_info(f"Executing step {step.step_id} (attempt {attempt + 1})")
                
                if step.task_type == TaskType.SEARCH:
                    result = await self._execute_search_step(step, context)
                elif step.task_type == TaskType.LLM_GENERATION:
                    result = await self._execute_llm_step(step, context)
                elif step.task_type == TaskType.CODE_EXECUTION:
                    result = await self._execute_code_step(step, context)
                elif step.task_type == TaskType.BROWSER_AUTOMATION:
                    result = await self._execute_browser_step(step, context)
                elif step.task_type == TaskType.BROWSER_USE:
                    result = await self._execute_browser_use_step(step, context)
                elif step.task_type == TaskType.FILE_OPERATION:
                    result = await self._execute_file_step(step, context)
                elif step.task_type == TaskType.DATA_ANALYSIS:
                    result = await self._execute_analysis_step(step, context)
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown task type: {step.task_type}"
                    }
                
                if result["success"]:
                    step.status = TaskStatus.COMPLETED
                    step.result = result["data"]
                    step.end_time = datetime.now()
                    return result
                else:
                    step.retry_count += 1
                    if attempt < step.max_retries:
                        self.log_warning(f"Step {step.step_id} failed, retrying...")
                        await asyncio.sleep(2 ** attempt)  # 指数退避
                    else:
                        step.status = TaskStatus.FAILED
                        step.error = result.get("error", "Unknown error")
                        step.end_time = datetime.now()
                        return result
                        
            except Exception as e:
                step.retry_count += 1
                error_msg = str(e)
                self.log_error(f"Step {step.step_id} execution error: {error_msg}")
                
                if attempt < step.max_retries:
                    await asyncio.sleep(2 ** attempt)
                else:
                    step.status = TaskStatus.FAILED
                    step.error = error_msg
                    step.end_time = datetime.now()
                    return {"success": False, "error": error_msg}
        
        return {"success": False, "error": "Max retries exceeded"}
    
    async def _execute_search_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行搜索步骤。"""
        try:
            query = step.parameters.get("query", "")
            max_results = step.parameters.get("max_results", 10)
            engines = step.parameters.get("engines", ["duckduckgo"])
            
            # 如果查询依赖于之前的结果，进行动态构建
            if "section_index" in step.parameters:
                section_index = step.parameters["section_index"]
                # 从提纲生成步骤获取章节信息
                outline_result = None
                for result in context.values():
                    if result.get("task") == "outline_generation":
                        outline_result = result
                        break
                
                if outline_result and "sections" in outline_result.get("data", {}):
                    sections = outline_result["data"]["sections"]
                    if section_index < len(sections):
                        section = sections[section_index]
                        query = f"{query} {section.get('title', '')} {' '.join(section.get('keywords', []))}"
            
            # 使用异步执行器执行搜索工具
            search_tool = self.tool_registry.get_tool("web_search")
            if search_tool and self.async_executor:
                result = await self.async_executor.execute_tool(
                    search_tool,
                    query,
                    timeout=step.estimated_duration
                )
                
                if result.success:
                    # 解析搜索结果 - 统一格式化为结构化数据
                    search_output = result.data
                    
                    # 尝试解析搜索结果为结构化格式
                    parsed_results = self._parse_search_output(search_output)
                    
                    return {
                        "success": True,
                        "data": {
                            "query": query,
                            "results": parsed_results,
                            "search_output": search_output,  # 保留原始输出
                            "count": len(parsed_results)
                        },
                        "task": "search",
                        "execution_time": result.execution_time
                    }
                else:
                    return {"success": False, "error": result.error}
            else:
                # 回退到直接使用搜索管理器
                results = self.search_manager.search(
                    query=query,
                    max_results=max_results
                )
                
                return {
                    "success": True,
                    "data": {
                        "query": query,
                        "results": [
                            {
                                "title": r.title,
                                "url": r.url,
                                "snippet": r.snippet,
                                "source": r.source
                            } for r in results
                        ],
                        "count": len(results)
                    },
                    "task": "search"
                }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_llm_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 LLM 生成步骤。"""
        try:
            task = step.parameters.get("task", "")
            topic = step.parameters.get("topic", "")
            
            # 选择 LLM 提供商（支持任务特定配置）
            provider, llm_params = self._select_llm_for_task(task, step.parameters)
            
            if provider not in self.llm_wrappers:
                provider = list(self.llm_wrappers.keys())[0] if self.llm_wrappers else None
            
            if not provider:
                return {"success": False, "error": "No LLM provider available"}
            
            llm = self.llm_wrappers[provider]
            
            if task == "outline_generation":
                return await self._generate_outline(llm, step, context, llm_params)
            elif task == "content_generation":
                return await self._generate_content(llm, step, context, llm_params)
            elif task == "final_report":
                return await self._generate_final_report(llm, step, context, llm_params)
            else:
                return {"success": False, "error": f"Unknown LLM task: {task}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_llm_parameters(self, step_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """从步骤参数中提取 LLM 特定参数。"""
        llm_params = {}
        
        # 支持的 LLM 参数
        llm_param_keys = [
            'max_tokens', 'temperature', 'top_p', 'top_k', 
            'frequency_penalty', 'presence_penalty', 'stop',
            'model', 'stream'
        ]
        
        for key in llm_param_keys:
            if key in step_parameters:
                llm_params[key] = step_parameters[key]
        
        # 设置默认值
        if 'max_tokens' not in llm_params:
            llm_params['max_tokens'] = 2000
        if 'temperature' not in llm_params:
            llm_params['temperature'] = 0.7
        
        return llm_params
    
    def _select_llm_for_task(self, task: str, step_parameters: Dict[str, Any]) -> tuple:
        """为特定任务选择最适合的 LLM 提供商和参数。"""
        # 优先级：步骤参数 > 任务特定配置 > 默认配置
        
        # 1. 检查步骤参数中的显式指定
        if "llm_provider" in step_parameters:
            provider = step_parameters["llm_provider"]
            llm_params = self._extract_llm_parameters(step_parameters)
            return provider, llm_params
        
        # 2. 检查任务特定配置
        task_specific_config = getattr(config.llm, 'task_specific_models', {})
        if task in task_specific_config:
            task_config = task_specific_config[task]
            provider = task_config.get("provider", config.llm.default_provider)
            
            # 合并任务特定参数和步骤参数
            llm_params = {}
            
            # 从任务配置中提取参数
            for key in ['model', 'temperature', 'max_tokens', 'top_p', 'top_k', 
                       'frequency_penalty', 'presence_penalty', 'stop']:
                if key in task_config:
                    llm_params[key] = task_config[key]
            
            # 步骤参数覆盖任务配置
            step_params = self._extract_llm_parameters(step_parameters)
            llm_params.update(step_params)
            
            self.log_debug(f"Using task-specific LLM config for {task}: {provider} with params {llm_params}")
            return provider, llm_params
        
        # 3. 使用默认配置
        provider = config.llm.default_provider
        llm_params = self._extract_llm_parameters(step_parameters)
        
        self.log_debug(f"Using default LLM config for {task}: {provider}")
        return provider, llm_params
    
    async def _generate_outline(self, llm, step: ExecutionStep, context: Dict[str, Any], llm_params: Dict[str, Any]) -> Dict[str, Any]:
        """生成研究提纲。"""
        topic = step.parameters.get("topic", "")
        max_sections = step.parameters.get("max_sections", 5)
        language = step.parameters.get("language", "zh-CN")
        
        # 获取搜索结果作为上下文
        search_context = ""
        for result in context.values():
            if result.get("task") == "search" and "results" in result.get("data", {}):
                search_results = result["data"]["results"][:3]
                search_context += "\n参考信息:\n"
                for sr in search_results:
                    search_context += f"- {sr['title']}: {sr['snippet']}\n"
        
        system_prompt = f"""
        你是一个专业的研究助手。请为给定的研究主题生成一个详细的研究提纲。
        
        要求:
        1. 提纲应该包含 {max_sections} 个主要章节
        2. 每个章节应该有 2-3 个子章节
        3. 提供每个章节的简要描述和关键词
        4. 使用 {language} 语言
        
        请以JSON格式返回提纲。
        """
        
        user_prompt = f"请为以下研究主题生成详细的研究提纲：{topic}\n{search_context}"
        
        # 使用传入的 LLM 参数
        response = llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            **llm_params  # 展开 LLM 参数
        )
        
        if response.is_success:
            # 解析提纲
            try:
                import json
                outline_data = json.loads(response.content)
                return {
                    "success": True,
                    "data": outline_data,
                    "task": "outline_generation"
                }
            except json.JSONDecodeError:
                # 如果不是有效的JSON，返回文本内容
                return {
                    "success": True,
                    "data": {"outline_text": response.content},
                    "task": "outline_generation"
                }
        else:
            return {"success": False, "error": response.error}
    
    async def _generate_content(self, llm, step: ExecutionStep, context: Dict[str, Any], llm_params: Dict[str, Any]) -> Dict[str, Any]:
        """生成章节内容。"""
        topic = step.parameters.get("topic", "")
        section_index = step.parameters.get("section_index", 0)
        language = step.parameters.get("language", "zh-CN")
        
        # 获取提纲信息
        outline_data = None
        for result in context.values():
            if result.get("task") == "outline_generation":
                outline_data = result.get("data", {})
                break
        
        # 获取相关搜索结果
        search_context = ""
        for result in context.values():
            if (result.get("task") == "search" and 
                "section_index" in result.get("data", {}) and
                result["data"]["section_index"] == section_index):
                search_results = result["data"]["results"][:3]
                search_context += "\n参考资料:\n"
                for sr in search_results:
                    search_context += f"- {sr['title']}: {sr['snippet']}\n"
        
        # 构建章节信息
        section_info = ""
        if outline_data and "sections" in outline_data:
            sections = outline_data["sections"]
            if section_index < len(sections):
                section = sections[section_index]
                section_info = f"章节标题: {section.get('title', '')}\n"
                section_info += f"章节描述: {section.get('description', '')}\n"
                section_info += f"关键词: {', '.join(section.get('keywords', []))}\n"
        
        system_prompt = f"""
        你是一个专业的研究写作助手。请为给定的研究章节生成详细的内容。
        
        要求:
        1. 内容应该专业、准确、有深度
        2. 字数约 800-1200 字
        3. 使用 {language} 语言
        4. 结构清晰，逻辑严密
        5. 如果有参考资料，请合理引用
        """
        
        user_prompt = f"""
        研究主题: {topic}
        {section_info}
        
        请生成这个章节的详细内容。
        
        {search_context}
        """
        
        response = llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            **llm_params
        )
        
        if response.is_success:
            return {
                "success": True,
                "data": {
                    "section_index": section_index,
                    "content": response.content
                },
                "task": "content_generation"
            }
        else:
            return {"success": False, "error": response.error}
    
    async def _generate_final_report(self, llm, step: ExecutionStep, context: Dict[str, Any], llm_params: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终报告。"""
        topic = step.parameters.get("topic", "")
        format_type = step.parameters.get("format", "markdown")
        
        # 收集所有章节内容
        sections_content = []
        for result in context.values():
            if result.get("task") == "content_generation":
                data = result.get("data", {})
                sections_content.append({
                    "index": data.get("section_index", 0),
                    "content": data.get("content", "")
                })
        
        # 按索引排序
        sections_content.sort(key=lambda x: x["index"])
        
        # 构建完整内容
        full_content = f"# {topic}\n\n"
        for i, section in enumerate(sections_content):
            full_content += f"## 第 {i+1} 章\n\n"
            full_content += section["content"] + "\n\n"
        
        system_prompt = f"""
        你是一个专业的报告编辑。请将给定的章节内容整理成一份完整的研究报告。
        
        要求:
        1. 添加适当的标题和结构
        2. 确保内容连贯性
        3. 添加摘要和结论
        4. 使用 {format_type} 格式
        5. 保持专业性和可读性
        """
        
        user_prompt = f"""
        请将以下内容整理成一份完整的研究报告：
        
        {full_content}
        """
        
        response = llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            **llm_params
        )
        
        if response.is_success:
            return {
                "success": True,
                "data": {
                    "final_report": response.content,
                    "format": format_type,
                    "sections_count": len(sections_content)
                },
                "task": "final_report"
            }
        else:
            return {"success": False, "error": response.error}
    
    async def _execute_code_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码步骤。"""
        try:
            code = step.parameters.get("code", "")
            language = step.parameters.get("language", "python")
            
            # 使用异步执行器执行代码工具
            code_tool = self.tool_registry.get_tool("python_executor")
            if code_tool and self.async_executor:
                result = await self.async_executor.execute_tool(
                    code_tool,
                    code,
                    timeout=step.estimated_duration
                )
                
                # 统一代码执行结果格式
                if result.success:
                    return {
                        "success": True,
                        "data": {
                            "output": result.data,
                            "execution_time": result.execution_time,
                            "stdout": result.data,  # 兼容性字段
                            "return_value": None
                        },
                        "task": "code_execution"
                    }
                else:
                    return {
                        "success": False,
                        "data": {
                            "output": "",
                            "execution_time": result.execution_time,
                            "stderr": result.error
                        },
                        "error": result.error,
                        "task": "code_execution"
                    }
            else:
                # 回退到直接使用代码执行器
                result = self.code_runner.execute_code(code, language)
                
                return {
                    "success": result.success,
                    "data": {
                        "output": result.output,
                        "execution_time": result.execution_time
                    },
                    "error": result.error if not result.success else None,
                    "task": "code_execution"
                }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_browser_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行浏览器自动化步骤。"""
        try:
            action = step.parameters.get("action", "")
            url = step.parameters.get("url", "")
            
            # 优先尝试使用 browser_use 工具（AI 驱动）
            browser_use_tool = self.tool_registry.get_tool("browser_use")
            if browser_use_tool:
                # 构建 browser_use 输入数据
                import json
                
                # 根据动作类型构建参数
                if action == "search":
                    input_data = json.dumps({
                        "action": "search_and_extract",
                        "parameters": {
                            "query": step.parameters.get("query", ""),
                            "search_engine": step.parameters.get("search_engine", "google")
                        }
                    })
                elif action == "navigate":
                    input_data = json.dumps({
                        "action": "navigate_and_extract",
                        "parameters": {
                            "url": url,
                            "extraction_task": step.parameters.get("extraction_task", "Extract all important information from this page")
                        }
                    })
                elif action == "fill_form":
                    input_data = json.dumps({
                        "action": "fill_form",
                        "parameters": {
                            "url": url,
                            "form_data": step.parameters.get("form_data", {}),
                            "submit": step.parameters.get("submit", False)
                        }
                    })
                elif action == "workflow":
                    input_data = json.dumps({
                        "action": "automate_workflow",
                        "parameters": {
                            "workflow_steps": step.parameters.get("workflow_steps", [])
                        }
                    })
                else:
                    # 自定义任务
                    input_data = json.dumps({
                        "action": "custom_task",
                        "parameters": {
                            "task_description": step.parameters.get("task_description", f"Execute browser action: {action}"),
                            "url": url,
                            "max_steps": step.parameters.get("max_steps", 30),
                            "headless": step.parameters.get("headless", True)
                        }
                    })
                
                # 使用异步执行器执行 browser_use 工具
                if self.async_executor:
                    result = await self.async_executor.execute_tool(
                        browser_use_tool,
                        input_data,
                        timeout=step.estimated_duration
                    )
                    
                    return {
                        "success": result.success,
                        "data": {"result": result.data},
                        "error": result.error,
                        "task": "browser_use",
                        "execution_time": result.execution_time
                    }
                else:
                    # 回退到同步执行
                    result = browser_use_tool._run(input_data)
                    return {
                        "success": True,
                        "data": {"result": result},
                        "task": "browser_use"
                    }
            
            # 回退到传统的 browser_automation 工具
            browser_tool = self.tool_registry.get_tool("browser_automation")
            if not browser_tool:
                return {"success": False, "error": "No browser tools available"}
            
            # 构建输入数据
            import json
            input_data = json.dumps({"action": action, "url": url})
            
            # 使用异步执行器执行工具
            if self.async_executor:
                result = await self.async_executor.execute_tool(
                    browser_tool,
                    input_data,
                    timeout=step.estimated_duration
                )
                
                return {
                    "success": result.success,
                    "data": {"result": result.data},
                    "error": result.error,
                    "task": "browser_automation",
                    "execution_time": result.execution_time
                }
            else:
                # 回退到同步执行
                result = browser_tool._run(input_data)
                return {
                    "success": True,
                    "data": {"result": result},
                    "task": "browser_automation"
                }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_browser_use_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Browser-Use AI 驱动的浏览器自动化步骤。"""
        try:
            browser_use_tool = self.tool_registry.get_tool("browser_use")
            if not browser_use_tool:
                return {"success": False, "error": "Browser-Use tool not available"}
            
            # 构建输入数据
            import json
            action = step.parameters.get("action", "custom_task")
            
            # 根据动作类型构建参数
            if action == "search_and_extract":
                input_data = json.dumps({
                    "action": "search_and_extract",
                    "parameters": {
                        "query": step.parameters.get("query", ""),
                        "search_engine": step.parameters.get("search_engine", "google")
                    }
                })
            elif action == "navigate_and_extract":
                input_data = json.dumps({
                    "action": "navigate_and_extract",
                    "parameters": {
                        "url": step.parameters.get("url", ""),
                        "extraction_task": step.parameters.get("extraction_task", "Extract all important information from this page")
                    }
                })
            elif action == "fill_form":
                input_data = json.dumps({
                    "action": "fill_form",
                    "parameters": {
                        "url": step.parameters.get("url", ""),
                        "form_data": step.parameters.get("form_data", {}),
                        "submit": step.parameters.get("submit", False)
                    }
                })
            elif action == "monitor_changes":
                input_data = json.dumps({
                    "action": "monitor_changes",
                    "parameters": {
                        "url": step.parameters.get("url", ""),
                        "element_selector": step.parameters.get("element_selector", ""),
                        "check_interval": step.parameters.get("check_interval", 60),
                        "max_checks": step.parameters.get("max_checks", 10)
                    }
                })
            elif action == "automate_workflow":
                input_data = json.dumps({
                    "action": "automate_workflow",
                    "parameters": {
                        "workflow_steps": step.parameters.get("workflow_steps", [])
                    }
                })
            else:
                # 自定义任务
                input_data = json.dumps({
                    "action": "custom_task",
                    "parameters": {
                        "task_description": step.parameters.get("task_description", "Execute browser automation task"),
                        "url": step.parameters.get("url"),
                        "max_steps": step.parameters.get("max_steps", 50),
                        "headless": step.parameters.get("headless", True),
                        "timeout": step.parameters.get("timeout", 300)
                    }
                })
            
            # 使用异步执行器执行工具
            if self.async_executor:
                result = await self.async_executor.execute_tool(
                    browser_use_tool,
                    input_data,
                    timeout=step.estimated_duration
                )
                
                return {
                    "success": result.success,
                    "data": {"result": result.data},
                    "error": result.error,
                    "task": "browser_use",
                    "execution_time": result.execution_time
                }
            else:
                # 回退到同步执行
                result = browser_use_tool._run(input_data)
                return {
                    "success": True,
                    "data": {"result": result},
                    "task": "browser_use"
                }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_file_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件操作步骤。"""
        try:
            file_info = step.parameters.get("file_info", {})
            
            file_tool = self.tool_registry.get_tool("file_reader")
            if not file_tool:
                return {"success": False, "error": "File tool not available"}
            
            # 构建输入数据
            import json
            input_data = json.dumps(file_info)
            
            # 使用异步执行器执行文件工具
            if self.async_executor:
                result = await self.async_executor.execute_tool(
                    file_tool,
                    input_data,
                    timeout=step.estimated_duration
                )
                
                return {
                    "success": result.success,
                    "data": {"result": result.data},
                    "error": result.error,
                    "task": "file_operation",
                    "execution_time": result.execution_time
                }
            else:
                # 回退到同步执行
                result = file_tool._run(input_data)
                return {
                    "success": True,
                    "data": {"result": result},
                    "task": "file_operation"
                }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_analysis_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据分析步骤。"""
        try:
            analysis_type = step.parameters.get("analysis_type", "basic")
            topic = step.parameters.get("topic", "")
            
            # 生成分析代码
            analysis_code = self._generate_analysis_code(analysis_type, topic, context)
            
            # 执行分析代码
            result = self.code_runner.execute_code(analysis_code, "python")
            
            return {
                "success": result.success,
                "data": {
                    "analysis_output": result.output,
                    "analysis_type": analysis_type
                },
                "error": result.error if not result.success else None,
                "task": "data_analysis"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_analysis_code(self, analysis_type: str, topic: str, context: Dict[str, Any]) -> str:
        """生成数据分析代码。"""
        if analysis_type == "statistical":
            return self._generate_statistical_analysis_code(topic, context)
        elif analysis_type == "content":
            return self._generate_content_analysis_code(topic, context)
        elif analysis_type == "trend":
            return self._generate_trend_analysis_code(topic, context)
        elif analysis_type == "sentiment":
            return self._generate_sentiment_analysis_code(topic, context)
        else:
            return self._generate_basic_analysis_code(topic, analysis_type)
    
    def _generate_statistical_analysis_code(self, topic: str, context: Dict[str, Any]) -> str:
        """生成统计分析代码。"""
        return f'''
# 统计分析代码 - {topic}
import json
from collections import Counter, defaultdict
import re
from datetime import datetime

print(f"=== 统计分析报告: {topic} ===")
print(f"分析时间: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")

# 从上下文中提取搜索结果
search_results = []
content_sections = []

context_data = {context}

for result in context_data.values():
    if result.get("task") == "search":
        search_results.extend(result.get("data", {{}}).get("results", []))
    elif result.get("task") == "content_generation":
        content_sections.append(result.get("data", {{}}).get("content", ""))

print(f"\\n📊 数据概览:")
print(f"  搜索结果数量: {{len(search_results)}}")
print(f"  内容章节数量: {{len(content_sections)}}")

# 分析搜索结果来源分布
if search_results:
    print(f"\\n🔍 搜索结果分析:")
    sources = [r.get("source", "unknown") for r in search_results]
    source_counts = Counter(sources)
    
    for source, count in source_counts.most_common():
        percentage = (count / len(search_results)) * 100
        print(f"  {{source}}: {{count}} ({{percentage:.1f}}%)")
    
    # 分析标题关键词
    all_titles = " ".join([r.get("title", "") for r in search_results])
    words = re.findall(r'\\b\\w{{3,}}\\b', all_titles.lower())
    word_counts = Counter(words)
    
    print(f"\\n🔤 标题关键词 (Top 10):")
    for word, count in word_counts.most_common(10):
        print(f"  {{word}}: {{count}}")

# 分析内容长度分布
if content_sections:
    print(f"\\n📝 内容分析:")
    lengths = [len(content) for content in content_sections]
    avg_length = sum(lengths) / len(lengths)
    min_length = min(lengths)
    max_length = max(lengths)
    
    print(f"  平均长度: {{avg_length:.0f}} 字符")
    print(f"  最短章节: {{min_length}} 字符")
    print(f"  最长章节: {{max_length}} 字符")
    
    # 词频分析
    all_content = " ".join(content_sections)
    content_words = re.findall(r'\\b\\w{{2,}}\\b', all_content.lower())
    content_word_counts = Counter(content_words)
    
    print(f"\\n📈 内容词频 (Top 15):")
    for word, count in content_word_counts.most_common(15):
        if len(word) > 2:  # 过滤短词
            print(f"  {{word}}: {{count}}")

print(f"\\n✅ 统计分析完成")
'''
    
    def _generate_content_analysis_code(self, topic: str, context: Dict[str, Any]) -> str:
        """生成内容分析代码。"""
        return f'''
# 内容分析代码 - {topic}
import re
from collections import Counter
import json

print(f"=== 内容质量分析: {topic} ===")

# 提取内容数据
content_sections = []
context_data = {context}

for result in context_data.values():
    if result.get("task") == "content_generation":
        content = result.get("data", {{}}).get("content", "")
        if content:
            content_sections.append(content)

if not content_sections:
    print("❌ 没有找到内容数据")
else:
    print(f"📄 分析 {{len(content_sections)}} 个内容章节")
    
    # 内容质量指标
    total_chars = sum(len(content) for content in content_sections)
    total_words = sum(len(re.findall(r'\\b\\w+\\b', content)) for content in content_sections)
    total_sentences = sum(len(re.findall(r'[.!?]+', content)) for content in content_sections)
    
    print(f"\\n📊 内容统计:")
    print(f"  总字符数: {{total_chars:,}}")
    print(f"  总词数: {{total_words:,}}")
    print(f"  总句数: {{total_sentences:,}}")
    print(f"  平均每章节: {{total_chars//len(content_sections):,}} 字符")
    
    # 结构分析
    print(f"\\n🏗️ 结构分析:")
    for i, content in enumerate(content_sections, 1):
        paragraphs = len(content.split('\\n\\n'))
        sentences = len(re.findall(r'[.!?]+', content))
        print(f"  章节 {{i}}: {{paragraphs}} 段落, {{sentences}} 句子")
    
    # 关键词密度分析
    all_content = " ".join(content_sections).lower()
    topic_words = "{topic}".lower().split()
    
    print(f"\\n🎯 主题相关性:")
    for word in topic_words:
        count = all_content.count(word)
        density = (count / total_words) * 100 if total_words > 0 else 0
        print(f"  '{{word}}': {{count}} 次 ({{density:.2f}}%)")

print(f"\\n✅ 内容分析完成")
'''
    
    def _generate_trend_analysis_code(self, topic: str, context: Dict[str, Any]) -> str:
        """生成趋势分析代码。"""
        return f'''
# 趋势分析代码 - {topic}
import re
from collections import defaultdict, Counter
from datetime import datetime

print(f"=== 趋势分析: {topic} ===")

# 提取时间相关信息
search_results = []
context_data = {context}

for result in context_data.values():
    if result.get("task") == "search":
        search_results.extend(result.get("data", {{}}).get("results", []))

if search_results:
    print(f"🔍 分析 {{len(search_results)}} 个搜索结果")
    
    # 提取年份信息
    years = []
    for result in search_results:
        text = f"{{result.get('title', '')}} {{result.get('snippet', '')}}"
        year_matches = re.findall(r'\\b(20[0-2][0-9])\\b', text)
        years.extend(year_matches)
    
    if years:
        year_counts = Counter(years)
        print(f"\\n📅 时间分布:")
        for year in sorted(year_counts.keys()):
            count = year_counts[year]
            print(f"  {{year}}: {{count}} 次提及")
    
    # 分析发展阶段关键词
    development_keywords = [
        '发展', '进步', '创新', '突破', '改进', '升级', '演进',
        'development', 'progress', 'innovation', 'breakthrough', 'improvement'
    ]
    
    trend_mentions = defaultdict(int)
    for result in search_results:
        text = f"{{result.get('title', '')}} {{result.get('snippet', '')}}".lower()
        for keyword in development_keywords:
            if keyword in text:
                trend_mentions[keyword] += 1
    
    if trend_mentions:
        print(f"\\n📈 发展趋势关键词:")
        for keyword, count in sorted(trend_mentions.items(), key=lambda x: x[1], reverse=True):
            print(f"  {{keyword}}: {{count}} 次")

print(f"\\n✅ 趋势分析完成")
'''
    
    def _generate_sentiment_analysis_code(self, topic: str, context: Dict[str, Any]) -> str:
        """生成情感分析代码。"""
        return f'''
# 情感分析代码 - {topic}
import re
from collections import Counter

print(f"=== 情感分析: {topic} ===")

# 简单的情感词典
positive_words = [
    '好', '优秀', '成功', '有效', '重要', '创新', '先进', '突出', '显著',
    'good', 'excellent', 'successful', 'effective', 'important', 'innovative', 'advanced'
]

negative_words = [
    '差', '失败', '问题', '困难', '挑战', '限制', '缺点', '不足',
    'bad', 'failed', 'problem', 'difficult', 'challenge', 'limitation', 'disadvantage'
]

neutral_words = [
    '研究', '分析', '方法', '系统', '技术', '数据', '结果',
    'research', 'analysis', 'method', 'system', 'technology', 'data', 'result'
]

# 提取文本内容
all_text = ""
context_data = {context}

for result in context_data.values():
    if result.get("task") == "search":
        for search_result in result.get("data", {{}}).get("results", []):
            all_text += f" {{search_result.get('title', '')}} {{search_result.get('snippet', '')}}"
    elif result.get("task") == "content_generation":
        all_text += f" {{result.get('data', {{}}).get('content', '')}}"

if all_text:
    text_lower = all_text.lower()
    
    # 统计情感词
    positive_count = sum(text_lower.count(word) for word in positive_words)
    negative_count = sum(text_lower.count(word) for word in negative_words)
    neutral_count = sum(text_lower.count(word) for word in neutral_words)
    
    total_sentiment_words = positive_count + negative_count + neutral_count
    
    print(f"📊 情感分析结果:")
    if total_sentiment_words > 0:
        pos_pct = (positive_count / total_sentiment_words) * 100
        neg_pct = (negative_count / total_sentiment_words) * 100
        neu_pct = (neutral_count / total_sentiment_words) * 100
        
        print(f"  积极情感: {{positive_count}} ({{pos_pct:.1f}}%)")
        print(f"  消极情感: {{negative_count}} ({{neg_pct:.1f}}%)")
        print(f"  中性描述: {{neutral_count}} ({{neu_pct:.1f}}%)")
        
        # 情感倾向
        if positive_count > negative_count:
            sentiment = "积极"
        elif negative_count > positive_count:
            sentiment = "消极"
        else:
            sentiment = "中性"
        
        print(f"\\n🎭 总体情感倾向: {{sentiment}}")
    else:
        print("  未检测到明显的情感倾向")

print(f"\\n✅ 情感分析完成")
'''
    
    def _generate_basic_analysis_code(self, topic: str, analysis_type: str) -> str:
        """生成基础分析代码。"""
        return f'''
# 基础分析代码 - {topic}
from datetime import datetime

print(f"=== 基础分析: {topic} ===")
print(f"分析类型: {analysis_type}")
print(f"分析时间: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")

# 基础统计
print(f"\\n📋 分析概要:")
print(f"  主题: {topic}")
print(f"  类型: {analysis_type}")
print(f"  状态: 已完成")

print(f"\\n✅ 基础分析完成")
'''
    
    def _parse_search_output(self, search_output: str) -> List[Dict[str, str]]:
        """
        解析搜索工具输出为结构化格式。
        
        Args:
            search_output: 搜索工具的原始输出
        
        Returns:
            结构化的搜索结果列表
        """
        results = []
        
        if not search_output:
            return results
        
        try:
            # 尝试解析格式化的搜索结果
            # 格式: "1. Title\n   Snippet\n   URL: url"
            sections = search_output.split('\n\n')
            
            for section in sections:
                if not section.strip():
                    continue
                
                lines = section.strip().split('\n')
                if len(lines) >= 3:
                    # 提取标题（去掉序号）
                    title_line = lines[0].strip()
                    if '. ' in title_line:
                        title = title_line.split('. ', 1)[1]
                    else:
                        title = title_line
                    
                    # 提取描述
                    snippet = lines[1].strip()
                    
                    # 提取URL
                    url = ""
                    for line in lines[2:]:
                        if line.strip().startswith('URL:'):
                            url = line.strip().replace('URL:', '').strip()
                            break
                    
                    results.append({
                        "title": title,
                        "snippet": snippet,
                        "url": url,
                        "source": "search_tool"
                    })
        
        except Exception as e:
            self.log_warning(f"Failed to parse search output: {e}")
            # 回退：将整个输出作为单个结果
            if search_output.strip():
                results.append({
                    "title": "Search Results",
                    "snippet": search_output[:200] + "..." if len(search_output) > 200 else search_output,
                    "url": "",
                    "source": "search_tool"
                })
        
        return results
    
    async def _execute_parallel(self, plan: ExecutionPlan, results: Dict[str, Any], errors: List[str]):
        """并行执行计划。"""
        # 按依赖关系分组
        ready_steps = [step for step in plan.steps if not step.dependencies]
        pending_steps = [step for step in plan.steps if step.dependencies]
        
        while ready_steps or pending_steps:
            # 执行当前可执行的步骤
            if ready_steps:
                batch = ready_steps[:self.max_concurrent_tasks]
                ready_steps = ready_steps[self.max_concurrent_tasks:]
                
                # 使用异步执行器并行执行工具
                if self.async_executor and len(batch) > 1:
                    # 分离可并行和需要特殊处理的步骤
                    parallel_steps = []
                    special_steps = []
                    tools_and_inputs = []
                    
                    for step in batch:
                        tool, input_data = self._prepare_tool_execution(step, results)
                        if tool:
                            parallel_steps.append(step)
                            tools_and_inputs.append((tool, input_data))
                        else:
                            special_steps.append(step)
                    
                    # 并行执行可并行的步骤
                    parallel_tasks = []
                    if tools_and_inputs:
                        parallel_task = asyncio.create_task(
                            self.async_executor.execute_tools_parallel(
                                tools_and_inputs,
                                timeout=self.timeout_per_batch
                            )
                        )
                        parallel_tasks.append(parallel_task)
                    
                    # 同时执行需要特殊处理的步骤
                    special_tasks = []
                    for step in special_steps:
                        special_task = asyncio.create_task(self._execute_step(step, results))
                        special_tasks.append(special_task)
                    
                    # 等待所有任务完成
                    all_tasks = parallel_tasks + special_tasks
                    if all_tasks:
                        task_results = await asyncio.gather(*all_tasks, return_exceptions=True)
                        
                        # 处理并行工具执行结果
                        if parallel_tasks and not isinstance(task_results[0], Exception):
                            parallel_results = task_results[0]
                            for i, step in enumerate(parallel_steps):
                                task_id = f"parallel_{i}_{step.step_id}"
                                if task_id in parallel_results:
                                    async_result = parallel_results[task_id]
                                    if async_result.success:
                                        results[step.step_id] = {
                                            "success": True,
                                            "data": async_result.data,
                                            "execution_time": async_result.execution_time,
                                            "task": step.task_type.value
                                        }
                                    else:
                                        errors.append(f"Step {step.step_id}: {async_result.error}")
                                else:
                                    errors.append(f"Step {step.step_id}: No result from parallel execution")
                        elif parallel_tasks and isinstance(task_results[0], Exception):
                            errors.append(f"Parallel execution failed: {task_results[0]}")
                        
                        # 处理特殊步骤结果
                        special_result_start = len(parallel_tasks)
                        for i, step in enumerate(special_steps):
                            result_index = special_result_start + i
                            if result_index < len(task_results):
                                result = task_results[result_index]
                                if isinstance(result, Exception):
                                    errors.append(f"Step {step.step_id}: {str(result)}")
                                else:
                                    results[step.step_id] = result
                    else:
                        # 没有任务需要执行，回退到传统方式
                        tasks = [self._execute_step(step, results) for step in batch]
                        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        for step, result in zip(batch, batch_results):
                            if isinstance(result, Exception):
                                errors.append(f"Step {step.step_id}: {str(result)}")
                            else:
                                results[step.step_id] = result
                else:
                    # 传统并行执行
                    tasks = [self._execute_step(step, results) for step in batch]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 处理结果
                    for step, result in zip(batch, batch_results):
                        if isinstance(result, Exception):
                            errors.append(f"Step {step.step_id}: {str(result)}")
                        else:
                            results[step.step_id] = result
            
            # 检查是否有新的步骤可以执行
            new_ready = []
            remaining_pending = []
            
            for step in pending_steps:
                if self._check_dependencies(step, results):
                    new_ready.append(step)
                else:
                    remaining_pending.append(step)
            
            ready_steps.extend(new_ready)
            pending_steps = remaining_pending
            
            # 避免无限循环
            if not ready_steps and pending_steps:
                break
    
    async def _execute_adaptive(self, plan: ExecutionPlan, results: Dict[str, Any], errors: List[str]):
        """自适应执行计划。"""
        # 根据系统负载和步骤特性动态调整执行策略
        high_priority_steps = [s for s in plan.steps if s.priority <= 2]
        low_priority_steps = [s for s in plan.steps if s.priority > 2]
        
        # 优先执行高优先级步骤
        for step in high_priority_steps:
            if self._check_dependencies(step, results):
                result = await self._execute_step(step, results)
                results[step.step_id] = result
                if not result["success"]:
                    errors.append(f"High priority step {step.step_id} failed")
        
        # 并行执行低优先级步骤
        await self._execute_parallel(
            ExecutionPlan(
                plan_id=plan.plan_id + "_low_priority",
                topic=plan.topic,
                steps=low_priority_steps,
                strategy=ExecutionStrategy.PARALLEL,
                estimated_total_duration=0
            ),
            results,
            errors
        )
    
    def _prepare_tool_execution(self, step: ExecutionStep, context: Dict[str, Any]) -> tuple:
        """准备工具执行的工具和输入数据。"""
        try:
            if step.task_type == TaskType.SEARCH:
                tool = self.tool_registry.get_tool("web_search")
                query = step.parameters.get("query", "")
                
                # 处理依赖的查询构建
                if "section_index" in step.parameters:
                    section_index = step.parameters["section_index"]
                    for result in context.values():
                        if result.get("task") == "outline_generation":
                            outline_data = result.get("data", {})
                            if "sections" in outline_data:
                                sections = outline_data["sections"]
                                if section_index < len(sections):
                                    section = sections[section_index]
                                    query = f"{query} {section.get('title', '')} {' '.join(section.get('keywords', []))}"
                            break
                
                return tool, query
                
            elif step.task_type == TaskType.CODE_EXECUTION:
                tool = self.tool_registry.get_tool("python_executor")
                code = step.parameters.get("code", "")
                return tool, code
                
            elif step.task_type == TaskType.BROWSER_AUTOMATION:
                # 优先使用 browser_use 工具
                browser_use_tool = self.tool_registry.get_tool("browser_use")
                if browser_use_tool:
                    import json
                    action = step.parameters.get("action", "")
                    
                    # 根据动作类型构建 browser_use 输入
                    if action == "search":
                        input_data = json.dumps({
                            "action": "search_and_extract",
                            "parameters": {
                                "query": step.parameters.get("query", ""),
                                "search_engine": step.parameters.get("search_engine", "google")
                            }
                        })
                    elif action == "navigate":
                        input_data = json.dumps({
                            "action": "navigate_and_extract",
                            "parameters": {
                                "url": step.parameters.get("url", ""),
                                "extraction_task": step.parameters.get("extraction_task", "Extract all important information")
                            }
                        })
                    else:
                        # 通用自定义任务
                        input_data = json.dumps({
                            "action": "custom_task",
                            "parameters": {
                                "task_description": step.parameters.get("task_description", f"Execute browser action: {action}"),
                                "url": step.parameters.get("url", ""),
                                "max_steps": step.parameters.get("max_steps", 30)
                            }
                        })
                    
                    return browser_use_tool, input_data
                
                # 回退到传统 browser_automation
                tool = self.tool_registry.get_tool("browser_automation")
                import json
                action_data = {
                    "action": step.parameters.get("action", ""),
                    "url": step.parameters.get("url", "")
                }
                return tool, json.dumps(action_data)
                
            elif step.task_type == TaskType.BROWSER_USE:
                # 专门的 Browser-Use 任务
                tool = self.tool_registry.get_tool("browser_use")
                if not tool:
                    return None, None
                
                import json
                action = step.parameters.get("action", "custom_task")
                
                # 构建输入数据
                input_data = json.dumps({
                    "action": action,
                    "parameters": step.parameters.get("parameters", {})
                })
                
                return tool, input_data
                
            elif step.task_type == TaskType.FILE_OPERATION:
                tool = self.tool_registry.get_tool("file_reader")
                import json
                file_data = {
                    "path": step.parameters.get("path", ""),
                    "source": step.parameters.get("source", "local")
                }
                return tool, json.dumps(file_data)
            
            else:
                return None, None
                
        except Exception as e:
            self.log_error(f"Failed to prepare tool execution: {e}")
            return None, None
    
    def _check_dependencies(self, step: ExecutionStep, results: Dict[str, Any]) -> bool:
        """检查步骤依赖是否满足。"""
        for dep_id in step.dependencies:
            if dep_id not in results or not results[dep_id].get("success", False):
                return False
        return True
    
    def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """获取计划执行状态。"""
        if plan_id not in self.plans:
            return None
        
        plan = self.plans[plan_id]
        
        completed_steps = len([s for s in plan.steps if s.status == TaskStatus.COMPLETED])
        failed_steps = len([s for s in plan.steps if s.status == TaskStatus.FAILED])
        running_steps = len([s for s in plan.steps if s.status == TaskStatus.RUNNING])
        
        return {
            "plan_id": plan_id,
            "topic": plan.topic,
            "status": plan.status.value,
            "total_steps": len(plan.steps),
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "running_steps": running_steps,
            "progress": completed_steps / len(plan.steps) if plan.steps else 0
        }
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取执行历史。"""
        return [
            {
                "plan_id": result.plan_id,
                "success": result.success,
                "duration": result.total_duration,
                "completed_steps": result.completed_steps,
                "failed_steps": result.failed_steps,
                "error_count": len(result.errors)
            }
            for result in self.execution_history
        ] 