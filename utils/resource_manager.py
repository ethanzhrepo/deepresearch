"""
Resource manager for DeepResearch system.
Manages lifecycle of browser instances, database connections, and other resources.
"""

import asyncio
import weakref
import uuid
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import threading
import time
from abc import ABC, abstractmethod
import warnings

from utils.logger import LoggerMixin


class ResourceState(Enum):
    """Resource states."""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class ResourceInfo:
    """Resource information."""
    resource_id: str
    resource_type: str
    state: ResourceState
    created_at: float
    last_used: float
    use_count: int = 0
    max_uses: Optional[int] = None
    ttl: Optional[float] = None  # Time to live in seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


T = TypeVar('T')


class ResourceFactory(ABC, Generic[T]):
    """Abstract resource factory."""
    
    @abstractmethod
    async def create_resource(self, **kwargs) -> T:
        """Create a new resource instance."""
        pass
    
    @abstractmethod
    async def destroy_resource(self, resource: T) -> None:
        """Destroy a resource instance."""
        pass
    
    @abstractmethod
    def validate_resource(self, resource: T) -> bool:
        """Validate if resource is still usable."""
        pass


class BrowserResourceFactory(ResourceFactory):
    """Factory for browser resources."""
    
    async def create_resource(self, **kwargs) -> Any:
        """Create a new browser instance."""
        try:
            from tools.browser_agent import BrowserAgent
            browser = BrowserAgent()
            await browser.__aenter__()
            return browser
        except ImportError:
            # 如果没有浏览器代理，返回模拟对象
            return MockBrowser()
    
    async def destroy_resource(self, resource: Any) -> None:
        """Destroy browser instance."""
        try:
            if hasattr(resource, '__aexit__'):
                await resource.__aexit__(None, None, None)
        except Exception:
            pass  # Ignore cleanup errors
    
    def validate_resource(self, resource: Any) -> bool:
        """Validate browser resource."""
        try:
            return hasattr(resource, 'execute_action')
        except Exception:
            return False


class MockBrowser:
    """Mock browser for testing."""
    
    async def execute_action(self, action):
        """Mock execute action."""
        return type('Result', (), {'success': True, 'data': {'mock': True}})()


class ResourceManager(LoggerMixin):
    """
    Global resource manager for the DeepResearch system.
    """
    
    def __init__(self):
        """Initialize resource manager."""
        self._pools: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._closed = False
    
    def create_pool(
        self,
        name: str,
        factory: ResourceFactory,
        **pool_kwargs
    ) -> 'ResourcePool':
        """
        Create a new resource pool.
        
        Args:
            name: Pool name
            factory: Resource factory
            **pool_kwargs: Pool configuration
        
        Returns:
            Resource pool instance
        """
        with self._lock:
            if self._closed:
                raise RuntimeError("Resource manager is closed")
            
            if name in self._pools:
                raise ValueError(f"Pool '{name}' already exists")
            
            pool = ResourcePool(factory, **pool_kwargs)
            self._pools[name] = pool
            
            self.log_info(f"Created resource pool '{name}'")
            return pool
    
    def get_pool(self, name: str) -> Optional['ResourcePool']:
        """
        Get a resource pool by name.
        
        Args:
            name: Pool name
        
        Returns:
            Resource pool or None if not found
        """
        with self._lock:
            return self._pools.get(name)
    
    async def close_pool(self, name: str):
        """
        Close a resource pool.
        
        Args:
            name: Pool name
        """
        with self._lock:
            pool = self._pools.pop(name, None)
        
        if pool:
            await pool.close()
            self.log_info(f"Closed resource pool '{name}'")
    
    async def close_all(self):
        """Close all resource pools."""
        self._closed = True
        
        pools = list(self._pools.values())
        self._pools.clear()
        
        # Close all pools concurrently
        if pools:
            await asyncio.gather(
                *[pool.close() for pool in pools],
                return_exceptions=True
            )
        
        self.log_info("All resource pools closed")
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools."""
        with self._lock:
            return {
                name: pool.get_stats()
                for name, pool in self._pools.items()
            }


class ResourcePool(LoggerMixin, Generic[T]):
    """Generic resource pool with lifecycle management."""
    
    def __init__(
        self,
        factory: ResourceFactory[T],
        min_size: int = 0,
        max_size: int = 10,
        max_idle_time: float = 300.0,  # 5 minutes
        max_uses: Optional[int] = None,
        cleanup_interval: float = 60.0,  # 1 minute
        acquire_timeout: float = 30.0  # 30 seconds
    ):
        """
        Initialize resource pool.
        
        Args:
            factory: Resource factory
            min_size: Minimum pool size
            max_size: Maximum pool size
            max_idle_time: Maximum idle time before cleanup
            max_uses: Maximum uses per resource
            cleanup_interval: Cleanup interval in seconds
            acquire_timeout: Timeout for acquiring resources
        """
        self.factory = factory
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.max_uses = max_uses
        self.cleanup_interval = cleanup_interval
        self.acquire_timeout = acquire_timeout
        
        self._resources: Dict[str, T] = {}
        self._resource_info: Dict[str, ResourceInfo] = {}
        self._available: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._closed = False
        self._waiters: List[asyncio.Future] = []
        
        # Start cleanup task
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Cleanup loop for expired resources."""
        while not self._closed:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_resources()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log_error(f"Cleanup loop error: {e}")
    
    async def _cleanup_expired_resources(self):
        """Clean up expired resources."""
        current_time = time.time()
        expired_ids = []
        
        async with self._lock:
            for resource_id, info in self._resource_info.items():
                # Check if resource is expired
                if (info.state == ResourceState.IDLE and 
                    current_time - info.last_used > self.max_idle_time):
                    expired_ids.append(resource_id)
                elif (self.max_uses and info.use_count >= self.max_uses):
                    expired_ids.append(resource_id)
                elif (info.ttl and current_time - info.created_at > info.ttl):
                    expired_ids.append(resource_id)
        
        # Remove expired resources
        for resource_id in expired_ids:
            await self._remove_resource(resource_id)
    
    async def _remove_resource(self, resource_id: str):
        """Remove a resource from the pool."""
        async with self._lock:
            resource = self._resources.pop(resource_id, None)
            info = self._resource_info.pop(resource_id, None)
            
            if resource and info:
                info.state = ResourceState.CLOSED
                try:
                    await self.factory.destroy_resource(resource)
                    self.log_debug(f"Removed expired resource {resource_id}")
                except Exception as e:
                    self.log_error(f"Error destroying resource {resource_id}: {e}")
    
    async def _create_resource(self) -> Optional[str]:
        """Create a new resource."""
        if len(self._resources) >= self.max_size:
            return None
        
        try:
            resource = await self.factory.create_resource()
            resource_id = str(uuid.uuid4())
            current_time = time.time()
            
            info = ResourceInfo(
                resource_id=resource_id,
                resource_type=type(resource).__name__,
                state=ResourceState.IDLE,
                created_at=current_time,
                last_used=current_time,
                max_uses=self.max_uses
            )
            
            self._resources[resource_id] = resource
            self._resource_info[resource_id] = info
            
            self.log_debug(f"Created new resource {resource_id}")
            return resource_id
            
        except Exception as e:
            self.log_error(f"Failed to create resource: {e}")
            return None
    
    async def acquire(self, timeout: Optional[float] = None) -> T:
        """
        Acquire a resource from the pool.
        
        Args:
            timeout: Timeout for acquiring resource
        
        Returns:
            Resource instance
        
        Raises:
            asyncio.TimeoutError: If timeout is exceeded
            RuntimeError: If pool is closed
        """
        if self._closed:
            raise RuntimeError("Resource pool is closed")
        
        timeout = timeout or self.acquire_timeout
        
        try:
            # Try to get an available resource
            resource_id = await self._get_available_resource(timeout)
            
            async with self._lock:
                resource = self._resources[resource_id]
                info = self._resource_info[resource_id]
                
                # Validate resource
                if not self.factory.validate_resource(resource):
                    await self._remove_resource(resource_id)
                    # Retry with remaining timeout
                    remaining_timeout = max(0, timeout - 1)
                    return await self.acquire(remaining_timeout)
                
                # Mark as active
                info.state = ResourceState.ACTIVE
                info.last_used = time.time()
                info.use_count += 1
                
                self.log_debug(f"Acquired resource {resource_id}")
                return resource
                
        except asyncio.TimeoutError:
            self.log_warning(f"Resource acquisition timeout after {timeout}s")
            raise
    
    async def _get_available_resource(self, timeout: Optional[float] = None) -> str:
        """Get an available resource ID with timeout support."""
        start_time = time.time()
        
        while True:
            # Check for idle resources
            async with self._lock:
                for resource_id, info in self._resource_info.items():
                    if info.state == ResourceState.IDLE:
                        return resource_id
                
                # Try to create a new resource
                if len(self._resources) < self.max_size:
                    new_resource_id = await self._create_resource()
                    if new_resource_id:
                        return new_resource_id
            
            # Calculate remaining timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                remaining_timeout = timeout - elapsed
                if remaining_timeout <= 0:
                    raise asyncio.TimeoutError("Resource acquisition timeout")
            else:
                remaining_timeout = None
            
            # Wait for a resource to become available with timeout
            future = asyncio.Future()
            self._waiters.append(future)
            try:
                if remaining_timeout is not None:
                    await asyncio.wait_for(future, timeout=remaining_timeout)
                else:
                    await future
            except asyncio.CancelledError:
                if future in self._waiters:
                    self._waiters.remove(future)
                raise
            except asyncio.TimeoutError:
                if future in self._waiters:
                    self._waiters.remove(future)
                raise
    
    async def release(self, resource: T):
        """
        Release a resource back to the pool.
        
        Args:
            resource: Resource to release
        """
        async with self._lock:
            # Find the resource ID
            resource_id = None
            for rid, res in self._resources.items():
                if res is resource:
                    resource_id = rid
                    break
            
            if resource_id is None:
                self.log_warning("Attempted to release unknown resource")
                return
            
            info = self._resource_info[resource_id]
            
            # Validate resource before returning to pool
            if self.factory.validate_resource(resource):
                info.state = ResourceState.IDLE
                info.last_used = time.time()
                self.log_debug(f"Released resource {resource_id}")
                
                # Notify waiters
                if self._waiters:
                    waiter = self._waiters.pop(0)
                    if not waiter.cancelled():
                        waiter.set_result(None)
            else:
                # Resource is invalid, remove it
                await self._remove_resource(resource_id)
    
    @asynccontextmanager
    async def acquire_context(self, timeout: Optional[float] = None):
        """
        Context manager for acquiring and releasing resources.
        
        Args:
            timeout: Timeout for acquiring resource
        
        Yields:
            Resource instance
        """
        resource = await self.acquire(timeout)
        try:
            yield resource
        finally:
            await self.release(resource)
    
    async def ensure_min_size(self):
        """Ensure the pool has at least min_size resources."""
        async with self._lock:
            current_size = len(self._resources)
            if current_size < self.min_size:
                tasks = []
                for _ in range(self.min_size - current_size):
                    tasks.append(self._create_resource())
                
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        idle_count = sum(
            1 for info in self._resource_info.values()
            if info.state == ResourceState.IDLE
        )
        active_count = sum(
            1 for info in self._resource_info.values()
            if info.state == ResourceState.ACTIVE
        )
        
        return {
            "total_resources": len(self._resources),
            "idle_resources": idle_count,
            "active_resources": active_count,
            "waiters": len(self._waiters),
            "min_size": self.min_size,
            "max_size": self.max_size,
            "closed": self._closed
        }
    
    async def close(self):
        """Close the resource pool."""
        self._closed = True
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all waiters
        for waiter in self._waiters:
            if not waiter.cancelled():
                waiter.cancel()
        self._waiters.clear()
        
        # Close all resources
        async with self._lock:
            for resource_id in list(self._resources.keys()):
                await self._remove_resource(resource_id)
        
        self.log_info("Resource pool closed")


# Global resource manager instance
# DEPRECATED: Use get_resource_manager() from utils.service_container instead
def _get_deprecated_resource_manager():
    """Internal function to handle deprecated global access."""
    warnings.warn(
        "Direct import of resource_manager is deprecated. "
        "Use get_resource_manager() from utils.service_container instead.",
        DeprecationWarning,
        stacklevel=3
    )
    from utils.service_container import get_resource_manager
    return get_resource_manager()

# 保持向后兼容性的全局实例
resource_manager = _get_deprecated_resource_manager()


# Convenience functions for browser resources
async def get_browser_pool() -> ResourcePool:
    """Get or create browser resource pool."""
    pool = resource_manager.get_pool("browser")
    if pool is None:
        factory = BrowserResourceFactory()
        pool = resource_manager.create_pool(
            "browser",
            factory,
            min_size=0,
            max_size=3,
            max_idle_time=300.0,
            max_uses=10
        )
        # Ensure minimum size
        await pool.ensure_min_size()
    return pool


@asynccontextmanager
async def get_browser_resource():
    """Context manager for browser resource."""
    pool = await get_browser_pool()
    async with pool.acquire_context() as browser:
        yield browser 