"""
Async tool execution framework for DeepResearch.
Provides better integration with async workflows and LangGraph.
"""

import asyncio
import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, Callable, Awaitable
from langchain.tools import BaseTool
from pydantic import BaseModel

from utils.logger import LoggerMixin


class AsyncToolResult(BaseModel):
    """Result from async tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class AsyncBaseTool(BaseTool, LoggerMixin, ABC):
    """Base class for async-first tools."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @abstractmethod
    async def _arun(self, *args, **kwargs) -> str:
        """Async implementation of the tool."""
        pass
    
    def _run(self, *args, **kwargs) -> str:
        """Simplified and reliable sync wrapper for async implementation."""
        try:
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # If there's a running loop, use thread pool to avoid blocking
                return self._run_in_thread_pool(*args, **kwargs)
            except RuntimeError:
                # No running loop, we can create one safely
                return asyncio.run(self._arun(*args, **kwargs))
                
        except Exception as e:
            self.log_error(f"Tool execution failed: {e}")
            return f"Tool execution error: {str(e)}"
    
    def _run_in_thread_pool(self, *args, **kwargs) -> str:
        """Fallback: run async method in thread pool."""
        import concurrent.futures
        
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self._arun(*args, **kwargs))
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_in_thread)
            return future.result(timeout=300)  # 5 minutes timeout


class AsyncToolExecutor(LoggerMixin):
    """Executor for managing async tool execution."""
    
    def __init__(self):
        """Initialize async tool executor."""
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, AsyncToolResult] = {}
    
    async def execute_tool(
        self,
        tool: Union[AsyncBaseTool, BaseTool],
        input_data: Any,
        task_id: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> AsyncToolResult:
        """
        Execute a tool asynchronously.
        
        Args:
            tool: Tool to execute
            input_data: Input data for the tool
            task_id: Optional task identifier
            timeout: Execution timeout
        
        Returns:
            AsyncToolResult with execution details
        """
        import time
        import uuid
        
        task_id = task_id or str(uuid.uuid4())
        start_time = time.time()
        
        try:
            self.log_debug(f"Executing tool {tool.name} (task: {task_id})")
            
            # Execute the tool
            if isinstance(tool, AsyncBaseTool):
                # Native async tool
                if timeout:
                    result = await asyncio.wait_for(
                        tool._arun(input_data),
                        timeout=timeout
                    )
                else:
                    result = await tool._arun(input_data)
            else:
                # Legacy sync tool - run in executor
                loop = asyncio.get_running_loop()
                if timeout:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, tool._run, input_data),
                        timeout=timeout
                    )
                else:
                    result = await loop.run_in_executor(None, tool._run, input_data)
            
            execution_time = time.time() - start_time
            
            tool_result = AsyncToolResult(
                success=True,
                data=result,
                execution_time=execution_time,
                metadata={"task_id": task_id, "tool_name": tool.name}
            )
            
            self.task_results[task_id] = tool_result
            self.log_debug(f"Tool {tool.name} completed in {execution_time:.2f}s")
            
            return tool_result
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"Tool execution timeout after {timeout}s"
            
            tool_result = AsyncToolResult(
                success=False,
                data=None,
                error=error_msg,
                execution_time=execution_time,
                metadata={"task_id": task_id, "tool_name": tool.name}
            )
            
            self.task_results[task_id] = tool_result
            self.log_error(f"Tool {tool.name} timed out after {timeout}s")
            
            return tool_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            tool_result = AsyncToolResult(
                success=False,
                data=None,
                error=error_msg,
                execution_time=execution_time,
                metadata={"task_id": task_id, "tool_name": tool.name}
            )
            
            self.task_results[task_id] = tool_result
            self.log_error(f"Tool {tool.name} failed: {error_msg}")
            
            return tool_result
        finally:
            # Clean up running task reference
            self.running_tasks.pop(task_id, None)
    
    async def execute_tools_parallel(
        self,
        tools_and_inputs: list,
        timeout: Optional[float] = None
    ) -> Dict[str, AsyncToolResult]:
        """
        Execute multiple tools in parallel.
        
        Args:
            tools_and_inputs: List of (tool, input_data) tuples
            timeout: Overall timeout for all tools
        
        Returns:
            Dictionary mapping task IDs to results
        """
        tasks = []
        task_ids = []
        
        for i, (tool, input_data) in enumerate(tools_and_inputs):
            task_id = f"parallel_{i}_{tool.name}"
            task_ids.append(task_id)
            
            task = asyncio.create_task(
                self.execute_tool(tool, input_data, task_id, timeout)
            )
            tasks.append(task)
            self.running_tasks[task_id] = task
        
        try:
            if timeout:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout
                )
            else:
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            result_dict = {}
            for task_id, result in zip(task_ids, results):
                if isinstance(result, Exception):
                    result_dict[task_id] = AsyncToolResult(
                        success=False,
                        data=None,
                        error=str(result),
                        metadata={"task_id": task_id}
                    )
                else:
                    result_dict[task_id] = result
            
            return result_dict
            
        except asyncio.TimeoutError:
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for cancellation
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Return partial results
            return {task_id: self.task_results.get(task_id, AsyncToolResult(
                success=False,
                error="Parallel execution timeout",
                metadata={"task_id": task_id}
            )) for task_id in task_ids}
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: Task identifier
        
        Returns:
            True if task was cancelled, False if not found
        """
        task = self.running_tasks.get(task_id)
        if task and not task.done():
            task.cancel()
            self.log_info(f"Cancelled task {task_id}")
            return True
        return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a task.
        
        Args:
            task_id: Task identifier
        
        Returns:
            Task status information or None if not found
        """
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            return {
                "task_id": task_id,
                "status": "running" if not task.done() else "completed",
                "cancelled": task.cancelled() if task.done() else False
            }
        elif task_id in self.task_results:
            result = self.task_results[task_id]
            return {
                "task_id": task_id,
                "status": "completed",
                "success": result.success,
                "execution_time": result.execution_time
            }
        return None
    
    def cleanup_completed_tasks(self):
        """Clean up completed task results."""
        completed_tasks = [
            task_id for task_id, task in self.running_tasks.items()
            if task.done()
        ]
        
        for task_id in completed_tasks:
            self.running_tasks.pop(task_id, None)
        
        self.log_debug(f"Cleaned up {len(completed_tasks)} completed tasks")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        return {
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.task_results),
            "total_tasks": len(self.running_tasks) + len(self.task_results)
        }


# Global async tool executor (deprecated - use ToolRegistry.get_async_executor() instead)
# This is kept for backward compatibility
async_tool_executor = None

def get_global_async_executor() -> AsyncToolExecutor:
    """
    Get global async executor instance (lazy initialization).
    
    DEPRECATED: Use ToolRegistry.get_async_executor() instead.
    This function is kept for backward compatibility only.
    """
    import warnings
    warnings.warn(
        "get_global_async_executor() is deprecated. "
        "Use ToolRegistry.get_async_executor() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    global async_tool_executor
    if async_tool_executor is None:
        # Use ToolRegistry instead of creating a standalone instance
        try:
            from tools.tool_registry import tool_registry
            return tool_registry.get_async_executor()
        except ImportError:
            # Fallback for edge cases
            async_tool_executor = AsyncToolExecutor()
    return async_tool_executor


# DEPRECATED: Direct access to global instance
# Use ToolRegistry.get_async_executor() instead
def _get_deprecated_global_executor():
    """Internal function for backward compatibility."""
    return get_global_async_executor()


class AsyncSearchTool(AsyncBaseTool):
    """Async version of search tool."""
    
    name: str = "async_web_search"
    description: str = "Asynchronously search the web for information. Input should be a search query string."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._search_manager = None
    
    @property
    def search_manager(self):
        """Get search manager instance."""
        if self._search_manager is None:
            from tools.search_engines import SearchEngineManager
            self._search_manager = SearchEngineManager()
        return self._search_manager
    
    async def _arun(self, query: str) -> str:
        """Execute web search asynchronously."""
        try:
            # Run search in executor to avoid blocking
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(
                None,
                self.search_manager.search,
                query,
                None,  # engine
                5      # max_results
            )
            
            if not results:
                return "No search results found."
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(
                    f"{i}. {result.title}\n   {result.snippet}\n   URL: {result.url}"
                )
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            self.log_error(f"Async search failed: {e}")
            return f"Search failed: {str(e)}"


class AsyncBrowserTool(AsyncBaseTool):
    """Async version of browser tool."""
    
    name: str = "async_browser_automation"
    description: str = "Asynchronously automate browser actions. Input should be a JSON string with action details."
    
    async def _arun(self, action_json: str) -> str:
        """Execute browser automation asynchronously."""
        try:
            import json
            
            action = json.loads(action_json)
            
            # Use resource manager for browser instances
            from utils.resource_manager import get_browser_resource
            async with get_browser_resource() as browser:
                result = await browser.execute_action(action)
                
                if result.success:
                    if result.data:
                        return f"Browser action successful:\n{json.dumps(result.data, indent=2)}"
                    else:
                        return "Browser action completed successfully"
                else:
                    return f"Browser action failed: {result.error}"
                    
        except json.JSONDecodeError:
            return "Invalid JSON input. Please provide action details in JSON format."
        except Exception as e:
            self.log_error(f"Async browser automation failed: {e}")
            return f"Browser automation error: {str(e)}" 