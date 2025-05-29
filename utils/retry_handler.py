"""
Retry handler with exponential backoff and various retry strategies.
Provides robust error handling for external API calls and operations.
"""

import asyncio
import time
import random
from typing import Callable, Any, Optional, List, Dict, Union
from dataclasses import dataclass
from enum import Enum
from functools import wraps

from utils.logger import LoggerMixin


class RetryStrategy(Enum):
    """Retry strategies."""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    RANDOM_JITTER = "random_jitter"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    backoff_factor: float = 2.0
    jitter: bool = True
    exceptions: tuple = (Exception,)
    retry_on_result: Optional[Callable[[Any], bool]] = None


class RetryHandler(LoggerMixin):
    """
    Retry handler with configurable strategies and error handling.
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry handler.
        
        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()
        self.retry_stats: Dict[str, Dict[str, Any]] = {}
    
    def retry(
        self,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None,
        strategy: Optional[RetryStrategy] = None,
        exceptions: Optional[tuple] = None
    ):
        """
        Decorator for adding retry logic to functions.
        
        Args:
            max_retries: Maximum number of retries
            base_delay: Base delay between retries
            strategy: Retry strategy
            exceptions: Exceptions to retry on
        
        Returns:
            Decorated function with retry logic
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.execute_with_retry(
                    func,
                    *args,
                    max_retries=max_retries,
                    base_delay=base_delay,
                    strategy=strategy,
                    exceptions=exceptions,
                    **kwargs
                )
            return wrapper
        return decorator
    
    def async_retry(
        self,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None,
        strategy: Optional[RetryStrategy] = None,
        exceptions: Optional[tuple] = None
    ):
        """
        Decorator for adding retry logic to async functions.
        
        Args:
            max_retries: Maximum number of retries
            base_delay: Base delay between retries
            strategy: Retry strategy
            exceptions: Exceptions to retry on
        
        Returns:
            Decorated async function with retry logic
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.execute_with_retry_async(
                    func,
                    *args,
                    max_retries=max_retries,
                    base_delay=base_delay,
                    strategy=strategy,
                    exceptions=exceptions,
                    **kwargs
                )
            return wrapper
        return decorator
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None,
        strategy: Optional[RetryStrategy] = None,
        exceptions: Optional[tuple] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            max_retries: Maximum number of retries
            base_delay: Base delay between retries
            strategy: Retry strategy
            exceptions: Exceptions to retry on
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Last exception if all retries failed
        """
        max_retries = max_retries or self.config.max_retries
        base_delay = base_delay or self.config.base_delay
        strategy = strategy or self.config.strategy
        exceptions = exceptions or self.config.exceptions
        
        func_name = getattr(func, '__name__', str(func))
        
        # Initialize stats
        if func_name not in self.retry_stats:
            self.retry_stats[func_name] = {
                "total_calls": 0,
                "total_retries": 0,
                "success_count": 0,
                "failure_count": 0
            }
        
        stats = self.retry_stats[func_name]
        stats["total_calls"] += 1
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                self.log_debug(f"Executing {func_name} (attempt {attempt + 1}/{max_retries + 1})")
                
                result = func(*args, **kwargs)
                
                # Check if result should trigger retry
                if self.config.retry_on_result and self.config.retry_on_result(result):
                    if attempt < max_retries:
                        self.log_warning(f"{func_name} returned retry-triggering result, retrying...")
                        delay = self._calculate_delay(attempt, base_delay, strategy)
                        time.sleep(delay)
                        stats["total_retries"] += 1
                        continue
                    else:
                        self.log_error(f"{func_name} failed after {max_retries} retries (result-based)")
                        stats["failure_count"] += 1
                        return result
                
                # Success
                if attempt > 0:
                    self.log_info(f"{func_name} succeeded after {attempt} retries")
                
                stats["success_count"] += 1
                return result
                
            except exceptions as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = self._calculate_delay(attempt, base_delay, strategy)
                    self.log_warning(f"{func_name} failed (attempt {attempt + 1}): {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                    stats["total_retries"] += 1
                else:
                    self.log_error(f"{func_name} failed after {max_retries} retries: {e}")
                    stats["failure_count"] += 1
                    break
            
            except Exception as e:
                # Non-retryable exception
                self.log_error(f"{func_name} failed with non-retryable exception: {e}")
                stats["failure_count"] += 1
                raise
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"Function {func_name} failed after {max_retries} retries")
    
    async def execute_with_retry_async(
        self,
        func: Callable,
        *args,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None,
        strategy: Optional[RetryStrategy] = None,
        exceptions: Optional[tuple] = None,
        **kwargs
    ) -> Any:
        """
        Execute async function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            max_retries: Maximum number of retries
            base_delay: Base delay between retries
            strategy: Retry strategy
            exceptions: Exceptions to retry on
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Last exception if all retries failed
        """
        max_retries = max_retries or self.config.max_retries
        base_delay = base_delay or self.config.base_delay
        strategy = strategy or self.config.strategy
        exceptions = exceptions or self.config.exceptions
        
        func_name = getattr(func, '__name__', str(func))
        
        # Initialize stats
        if func_name not in self.retry_stats:
            self.retry_stats[func_name] = {
                "total_calls": 0,
                "total_retries": 0,
                "success_count": 0,
                "failure_count": 0
            }
        
        stats = self.retry_stats[func_name]
        stats["total_calls"] += 1
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                self.log_debug(f"Executing {func_name} (attempt {attempt + 1}/{max_retries + 1})")
                
                result = await func(*args, **kwargs)
                
                # Check if result should trigger retry
                if self.config.retry_on_result and self.config.retry_on_result(result):
                    if attempt < max_retries:
                        self.log_warning(f"{func_name} returned retry-triggering result, retrying...")
                        delay = self._calculate_delay(attempt, base_delay, strategy)
                        await asyncio.sleep(delay)
                        stats["total_retries"] += 1
                        continue
                    else:
                        self.log_error(f"{func_name} failed after {max_retries} retries (result-based)")
                        stats["failure_count"] += 1
                        return result
                
                # Success
                if attempt > 0:
                    self.log_info(f"{func_name} succeeded after {attempt} retries")
                
                stats["success_count"] += 1
                return result
                
            except exceptions as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = self._calculate_delay(attempt, base_delay, strategy)
                    self.log_warning(f"{func_name} failed (attempt {attempt + 1}): {e}. Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    stats["total_retries"] += 1
                else:
                    self.log_error(f"{func_name} failed after {max_retries} retries: {e}")
                    stats["failure_count"] += 1
                    break
            
            except Exception as e:
                # Non-retryable exception
                self.log_error(f"{func_name} failed with non-retryable exception: {e}")
                stats["failure_count"] += 1
                raise
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"Function {func_name} failed after {max_retries} retries")
    
    def _calculate_delay(
        self,
        attempt: int,
        base_delay: float,
        strategy: RetryStrategy
    ) -> float:
        """
        Calculate delay for retry attempt.
        
        Args:
            attempt: Current attempt number (0-based)
            base_delay: Base delay
            strategy: Retry strategy
        
        Returns:
            Delay in seconds
        """
        if strategy == RetryStrategy.FIXED_DELAY:
            delay = base_delay
        
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (self.config.backoff_factor ** attempt)
        
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * (attempt + 1)
        
        elif strategy == RetryStrategy.RANDOM_JITTER:
            delay = base_delay + random.uniform(0, base_delay)
        
        else:
            delay = base_delay
        
        # Apply jitter if enabled
        if self.config.jitter and strategy != RetryStrategy.RANDOM_JITTER:
            jitter = random.uniform(0.1, 0.3) * delay
            delay += jitter
        
        # Ensure delay doesn't exceed maximum
        delay = min(delay, self.config.max_delay)
        
        return delay
    
    def get_retry_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get retry statistics for all functions."""
        return self.retry_stats.copy()
    
    def reset_stats(self):
        """Reset retry statistics."""
        self.retry_stats.clear()
        self.log_info("Retry statistics reset")
    
    def get_success_rate(self, func_name: str) -> float:
        """
        Get success rate for a specific function.
        
        Args:
            func_name: Function name
        
        Returns:
            Success rate (0.0 to 1.0)
        """
        if func_name not in self.retry_stats:
            return 0.0
        
        stats = self.retry_stats[func_name]
        total_calls = stats["total_calls"]
        
        if total_calls == 0:
            return 0.0
        
        return stats["success_count"] / total_calls


class CircuitBreaker(LoggerMixin):
    """
    Circuit breaker pattern implementation for preventing cascade failures.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: tuple = (Exception,)
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            expected_exception: Exceptions that count as failures
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for circuit breaker."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Exception if circuit is open or function fails
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
                self.log_info("Circuit breaker entering half-open state")
            else:
                raise RuntimeError("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        if self.state == "half-open":
            self.state = "closed"
            self.log_info("Circuit breaker closed after successful recovery")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            self.log_warning(f"Circuit breaker opened after {self.failure_count} failures")


# Global retry handler instance
retry_handler = RetryHandler()

# Convenience decorators
def retry_on_exception(
    max_retries: int = 3,
    base_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    exceptions: tuple = (Exception,)
):
    """Convenience decorator for retry on exception."""
    return retry_handler.retry(
        max_retries=max_retries,
        base_delay=base_delay,
        strategy=strategy,
        exceptions=exceptions
    )


def async_retry_on_exception(
    max_retries: int = 3,
    base_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    exceptions: tuple = (Exception,)
):
    """Convenience decorator for async retry on exception."""
    return retry_handler.async_retry(
        max_retries=max_retries,
        base_delay=base_delay,
        strategy=strategy,
        exceptions=exceptions
    ) 