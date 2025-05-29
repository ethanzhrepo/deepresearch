"""
Service container for dependency injection in DeepResearch system.
Provides centralized management of core services with lazy loading and dependency injection.
"""

from typing import Dict, Any, Optional, Type, TypeVar, Callable
from threading import Lock
import inspect
import warnings

from utils.logger import LoggerMixin

T = TypeVar('T')


class ServiceContainer(LoggerMixin):
    """
    Service container for dependency injection.
    Manages singleton instances and provides lazy loading.
    """
    
    def __init__(self):
        """Initialize service container."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._lock = Lock()
    
    def register_singleton(self, service_name: str, instance: Any):
        """
        Register a singleton service instance.
        
        Args:
            service_name: Name of the service
            instance: Service instance
        """
        with self._lock:
            self._singletons[service_name] = instance
            self.log_debug(f"Registered singleton service: {service_name}")
    
    def register_factory(self, service_name: str, factory: Callable):
        """
        Register a factory function for creating service instances.
        
        Args:
            service_name: Name of the service
            factory: Factory function that creates the service
        """
        with self._lock:
            self._factories[service_name] = factory
            self.log_debug(f"Registered factory for service: {service_name}")
    
    def register_class(self, service_name: str, service_class: Type[T], *args, **kwargs):
        """
        Register a service class with constructor arguments.
        
        Args:
            service_name: Name of the service
            service_class: Service class
            *args: Constructor arguments
            **kwargs: Constructor keyword arguments
        """
        def factory():
            return service_class(*args, **kwargs)
        
        self.register_factory(service_name, factory)
    
    def get(self, service_name: str) -> Any:
        """
        Get a service instance.
        
        Args:
            service_name: Name of the service
        
        Returns:
            Service instance
        
        Raises:
            ValueError: If service is not registered
        """
        # Check singletons first
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # Check if we have a factory
        if service_name in self._factories:
            with self._lock:
                # Double-check pattern for thread safety
                if service_name in self._singletons:
                    return self._singletons[service_name]
                
                # Create new instance
                factory = self._factories[service_name]
                instance = factory()
                
                # Store as singleton
                self._singletons[service_name] = instance
                self.log_debug(f"Created singleton instance for service: {service_name}")
                
                return instance
        
        raise ValueError(f"Service '{service_name}' is not registered")
    
    def get_optional(self, service_name: str) -> Optional[Any]:
        """
        Get a service instance if it exists.
        
        Args:
            service_name: Name of the service
        
        Returns:
            Service instance or None if not found
        """
        try:
            return self.get(service_name)
        except ValueError:
            return None
    
    def has(self, service_name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            service_name: Name of the service
        
        Returns:
            True if service is registered
        """
        return service_name in self._singletons or service_name in self._factories
    
    def remove(self, service_name: str):
        """
        Remove a service from the container.
        
        Args:
            service_name: Name of the service
        """
        with self._lock:
            self._singletons.pop(service_name, None)
            self._factories.pop(service_name, None)
            self.log_debug(f"Removed service: {service_name}")
    
    def clear(self):
        """Clear all services from the container."""
        with self._lock:
            self._singletons.clear()
            self._factories.clear()
            self.log_debug("Cleared all services from container")
    
    def get_registered_services(self) -> Dict[str, str]:
        """
        Get list of all registered services.
        
        Returns:
            Dictionary mapping service names to their types
        """
        services = {}
        
        for name in self._singletons:
            services[name] = f"singleton:{type(self._singletons[name]).__name__}"
        
        for name in self._factories:
            if name not in services:  # Don't override singleton info
                services[name] = f"factory:{self._factories[name].__name__}"
        
        return services
    
    def inject_dependencies(self, target_class: Type[T]) -> Type[T]:
        """
        Decorator to inject dependencies into a class constructor.
        
        Args:
            target_class: Class to inject dependencies into
        
        Returns:
            Modified class with dependency injection
        """
        original_init = target_class.__init__
        
        def new_init(self, *args, **kwargs):
            # Get constructor signature
            sig = inspect.signature(original_init)
            
            # Inject services based on parameter names
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'args', 'kwargs']:
                    continue
                
                # Check if parameter name matches a service
                if param_name not in kwargs and self.has(param_name):
                    kwargs[param_name] = self.get(param_name)
            
            # Call original constructor
            original_init(self, *args, **kwargs)
        
        target_class.__init__ = new_init
        return target_class


# Global service container instance
_global_container: Optional[ServiceContainer] = None
_container_lock = Lock()


def get_service_container() -> ServiceContainer:
    """
    Get the global service container instance.
    
    Returns:
        Global ServiceContainer instance
    """
    global _global_container
    
    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = ServiceContainer()
                _initialize_default_services(_global_container)
    
    return _global_container


def _initialize_default_services(container: ServiceContainer):
    """
    Initialize default services in the container.
    
    Args:
        container: Service container to initialize
    """
    try:
        # Register core services with lazy loading
        
        # Search Engine Manager
        def create_search_manager():
            from tools.search_engines import SearchEngineManager
            return SearchEngineManager()
        container.register_factory("search_manager", create_search_manager)
        
        # Code Runner
        def create_code_runner():
            from tools.code_runner import CodeRunner
            return CodeRunner()
        container.register_factory("code_runner", create_code_runner)
        
        # Tool Registry
        def create_tool_registry():
            from tools.tool_registry import ToolRegistry
            return ToolRegistry()
        container.register_factory("tool_registry", create_tool_registry)
        
        # Resource Manager
        def create_resource_manager():
            from utils.resource_manager import ResourceManager
            return ResourceManager()
        container.register_factory("resource_manager", create_resource_manager)
        
        # Prompt Manager
        def create_prompt_manager():
            from utils.prompt_manager import PromptManager
            return PromptManager()
        container.register_factory("prompt_manager", create_prompt_manager)
        
        # Retry Handler
        def create_retry_handler():
            from utils.retry_handler import RetryHandler
            return RetryHandler()
        container.register_factory("retry_handler", create_retry_handler)
        
        container.log_info("Initialized default services in container")
        
    except Exception as e:
        container.log_error(f"Failed to initialize default services: {e}")


def inject_service(service_name: str):
    """
    Decorator to inject a specific service into a method or class.
    
    Args:
        service_name: Name of the service to inject
    
    Returns:
        Decorator function
    """
    def decorator(func_or_class):
        if inspect.isclass(func_or_class):
            # Class injection
            original_init = func_or_class.__init__
            
            def new_init(self, *args, **kwargs):
                container = get_service_container()
                if service_name not in kwargs and container.has(service_name):
                    kwargs[service_name] = container.get(service_name)
                original_init(self, *args, **kwargs)
            
            func_or_class.__init__ = new_init
            return func_or_class
        else:
            # Function injection
            def wrapper(*args, **kwargs):
                container = get_service_container()
                if service_name not in kwargs and container.has(service_name):
                    kwargs[service_name] = container.get(service_name)
                return func_or_class(*args, **kwargs)
            return wrapper
    
    return decorator


# Convenience functions for common services
def get_search_manager():
    """
    获取搜索引擎管理器实例。
    """
    container = get_service_container()
    if not container.has("search_manager"):
        try:
            from search.search_engine import SearchEngineManager
            container.register("search_manager", SearchEngineManager())
        except ImportError:
            # 如果搜索模块不可用，返回None
            return None
    return container.get("search_manager")


def get_code_runner():
    """
    获取代码执行器实例。
    """
    container = get_service_container()
    if not container.has("code_runner"):
        try:
            from tools.code_executor import CodeRunner
            container.register("code_runner", CodeRunner())
        except ImportError:
            # 如果代码执行器不可用，返回None
            return None
    return container.get("code_runner")


def get_tool_registry():
    """
    获取工具注册表实例。
    
    推荐使用此函数而不是直接导入 tools.tool_registry.tool_registry
    """
    container = get_service_container()
    if not container.has("tool_registry"):
        from tools.tool_registry import ToolRegistry
        container.register("tool_registry", ToolRegistry())
    return container.get("tool_registry")


def get_resource_manager():
    """
    获取资源管理器实例。
    
    推荐使用此函数而不是直接导入 utils.resource_manager.resource_manager
    """
    container = get_service_container()
    if not container.has("resource_manager"):
        from utils.resource_manager import ResourceManager
        container.register("resource_manager", ResourceManager())
    return container.get("resource_manager")


def get_prompt_manager():
    """
    获取提示管理器实例。
    
    推荐使用此函数而不是直接导入 utils.prompt_manager.prompt_manager
    """
    container = get_service_container()
    if not container.has("prompt_manager"):
        from utils.prompt_manager import PromptManager
        container.register("prompt_manager", PromptManager())
    return container.get("prompt_manager")


def get_retry_handler():
    """Get RetryHandler instance."""
    return get_service_container().get("retry_handler")


def get_async_tool_executor():
    """
    获取异步工具执行器实例。
    
    推荐使用此函数而不是 tools.async_tools.get_global_async_executor()
    """
    container = get_service_container()
    if not container.has("async_tool_executor"):
        # 优先从工具注册表获取
        tool_registry = get_tool_registry()
        if tool_registry:
            container.register("async_tool_executor", tool_registry.get_async_executor())
        else:
            # 回退到直接创建
            from tools.async_tools import AsyncToolExecutor
            container.register("async_tool_executor", AsyncToolExecutor())
    return container.get("async_tool_executor")


def get_config():
    """
    获取配置实例。
    """
    container = get_service_container()
    if not container.has("config"):
        from config import config
        container.register("config", config)
    return container.get("config")


# 批量注册核心服务
def register_core_services():
    """
    批量注册核心服务到服务容器。
    
    这个函数应该在应用启动时调用，确保所有核心服务都通过服务容器管理。
    """
    container = get_service_container()
    
    # 注册配置
    if not container.has("config"):
        from config import config
        container.register("config", config)
    
    # 注册工具注册表
    if not container.has("tool_registry"):
        from tools.tool_registry import ToolRegistry
        container.register("tool_registry", ToolRegistry())
    
    # 注册提示管理器
    if not container.has("prompt_manager"):
        from utils.prompt_manager import PromptManager
        container.register("prompt_manager", PromptManager())
    
    # 注册资源管理器
    if not container.has("resource_manager"):
        from utils.resource_manager import ResourceManager
        container.register("resource_manager", ResourceManager())
    
    # 注册搜索管理器（如果可用）
    if not container.has("search_manager"):
        try:
            from search.search_engine import SearchEngineManager
            container.register("search_manager", SearchEngineManager())
        except ImportError:
            pass  # 搜索模块不可用
    
    # 注册代码执行器（如果可用）
    if not container.has("code_runner"):
        try:
            from tools.code_executor import CodeRunner
            container.register("code_runner", CodeRunner())
        except ImportError:
            pass  # 代码执行器不可用
    
    # 注册异步工具执行器
    if not container.has("async_tool_executor"):
        tool_registry = container.get("tool_registry")
        if tool_registry:
            container.register("async_tool_executor", tool_registry.get_async_executor())
    
    return container


# 清理全局实例的函数
def cleanup_global_instances():
    """
    清理所有全局实例，主要用于测试或重启场景。
    """
    container = get_service_container()
    container.clear()


# 迁移助手函数
def migrate_from_global_imports():
    """
    迁移助手：将现有的全局导入迁移到服务容器。
    
    这个函数可以帮助现有代码逐步迁移到服务容器模式。
    """
    warnings.warn(
        "Global imports are deprecated. Use service container functions instead:\n"
        "- get_tool_registry() instead of importing tool_registry\n"
        "- get_prompt_manager() instead of importing prompt_manager\n"
        "- get_resource_manager() instead of importing resource_manager\n"
        "- get_async_tool_executor() instead of get_global_async_executor()",
        DeprecationWarning,
        stacklevel=2
    )
    
    # 确保核心服务已注册
    register_core_services()


# 服务健康检查
def check_service_health() -> Dict[str, bool]:
    """
    检查所有注册服务的健康状态。
    
    Returns:
        Dict mapping service names to their health status
    """
    container = get_service_container()
    health_status = {}
    
    service_checks = {
        "config": lambda: get_config() is not None,
        "tool_registry": lambda: get_tool_registry() is not None,
        "prompt_manager": lambda: get_prompt_manager() is not None,
        "resource_manager": lambda: get_resource_manager() is not None,
        "search_manager": lambda: get_search_manager() is not None,
        "code_runner": lambda: get_code_runner() is not None,
        "async_tool_executor": lambda: get_async_tool_executor() is not None,
    }
    
    for service_name, check_func in service_checks.items():
        try:
            health_status[service_name] = check_func()
        except Exception as e:
            health_status[service_name] = False
            print(f"Service {service_name} health check failed: {e}")
    
    return health_status 