"""
Tool modules for DeepResearch system.
Provides various tools for research automation.
"""

from .code_runner import CodeRunner
from .search_engines import SearchEngineManager
from .tool_registry import ToolRegistry
from .browser_agent import BrowserAgent
from .drive_connector import GoogleDriveConnector
from .dropbox_connector import DropboxConnector

# Browser-Use integration
try:
    from .browser_use_tool import BrowserUseTool
    from .browser_use_langchain import BrowserUseLangChainTool, create_browser_use_tool
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False

__all__ = [
    "CodeRunner",
    "SearchEngineManager",
    "ToolRegistry",
    "BrowserAgent",
    "GoogleDriveConnector",
    "DropboxConnector"
]

# Add browser-use tools if available
if BROWSER_USE_AVAILABLE:
    __all__.extend([
        "BrowserUseTool",
        "BrowserUseLangChainTool",
        "create_browser_use_tool"
    ]) 