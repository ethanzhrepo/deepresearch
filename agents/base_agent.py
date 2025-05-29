"""
Base Agent class with LLM configuration support.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from utils.logger import LoggerMixin
from config import config


class BaseAgent(LoggerMixin, ABC):
    """
    Base class for all research agents with intelligent LLM selection.
    """
    
    def __init__(self, llm_provider: Optional[str] = None, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize base agent with LLM configuration.
        
        Args:
            llm_provider: Specific LLM provider to use (overrides config)
            custom_config: Custom configuration parameters
        """
        super().__init__()
        
        self.custom_config = custom_config or {}
        
        # 决定使用哪个 LLM 提供商
        self.llm_provider = self._select_llm_provider(llm_provider)
        
        # 初始化 LLM 实例
        self.llm = self._initialize_llm()
        
        # 初始化其他组件
        self._initialize_components()
        
        self.log_info(f"Initialized {self.__class__.__name__} with LLM provider: {self.llm_provider}")
    
    def _select_llm_provider(self, explicit_provider: Optional[str] = None) -> str:
        """
        选择最适合的 LLM 提供商。
        
        Args:
            explicit_provider: 显式指定的提供商
        
        Returns:
            选择的 LLM 提供商名称
        """
        # 优先级：显式指定 > Agent特定配置 > 全局默认
        
        if explicit_provider:
            self.log_debug(f"Using explicitly specified LLM provider: {explicit_provider}")
            return explicit_provider
        
        # 检查 Agent 特定配置
        agent_llms = getattr(config.llm, 'agent_llms', {})
        agent_name = self.__class__.__name__
        
        if agent_name in agent_llms:
            provider = agent_llms[agent_name]
            self.log_debug(f"Using agent-specific LLM provider for {agent_name}: {provider}")
            return provider
        
        # 使用全局默认
        provider = config.llm.default_provider
        self.log_debug(f"Using default LLM provider for {agent_name}: {provider}")
        return provider
    
    def _initialize_llm(self):
        """初始化 LLM 实例。"""
        try:
            llm_config_data = config.get_llm_config(self.llm_provider)
            
            if self.llm_provider == "openai":
                from llm.openai import OpenAIWrapper
                return OpenAIWrapper(llm_config_data)
            elif self.llm_provider == "claude":
                from llm.claude import ClaudeWrapper
                return ClaudeWrapper(llm_config_data)
            elif self.llm_provider == "gemini":
                from llm.gemini import GeminiWrapper
                return GeminiWrapper(llm_config_data)
            elif self.llm_provider == "ollama":
                from llm.ollama import OllamaWrapper
                return OllamaWrapper(llm_config_data)
            else:
                # 回退到默认提供商
                default_provider = config.llm.default_provider
                default_config = config.get_llm_config(default_provider)
                
                self.log_warning(f"Unknown LLM provider {self.llm_provider}, falling back to {default_provider}")
                
                if default_provider == "openai":
                    from llm.openai import OpenAIWrapper
                    return OpenAIWrapper(default_config)
                elif default_provider == "claude":
                    from llm.claude import ClaudeWrapper
                    return ClaudeWrapper(default_config)
                elif default_provider == "gemini":
                    from llm.gemini import GeminiWrapper
                    return GeminiWrapper(default_config)
                elif default_provider == "ollama":
                    from llm.ollama import OllamaWrapper
                    return OllamaWrapper(default_config)
                else:
                    raise ValueError(f"No valid LLM provider available")
                    
        except Exception as e:
            self.log_error(f"Failed to initialize LLM for {self.__class__.__name__}: {e}")
            raise
    
    def _initialize_components(self):
        """初始化 Agent 特定的组件。子类可以重写此方法。"""
        # 可选：从服务容器获取常用服务
        try:
            from utils.service_container import get_service_container
            self.service_container = get_service_container()
            
            # 子类可以通过 self.service_container.get("service_name") 获取服务
            self.log_debug("Service container initialized for agent")
        except Exception as e:
            self.log_warning(f"Failed to initialize service container: {e}")
            self.service_container = None
    
    def get_llm_parameters(self, task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取适合当前任务的 LLM 参数。
        
        Args:
            task_type: 任务类型（用于获取任务特定参数）
        
        Returns:
            LLM 参数字典
        """
        params = {}
        
        # 从任务特定配置获取参数
        if task_type:
            task_specific_config = getattr(config.llm, 'task_specific_models', {})
            if task_type in task_specific_config:
                task_config = task_specific_config[task_type]
                for key in ['model', 'temperature', 'max_tokens', 'top_p', 'top_k', 
                           'frequency_penalty', 'presence_penalty', 'stop']:
                    if key in task_config:
                        params[key] = task_config[key]
        
        # 从自定义配置覆盖
        if 'llm_params' in self.custom_config:
            params.update(self.custom_config['llm_params'])
        
        # 设置默认值
        if 'max_tokens' not in params:
            params['max_tokens'] = 2000
        if 'temperature' not in params:
            params['temperature'] = 0.7
        
        return params
    
    async def generate_with_context(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        task_type: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        使用上下文生成内容。
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            task_type: 任务类型（用于获取特定参数）
            **kwargs: 额外的 LLM 参数
        
        Returns:
            LLM 响应
        """
        # 获取任务特定参数
        llm_params = self.get_llm_parameters(task_type)
        
        # 用传入的参数覆盖
        llm_params.update(kwargs)
        
        # 生成内容
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            **llm_params
        )
        
        return response
    
    @abstractmethod
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 Agent 特定的任务。
        
        Args:
            task_data: 任务数据
        
        Returns:
            任务执行结果
        """
        pass
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取 Agent 信息。"""
        return {
            "agent_name": self.__class__.__name__,
            "llm_provider": self.llm_provider,
            "capabilities": self.get_capabilities(),
            "status": "ready"
        }
    
    @abstractmethod
    def get_capabilities(self) -> list:
        """
        获取 Agent 的能力列表。
        
        Returns:
            能力列表
        """
        pass 