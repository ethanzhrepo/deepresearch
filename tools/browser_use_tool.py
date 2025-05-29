"""
Browser Use Tool - 基于 browser-use 的智能浏览器自动化工具

集成 https://github.com/browser-use/browser-use 库，提供 AI 驱动的浏览器自动化功能。
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
import os

try:
    from browser_use import Agent
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain_google_genai import ChatGoogleGenerativeAI
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False

# 使用 LangChain 的 BaseTool
from langchain.tools import BaseTool
from pydantic import Field

logger = logging.getLogger(__name__)

@dataclass
class BrowserTask:
    """浏览器任务配置"""
    task_description: str
    url: Optional[str] = None
    max_steps: int = 50
    headless: bool = True
    timeout: int = 300
    save_screenshots: bool = True
    extract_data: bool = True

class BrowserUseTool(BaseTool):
    """基于 browser-use 的智能浏览器自动化工具"""
    
    name: str = "browser_use_tool"
    description: str = "AI-powered browser automation using browser-use library"
    
    # 使用 Pydantic v2 兼容的字段定义
    config: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    llm_provider: str = Field(default="openai", exclude=True)
    llm_model: str = Field(default="gpt-4o", exclude=True)
    llm: Any = Field(default=None, exclude=True)
    browser_config: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    default_headless: bool = Field(default=True, exclude=True)
    default_timeout: int = Field(default=300, exclude=True)
    output_dir: str = Field(default="browser_outputs", exclude=True)
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        
        if not BROWSER_USE_AVAILABLE:
            raise ImportError(
                "browser-use library not available. Install with: "
                "pip install browser-use"
            )
        
        # 配置 LLM
        self.llm_provider = config.get('llm_provider', 'openai')
        self.llm_model = config.get('llm_model', 'gpt-4o')
        self.llm = self._setup_llm()
        
        # 浏览器配置
        self.browser_config = config.get('browser', {})
        self.default_headless = self.browser_config.get('headless', True)
        self.default_timeout = self.browser_config.get('timeout', 300)
        
        # 输出配置
        self.output_dir = config.get('output_dir', 'browser_outputs')
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"BrowserUseTool initialized with {self.llm_provider} LLM")
    
    def _setup_llm(self):
        """设置 LLM 模型，支持 DeepSeek"""
        if self.llm_provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable required")
            return ChatOpenAI(model=self.llm_model, api_key=api_key)
        
        elif self.llm_provider == 'deepseek':
            # DeepSeek 使用 OpenAI 兼容的接口
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY environment variable required")
            return ChatOpenAI(
                model=self.llm_model,
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
        
        elif self.llm_provider == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable required")
            return ChatAnthropic(model=self.llm_model, api_key=api_key)
        
        elif self.llm_provider == 'google':
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable required")
            return ChatGoogleGenerativeAI(model=self.llm_model, google_api_key=api_key)
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}. Supported: openai, deepseek, anthropic, google")
    
    async def execute_task(self, task: BrowserTask) -> Dict[str, Any]:
        """执行浏览器自动化任务"""
        try:
            logger.info(f"Starting browser task: {task.task_description}")
            
            # 创建 browser-use Agent
            agent = Agent(
                task=task.task_description,
                llm=self.llm,
                max_steps=task.max_steps,
                headless=task.headless,
                save_conversation_path=f"{self.output_dir}/conversation_{asyncio.current_task().get_name()}.json"
            )
            
            # 如果指定了 URL，添加到任务描述中
            if task.url:
                agent.task = f"Go to {task.url} and {task.task_description}"
            
            # 执行任务
            result = await asyncio.wait_for(
                agent.run(),
                timeout=task.timeout
            )
            
            # 处理结果
            output = {
                'success': True,
                'task': task.task_description,
                'url': task.url,
                'result': str(result) if result else "Task completed successfully",
                'steps_taken': agent.history if hasattr(agent, 'history') else [],
                'screenshots': [],
                'extracted_data': {}
            }
            
            # 保存截图（如果启用）
            if task.save_screenshots and hasattr(agent, 'browser'):
                screenshot_path = f"{self.output_dir}/screenshot_{asyncio.current_task().get_name()}.png"
                try:
                    await agent.browser.screenshot(path=screenshot_path)
                    output['screenshots'].append(screenshot_path)
                except Exception as e:
                    logger.warning(f"Failed to save screenshot: {e}")
            
            # 提取数据（如果启用）
            if task.extract_data and hasattr(agent, 'browser'):
                try:
                    page_content = await agent.browser.content()
                    output['extracted_data'] = {
                        'title': await agent.browser.title(),
                        'url': agent.browser.url,
                        'content_length': len(page_content),
                        'content_preview': page_content[:1000] if page_content else ""
                    }
                except Exception as e:
                    logger.warning(f"Failed to extract data: {e}")
            
            logger.info(f"Browser task completed successfully")
            return output
            
        except asyncio.TimeoutError:
            error_msg = f"Browser task timed out after {task.timeout} seconds"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'task': task.task_description
            }
        
        except Exception as e:
            error_msg = f"Browser task failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'task': task.task_description
            }
    
    async def search_and_extract(self, query: str, search_engine: str = "google") -> Dict[str, Any]:
        """搜索并提取信息"""
        task = BrowserTask(
            task_description=f"Search for '{query}' on {search_engine} and extract the top 5 search results with titles, URLs, and snippets",
            max_steps=20,
            extract_data=True
        )
        
        return await self.execute_task(task)
    
    async def navigate_and_extract(self, url: str, extraction_task: str) -> Dict[str, Any]:
        """导航到指定 URL 并提取信息"""
        task = BrowserTask(
            task_description=extraction_task,
            url=url,
            max_steps=30,
            extract_data=True
        )
        
        return await self.execute_task(task)
    
    async def fill_form(self, url: str, form_data: Dict[str, str], submit: bool = False) -> Dict[str, Any]:
        """填写表单"""
        form_instructions = []
        for field, value in form_data.items():
            form_instructions.append(f"Fill the '{field}' field with '{value}'")
        
        if submit:
            form_instructions.append("Submit the form")
        
        task_description = f"Go to the form and {', then '.join(form_instructions)}"
        
        task = BrowserTask(
            task_description=task_description,
            url=url,
            max_steps=25
        )
        
        return await self.execute_task(task)
    
    async def monitor_changes(self, url: str, element_selector: str, check_interval: int = 60, max_checks: int = 10) -> Dict[str, Any]:
        """监控页面元素变化"""
        task = BrowserTask(
            task_description=f"Monitor the element '{element_selector}' on the page for changes, checking every {check_interval} seconds for up to {max_checks} times",
            url=url,
            max_steps=max_checks + 5,
            timeout=check_interval * max_checks + 60
        )
        
        return await self.execute_task(task)
    
    async def automate_workflow(self, workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行复杂的自动化工作流"""
        workflow_description = "Execute the following workflow steps:\n"
        
        for i, step in enumerate(workflow_steps, 1):
            action = step.get('action', '')
            target = step.get('target', '')
            value = step.get('value', '')
            
            if action == 'navigate':
                workflow_description += f"{i}. Navigate to {target}\n"
            elif action == 'click':
                workflow_description += f"{i}. Click on {target}\n"
            elif action == 'type':
                workflow_description += f"{i}. Type '{value}' in {target}\n"
            elif action == 'wait':
                workflow_description += f"{i}. Wait for {target} to appear\n"
            elif action == 'extract':
                workflow_description += f"{i}. Extract {target}\n"
            else:
                workflow_description += f"{i}. {action} {target} {value}\n"
        
        task = BrowserTask(
            task_description=workflow_description,
            max_steps=len(workflow_steps) * 3 + 10,
            extract_data=True
        )
        
        return await self.execute_task(task)
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """同步执行接口"""
        try:
            if action == "search_and_extract":
                query = kwargs.get('query', '')
                search_engine = kwargs.get('search_engine', 'google')
                return asyncio.run(self.search_and_extract(query, search_engine))
            
            elif action == "navigate_and_extract":
                url = kwargs.get('url', '')
                extraction_task = kwargs.get('extraction_task', 'Extract all important information from this page')
                return asyncio.run(self.navigate_and_extract(url, extraction_task))
            
            elif action == "fill_form":
                url = kwargs.get('url', '')
                form_data = kwargs.get('form_data', {})
                submit = kwargs.get('submit', False)
                return asyncio.run(self.fill_form(url, form_data, submit))
            
            elif action == "monitor_changes":
                url = kwargs.get('url', '')
                element_selector = kwargs.get('element_selector', '')
                check_interval = kwargs.get('check_interval', 60)
                max_checks = kwargs.get('max_checks', 10)
                return asyncio.run(self.monitor_changes(url, element_selector, check_interval, max_checks))
            
            elif action == "automate_workflow":
                workflow_steps = kwargs.get('workflow_steps', [])
                return asyncio.run(self.automate_workflow(workflow_steps))
            
            elif action == "custom_task":
                task_description = kwargs.get('task_description', '')
                url = kwargs.get('url')
                max_steps = kwargs.get('max_steps', 50)
                headless = kwargs.get('headless', self.default_headless)
                timeout = kwargs.get('timeout', self.default_timeout)
                
                task = BrowserTask(
                    task_description=task_description,
                    url=url,
                    max_steps=max_steps,
                    headless=headless,
                    timeout=timeout
                )
                
                return asyncio.run(self.execute_task(task))
            
            else:
                return {
                    'success': False,
                    'error': f"Unknown action: {action}",
                    'available_actions': [
                        'search_and_extract',
                        'navigate_and_extract', 
                        'fill_form',
                        'monitor_changes',
                        'automate_workflow',
                        'custom_task'
                    ]
                }
                
        except Exception as e:
            logger.error(f"BrowserUseTool execution failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _run(self, input_data: str) -> str:
        """同步执行接口（LangChain BaseTool 要求）"""
        try:
            # 解析输入数据
            if isinstance(input_data, str):
                try:
                    data = json.loads(input_data)
                except json.JSONDecodeError:
                    # 如果不是 JSON，当作简单的任务描述
                    data = {"action": "custom_task", "task_description": input_data}
            else:
                data = input_data
            
            action = data.get("action", "custom_task")
            
            # 执行相应的动作
            result = self.execute(action=action, **data.get("parameters", {}))
            
            # 返回 JSON 格式的结果
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"BrowserUseTool execution failed: {e}", exc_info=True)
            return json.dumps({
                'success': False,
                'error': str(e)
            })
    
    async def _arun(self, input_data: str) -> str:
        """异步执行接口（LangChain BaseTool 要求）"""
        # 对于 browser-use，我们使用同步包装器
        # 因为 execute() 方法内部已经处理了异步操作
        return self._run(input_data)

# 使用示例
async def example_usage():
    """使用示例"""
    config = {
        'llm_provider': 'openai',
        'llm_model': 'gpt-4o',
        'browser': {
            'headless': True,
            'timeout': 300
        },
        'output_dir': 'browser_outputs'
    }
    
    tool = BrowserUseTool(config)
    
    # 示例 1: 搜索并提取信息
    search_result = await tool.search_and_extract(
        query="DeepResearch AI research automation",
        search_engine="google"
    )
    print("Search result:", search_result)
    
    # 示例 2: 导航并提取信息
    extract_result = await tool.navigate_and_extract(
        url="https://github.com/browser-use/browser-use",
        extraction_task="Extract the project description, features, and installation instructions"
    )
    print("Extract result:", extract_result)
    
    # 示例 3: 自动化工作流
    workflow_result = await tool.automate_workflow([
        {'action': 'navigate', 'target': 'https://example.com'},
        {'action': 'click', 'target': 'search button'},
        {'action': 'type', 'target': 'search input', 'value': 'AI research'},
        {'action': 'click', 'target': 'submit button'},
        {'action': 'extract', 'target': 'search results'}
    ])
    print("Workflow result:", workflow_result)

if __name__ == "__main__":
    asyncio.run(example_usage()) 