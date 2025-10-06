"""Utilities for managing async event loops in evaluation."""

import asyncio
import threading
from typing import Optional, TypeVar, Coroutine
from functools import wraps

T = TypeVar("T")


class AsyncEventLoopManager:
    """
    Manages a persistent event loop running in a background thread.
    
    This is useful for running async code from synchronous contexts,
    particularly in LangSmith evaluations which expect synchronous functions.
    """

    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        """
        Get or create a persistent event loop running in a background thread.
        
        Returns:
            asyncio.AbstractEventLoop: The event loop instance
        """
        with self._lock:
            if self._loop is None or not self._loop.is_running():
                self._loop = asyncio.new_event_loop()

                def run_loop():
                    asyncio.set_event_loop(self._loop)
                    self._loop.run_forever()

                self._thread = threading.Thread(target=run_loop, daemon=True)
                self._thread.start()

            return self._loop

    def run_coroutine(
        self, coro: Coroutine[None, None, T], timeout: Optional[float] = None
    ) -> T:
        """
        Run a coroutine in the managed event loop from a synchronous context.
        
        Args:
            coro: The coroutine to run
            timeout: Optional timeout in seconds (default: None)
            
        Returns:
            The result of the coroutine
            
        Raises:
            TimeoutError: If the operation times out
            Exception: Any exception raised by the coroutine
        """
        loop = self.get_or_create_loop()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=timeout)

    def cleanup(self) -> None:
        """
        Stop and cleanup the event loop.
        
        This should be called at the end of evaluation to properly
        shutdown the background thread.
        """
        with self._lock:
            if self._loop is not None and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
                if self._thread is not None:
                    self._thread.join(timeout=5)
                self._loop = None
                self._thread = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup the loop."""
        self.cleanup()


# Global event loop manager instance
_global_loop_manager: Optional[AsyncEventLoopManager] = None


def get_global_loop_manager() -> AsyncEventLoopManager:
    """
    Get the global event loop manager instance.
    
    Returns:
        AsyncEventLoopManager: The global manager instance
    """
    global _global_loop_manager
    if _global_loop_manager is None:
        _global_loop_manager = AsyncEventLoopManager()
    return _global_loop_manager


def cleanup_global_loop_manager() -> None:
    """Cleanup the global event loop manager."""
    global _global_loop_manager
    if _global_loop_manager is not None:
        _global_loop_manager.cleanup()
        _global_loop_manager = None


def async_to_sync(timeout: Optional[float] = None):
    """
    Decorator to convert async functions to sync using the global loop manager.
    
    Args:
        timeout: Optional timeout in seconds
        
    Example:
        @async_to_sync(timeout=30)
        async def my_async_function(x: int) -> int:
            await asyncio.sleep(1)
            return x * 2
            
        # Can now call synchronously
        result = my_async_function(5)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_global_loop_manager()
            coro = func(*args, **kwargs)
            return manager.run_coroutine(coro, timeout=timeout)

        return wrapper

    return decorator
