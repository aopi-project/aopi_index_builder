import asyncio
from collections import Callable
from inspect import iscoroutinefunction
from typing import Any


async def run_smart_async(func: Callable[..., Any], *args: Any) -> Any:
    if iscoroutinefunction(func):
        returned = await func(*args)
    else:
        loop = asyncio.get_event_loop()
        returned = await loop.run_in_executor(None, func, *args)
    return returned
