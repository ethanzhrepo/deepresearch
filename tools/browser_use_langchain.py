"""
LangChain 兼容的 Browser-Use 工具包装器

将 BrowserUseTool 包装为 LangChain BaseTool，以便集成到 MCP 工具链中。
"""

import json
import logging
from typing import Dict, Any, Optional
from langchain.tools import BaseTool
from pydantic import Field

from .browser_use_tool import BrowserUseTool, BROWSER_USE_AVAILABLE
from config import config

logger = logging.getLogger(__name__)

class BrowserUseLangChainTool(BaseTool):
    """LangChain 兼容的 Browser-Use 工具"""
    
    name: str = "browser_use"
    description: str = """AI-powered browser automation tool. Can perform intelligent web browsing, form filling, data extraction, and workflow automation.
    
    Input should be a JSON string with the following structure:
    {
        "action": "search_and_extract|navigate_and_extract|fill_form|monitor_changes|automate_workflow|custom_task",
        "parameters": {
            // Action-specific parameters
        }
    }
    
    Available actions:
    - search_and_extract: Search and extract information from search engines
    - navigate_and_extract: Navigate to URL and extract data
    - fill_form: Automatically fill and submit forms
    - monitor_changes: Monitor page changes over time
    - automate_workflow: Execute complex multi-step workflows
    - custom_task: Execute custom browser automation tasks
    """
    
    browser_tool: Optional[BrowserUseTool] = Field(default=None, exclude=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialize_browser_tool()
    
    def _initialize_browser_tool(self):
        """初始化 BrowserUseTool 实例"""
        if not BROWSER_USE_AVAILABLE:
            logger.warning("browser-use library not available, BrowserUseTool will be disabled")
            return
        
        try:
            # 从配置中获取 browser-use 工具配置
            tool_config = config.tools.browser_tool
            
            if not tool_config.enabled:
                logger.info("BrowserUseTool is disabled in configuration")
                return
            
            # 获取 browser-use 特定配置，如果存在的话
            # 注意：config.yml 中的 browser_use_tool 需要通过字典方式访问
            browser_use_config = None
            try:
                # 尝试通过 config.tools.__dict__ 访问 browser_use_tool
                tools_dict = config.tools.__dict__
                browser_use_config = tools_dict.get('browser_use_tool', None)
            except:
                browser_use_config = None
            
            # 构建完整的配置字典，优先使用 DeepSeek
            browser_config = {
                'enabled': tool_config.enabled,
                'llm_provider': 'deepseek',  # 默认使用 DeepSeek
                'llm_model': 'deepseek-chat',  # 使用 deepseek-chat 模型
                'browser': {
                    'headless': True,
                    'timeout': 300,
                    'max_steps': 50
                },
                'output_dir': 'browser_outputs'
            }
            
            # 如果有 browser_use_tool 配置，使用它覆盖默认配置
            if browser_use_config:
                if hasattr(browser_use_config, 'llm_provider'):
                    browser_config['llm_provider'] = browser_use_config.llm_provider
                if hasattr(browser_use_config, 'llm_model'):
                    browser_config['llm_model'] = browser_use_config.llm_model
                if hasattr(browser_use_config, 'output_dir'):
                    browser_config['output_dir'] = browser_use_config.output_dir
                if hasattr(browser_use_config, 'browser'):
                    browser_attr = browser_use_config.browser
                    if hasattr(browser_attr, 'headless'):
                        browser_config['browser']['headless'] = browser_attr.headless
                    if hasattr(browser_attr, 'timeout'):
                        browser_config['browser']['timeout'] = browser_attr.timeout
                    if hasattr(browser_attr, 'max_steps'):
                        browser_config['browser']['max_steps'] = browser_attr.max_steps
            
            logger.info(f"Browser-Use configuration: {browser_config}")
            
            # 创建 BrowserUseTool 实例
            self.browser_tool = BrowserUseTool(browser_config)
            logger.info(f"BrowserUseTool initialized successfully with {browser_config['llm_provider']} LLM")
            
        except Exception as e:
            logger.error(f"Failed to initialize BrowserUseTool: {e}")
            logger.debug("BrowserUseTool error details:", exc_info=True)
            self.browser_tool = None
    
    def _run(self, input_json: str) -> str:
        """执行 browser-use 工具"""
        if not self.browser_tool:
            return json.dumps({
                "success": False,
                "error": "BrowserUseTool not available. Please check installation and configuration.",
                "suggestion": "Run 'pip install browser-use playwright' and configure API keys"
            })
        
        try:
            # 解析输入 JSON
            input_data = json.loads(input_json)
            action = input_data.get("action", "")
            parameters = input_data.get("parameters", {})
            
            if not action:
                return json.dumps({
                    "success": False,
                    "error": "Missing 'action' parameter",
                    "available_actions": [
                        "search_and_extract",
                        "navigate_and_extract", 
                        "fill_form",
                        "monitor_changes",
                        "automate_workflow",
                        "custom_task"
                    ]
                })
            
            # 执行相应的动作
            result = self.browser_tool.execute(action=action, **parameters)
            
            # 返回 JSON 格式的结果
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except json.JSONDecodeError as e:
            return json.dumps({
                "success": False,
                "error": f"Invalid JSON input: {str(e)}",
                "example": {
                    "action": "search_and_extract",
                    "parameters": {
                        "query": "AI research trends",
                        "search_engine": "google"
                    }
                }
            })
        
        except Exception as e:
            logger.error(f"BrowserUseTool execution failed: {e}", exc_info=True)
            return json.dumps({
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            })
    
    async def _arun(self, input_json: str) -> str:
        """异步执行 browser-use 工具"""
        # 对于 browser-use，我们使用同步包装器
        # 因为 BrowserUseTool.execute() 内部已经处理了异步操作
        return self._run(input_json)
    
    def is_available(self) -> bool:
        """检查工具是否可用"""
        return self.browser_tool is not None
    
    def get_tool_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        return {
            "name": self.name,
            "description": self.description,
            "available": self.is_available(),
            "browser_use_available": BROWSER_USE_AVAILABLE,
            "config_enabled": config.tools.browser_tool.enabled
        }

# 创建工具实例的工厂函数
def create_browser_use_tool() -> BrowserUseLangChainTool:
    """创建 BrowserUseLangChainTool 实例"""
    return BrowserUseLangChainTool()

# 用于测试的示例用法
def example_usage():
    """示例用法"""
    tool = create_browser_use_tool()
    
    # 示例 1: 搜索和提取
    search_input = json.dumps({
        "action": "search_and_extract",
        "parameters": {
            "query": "人工智能最新发展趋势",
            "search_engine": "google"
        }
    })
    
    print("搜索示例:")
    print(tool._run(search_input))
    
    # 示例 2: 导航和提取
    navigate_input = json.dumps({
        "action": "navigate_and_extract",
        "parameters": {
            "url": "https://github.com/browser-use/browser-use",
            "extraction_task": "提取项目描述、星标数和最新版本信息"
        }
    })
    
    print("\n导航示例:")
    print(tool._run(navigate_input))

if __name__ == "__main__":
    example_usage() 