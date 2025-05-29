"""
Tool registry for DeepResearch system.
Registers and manages all available tools for LangChain integration.
"""

from typing import Dict, List, Any, Optional, Type
from langchain.tools import BaseTool
from langchain.schema import BaseMessage
from pydantic import BaseModel, Field, PrivateAttr
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from utils.logger import LoggerMixin
from .search_engines import SearchEngineManager, SearchResult
from .code_runner import CodeRunner
from .browser_agent import BrowserAgent
from .drive_connector import GoogleDriveConnector
from .dropbox_connector import DropboxConnector
from config import config


class ToolType(Enum):
    """Types of available tools."""
    SEARCH = "search"
    CODE = "code"
    BROWSER = "browser"
    FILE = "file"
    LLM = "llm"


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchTool(BaseTool):
    """Tool for web search operations."""
    
    name: str = "web_search"
    description: str = "Search the web for information. Input should be a search query string."
    
    _search_manager: Any = PrivateAttr(default=None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._search_manager = None
    
    @property
    def search_manager(self):
        """获取搜索管理器实例。"""
        if self._search_manager is None:
            try:
                from search.search_engine import SearchEngineManager
                self._search_manager = SearchEngineManager()
            except Exception as e:
                self.log_error(f"Failed to initialize SearchEngineManager: {e}")
                # 创建一个简单的回退实现
                self._search_manager = self._create_fallback_search_manager()
        return self._search_manager
    
    def _create_fallback_search_manager(self):
        """创建回退搜索管理器。"""
        class FallbackSearchManager:
            def search(self, query: str, max_results: int = 5):
                return [{"title": "Search unavailable", "snippet": "Search service is currently unavailable", "url": ""}]
        
        return FallbackSearchManager()
    
    def _run(self, query: str) -> str:
        """Execute web search."""
        try:
            results = self.search_manager.search(query, max_results=5)
            
            if not results:
                return "No search results found."
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                if isinstance(result, SearchResult):
                    formatted_results.append(
                        f"{i}. {result.title}\n   {result.snippet}\n   URL: {result.url}"
                    )
                elif isinstance(result, dict):
                    title = result.get('title', 'No title')
                    snippet = result.get('snippet', 'No description')
                    url = result.get('url', 'No URL')
                    formatted_results.append(
                        f"{i}. {title}\n   {snippet}\n   URL: {url}"
                    )
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            self.log_error(f"Search execution failed: {e}")
            return f"Search failed: {str(e)}"


class CodeExecutionTool(BaseTool):
    """Tool for Python code execution."""
    
    name: str = "python_executor"
    description: str = "Execute Python code and return results. Input should be Python code as a string."
    
    _code_runner: Any = PrivateAttr(default=None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._code_runner = None
    
    @property
    def code_runner(self):
        """获取代码执行器实例。"""
        if self._code_runner is None:
            try:
                from tools.code_executor import CodeRunner
                self._code_runner = CodeRunner()
            except Exception as e:
                self.log_error(f"Failed to initialize CodeRunner: {e}")
                # 创建一个简单的回退实现
                self._code_runner = self._create_fallback_code_runner()
        return self._code_runner
    
    def _create_fallback_code_runner(self):
        """创建回退代码执行器。"""
        class FallbackCodeRunner:
            def execute_code(self, code: str):
                from dataclasses import dataclass
                
                @dataclass
                class ExecutionResult:
                    success: bool
                    stdout: str = ""
                    stderr: str = ""
                    return_value: Any = None
                
                return ExecutionResult(
                    success=False,
                    stderr="Code execution service is currently unavailable"
                )
        
        return FallbackCodeRunner()
    
    def _run(self, code: str) -> str:
        """Execute Python code."""
        try:
            result = self.code_runner.execute_code(code)
            
            if result.success:
                output = []
                if result.stdout:
                    output.append(f"Output:\n{result.stdout}")
                if result.return_value is not None:
                    output.append(f"Return value: {result.return_value}")
                
                return "\n\n".join(output) if output else "Code executed successfully (no output)"
            else:
                return f"Execution failed:\n{result.stderr}"
                
        except Exception as e:
            self.log_error(f"Code execution failed: {e}")
            return f"Code execution error: {str(e)}"


class BrowserTool(BaseTool):
    """Tool for browser automation with improved resource management."""
    
    name: str = "browser_automation"
    description: str = "Automate browser actions like visiting URLs, clicking elements, or extracting content. Input should be a JSON string with action details."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    async def _run_async(self, action_json: str) -> str:
        """异步执行浏览器自动化。"""
        try:
            import json
            
            action = json.loads(action_json)
            
            # 使用资源管理器获取浏览器实例
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
            return f"Browser automation error: {str(e)}"
    
    def _run(self, action_json: str) -> str:
        """Execute browser automation (sync wrapper)."""
        try:
            import asyncio
            
            # 检查是否已有运行的事件循环
            try:
                loop = asyncio.get_running_loop()
                # 如果有运行的循环，使用 run_in_executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_sync_in_thread, action_json)
                    return future.result()
            except RuntimeError:
                # 没有运行的循环，创建新的
                return asyncio.run(self._run_async(action_json))
                
        except Exception as e:
            return f"Browser automation error: {str(e)}"
    
    def _run_sync_in_thread(self, action_json: str) -> str:
        """在新线程中同步运行异步代码。"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._run_async(action_json))
        finally:
            loop.close()


class FileReaderTool(BaseTool):
    """Tool for reading files from various sources."""
    
    name: str = "file_reader"
    description: str = "Read files from local filesystem, Google Drive, or Dropbox. Input should be a JSON string with file details."
    
    _drive_connector: Any = PrivateAttr(default=None)
    _dropbox_connector: Any = PrivateAttr(default=None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._drive_connector = None
        self._dropbox_connector = None
    
    @property
    def drive_connector(self):
        """获取 Google Drive 连接器实例。"""
        if self._drive_connector is None:
            from .drive_connector import GoogleDriveConnector
            self._drive_connector = GoogleDriveConnector()
        return self._drive_connector
    
    @property
    def dropbox_connector(self):
        """获取 Dropbox 连接器实例。"""
        if self._dropbox_connector is None:
            from .dropbox_connector import DropboxConnector
            self._dropbox_connector = DropboxConnector()
        return self._dropbox_connector
    
    def _run(self, file_info_json: str) -> str:
        """Read file content."""
        try:
            import json
            
            file_info = json.loads(file_info_json)
            source = file_info.get("source", "local")  # local, drive, dropbox
            path = file_info.get("path", "")
            
            if source == "local":
                return self._read_local_file(path)
            elif source == "drive":
                return self._read_drive_file(file_info)
            elif source == "dropbox":
                return self._read_dropbox_file(file_info)
            else:
                return f"Unsupported file source: {source}"
                
        except json.JSONDecodeError:
            return "Invalid JSON input. Please provide file details in JSON format."
        except Exception as e:
            return f"File reading error: {str(e)}"
    
    def _read_local_file(self, path: str) -> str:
        """Read local file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"File content ({len(content)} characters):\n{content}"
        except Exception as e:
            return f"Failed to read local file: {str(e)}"
    
    def _read_drive_file(self, file_info: Dict[str, Any]) -> str:
        """Read Google Drive file."""
        try:
            file_id = file_info.get("file_id", "")
            if not file_id:
                return "Google Drive file ID required"
            
            result = self.drive_connector.read_text_file(file_id)
            
            if result.success:
                content = result.data.get("text_content", "")
                return f"Drive file content ({len(content)} characters):\n{content}"
            else:
                return f"Failed to read Drive file: {result.error}"
                
        except Exception as e:
            return f"Drive file reading error: {str(e)}"
    
    def _read_dropbox_file(self, file_info: Dict[str, Any]) -> str:
        """Read Dropbox file."""
        try:
            path = file_info.get("path", "")
            if not path:
                return "Dropbox file path required"
            
            result = self.dropbox_connector.read_text_file(path)
            
            if result.success:
                content = result.data.get("text_content", "")
                return f"Dropbox file content ({len(content)} characters):\n{content}"
            else:
                return f"Failed to read Dropbox file: {result.error}"
                
        except Exception as e:
            return f"Dropbox file reading error: {str(e)}"


class ToolRegistry(LoggerMixin):
    """
    Registry for all available tools in the DeepResearch system.
    Manages tool registration and provides unified access.
    """
    
    def __init__(self, async_executor=None):
        """Initialize tool registry."""
        self.tools = {}
        self.tool_types = {}
        self._async_executor = async_executor
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools."""
        try:
            # Core tools
            self.register_tool(SearchTool(), ToolType.SEARCH)
            self.register_tool(CodeExecutionTool(), ToolType.CODE)
            self.register_tool(BrowserTool(), ToolType.BROWSER)
            self.register_tool(FileReaderTool(), ToolType.FILE)
            
            # Browser-Use tool (AI-powered browser automation)
            try:
                from .browser_use_langchain import BrowserUseLangChainTool
                browser_use_tool = BrowserUseLangChainTool()
                if browser_use_tool.is_available():
                    self.register_tool(browser_use_tool, ToolType.BROWSER)
                    self.log_info("BrowserUseTool registered successfully")
                else:
                    self.log_warning("BrowserUseTool not available, skipping registration")
            except ImportError as e:
                self.log_warning(f"Failed to import BrowserUseTool: {e}")
            except Exception as e:
                self.log_error(f"Failed to register BrowserUseTool: {e}")
            
            self.log_info(f"Registered {len(self.tools)} default tools")
            
        except Exception as e:
            self.log_error(f"Failed to register default tools: {e}")
    
    def register_tool(self, tool: BaseTool, tool_type: ToolType):
        """
        Register a tool.
        
        Args:
            tool: Tool to register
            tool_type: Type of the tool
        """
        self.tools[tool.name] = tool
        self.tool_types[tool.name] = tool_type
        self.log_debug(f"Registered tool: {tool.name} ({tool_type.value})")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
        
        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all registered tools.
        
        Returns:
            List of all tools
        """
        return list(self.tools.values())
    
    def get_tool_names(self) -> List[str]:
        """
        Get names of all registered tools.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """
        Get tools by category.
        
        Args:
            category: Tool category
        
        Returns:
            List of tools in the category
        """
        category_mapping = {
            "search": ["web_search"],
            "code": ["python_executor"],
            "browser": ["browser_automation", "browser_use"],
            "file": ["file_reader"],
            "analysis": ["python_executor"]
        }
        
        tool_names = category_mapping.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    def execute_tool(self, tool_name: str, input_data: str) -> str:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of tool to execute
            input_data: Input data for the tool
        
        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return f"Tool '{tool_name}' not found"
        
        try:
            result = tool._run(input_data)
            self.log_debug(f"Executed tool {tool_name} successfully")
            return result
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self.log_error(error_msg)
            return error_msg
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered tools with their information.
        
        Returns:
            Dictionary mapping tool names to tool information
        """
        return {
            name: {
                "description": tool.description,
                "type": self.tool_types.get(name, ToolType.LLM).value,
                "available": True
            }
            for name, tool in self.tools.items()
        }
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all tools.
        
        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {name: tool.description for name, tool in self.tools.items()}
    
    def validate_tools(self) -> Dict[str, bool]:
        """
        Validate all registered tools.
        
        Returns:
            Dictionary mapping tool names to validation status
        """
        validation_results = {}
        
        for name, tool in self.tools.items():
            try:
                # Basic validation - check if tool has required attributes
                has_name = hasattr(tool, 'name') and tool.name
                has_description = hasattr(tool, 'description') and tool.description
                has_run_method = hasattr(tool, '_run') and callable(tool._run)
                
                validation_results[name] = has_name and has_description and has_run_method
                
            except Exception as e:
                self.log_error(f"Tool validation failed for {name}: {e}")
                validation_results[name] = False
        
        return validation_results
    
    def get_async_executor(self):
        """
        Get the async tool executor instance.
        
        Returns:
            AsyncToolExecutor instance
        """
        if self._async_executor is None:
            from tools.async_tools import AsyncToolExecutor
            self._async_executor = AsyncToolExecutor()
            self.log_debug("Created new AsyncToolExecutor instance")
        return self._async_executor
    
    def set_async_executor(self, executor):
        """
        Set a custom async tool executor.
        
        Args:
            executor: AsyncToolExecutor instance
        """
        self._async_executor = executor
        self.log_debug("Set custom AsyncToolExecutor instance")
    
    async def execute_tool_async(self, tool_name: str, input_data: str, timeout: Optional[float] = None) -> Any:
        """
        Execute a tool asynchronously.
        
        Args:
            tool_name: Name of tool to execute
            input_data: Input data for the tool
            timeout: Execution timeout
        
        Returns:
            AsyncToolResult with execution details
        """
        tool = self.get_tool(tool_name)
        if not tool:
            from tools.async_tools import AsyncToolResult
            return AsyncToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found"
            )
        
        executor = self.get_async_executor()
        return await executor.execute_tool(tool, input_data, timeout=timeout)
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about registered tools.
        
        Returns:
            Tool statistics
        """
        validation_results = self.validate_tools()
        
        executor_stats = {}
        if self._async_executor:
            executor_stats = self._async_executor.get_stats()
        
        return {
            "total_tools": len(self.tools),
            "valid_tools": sum(validation_results.values()),
            "invalid_tools": len(validation_results) - sum(validation_results.values()),
            "tool_names": list(self.tools.keys()),
            "validation_results": validation_results,
            "async_executor_stats": executor_stats
        }


# Global tool registry instance
# DEPRECATED: Use get_tool_registry() from utils.service_container instead
import warnings

def _get_deprecated_tool_registry():
    """Internal function to handle deprecated global access."""
    warnings.warn(
        "Direct import of tool_registry is deprecated. "
        "Use get_tool_registry() from utils.service_container instead.",
        DeprecationWarning,
        stacklevel=3
    )
    from utils.service_container import get_tool_registry
    return get_tool_registry()

# 保持向后兼容性的全局实例
tool_registry = _get_deprecated_tool_registry() 