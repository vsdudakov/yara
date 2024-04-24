import asyncio
import inspect
import typing as tp
from functools import wraps

import celery


class AsyncCeleryTask(celery.Task):
    abstract = True

    def __init__(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        super().__init__(*args, **kwargs)
        if inspect.iscoroutinefunction(self.run):  # type: ignore [has-type]
            self.run = self._async_run_wrapper(self.run)  # type: ignore [has-type]

    def _async_run_wrapper(self, func: tp.Any) -> tp.Any:
        @wraps(func)
        def wrapper(*args: tp.Any, **kwargs: tp.Any) -> None:
            async def wrapped_func(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
                from yara.main import fastapi_app_lifespan, root_app

                async with fastapi_app_lifespan(root_app.get_asgi_app()):
                    kwargs["root_app"] = root_app
                    return await func(*args, **kwargs)

            return self.run_async(wrapped_func(*args, **kwargs))

        return wrapper

    def run_async(self, coro: tp.Any) -> tp.Any:
        return asyncio.run(coro)


class AsyncioTaskManager:
    def __init__(self) -> None:
        self.running_tasks: tp.Any = set()

    def asyncio_task(self, func: tp.Any) -> tp.Any:
        async def task_runner(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
            task = asyncio.create_task(func(*args, **kwargs))
            self.running_tasks.add(task)
            task.add_done_callback(lambda t: self.running_tasks.remove(t))
            return await task

        def delay(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
            return asyncio.ensure_future(task_runner(*args, **kwargs))

        func.delay = delay
        return func


asyncio_task_manager = AsyncioTaskManager()

asyncio_task = asyncio_task_manager.asyncio_task
celery_task = celery.shared_task
