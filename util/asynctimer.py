from typing import Any, Callable
import asyncio


class Timer:
    def __init__(self, timeout: int, callback: Callable[[Any], Any]) -> None:
        """
        Initializes the Timer.
        :param timeout: How long needs to be between each callback.
        :param callback: The callback that needs to happen per iteration.
        """
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self) -> None:
        """
        Executes the callback after a timeout.
        """
        await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self) -> None:
        """
        Cancels the existing task.
        """
        self._task.cancel()


class Scheduler:
    async def main(self,
                   coro: Callable[[Any], Any],
                   time: int,
                   loop: asyncio.AbstractEventLoop) -> None:
        """
        Main execution of the Scheduler.
        :param coro: The co-routine that needs to be executed.
        :param time: Integer indicating how many seconds before it runs again.
        :param loop: The Asyncio EventLoop that the task should run in.
        """
        Timer(time, coro)
        await asyncio.sleep(time)
        await self.create_task(coro=coro, time=time, loop=loop)

    async def run(self,
                  coro: Callable[[Any], Any],
                  time: int) -> None:
        """
        Selects the event loop and schedules the running of the co-routine.
        :param coro: The co-routine that needs to be executed.
        :param time: Integer indicating how many seconds before it runs again.
        """
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        if not loop:
            loop = asyncio.new_event_loop()
            loop.run_forever()
            asyncio.set_event_loop(loop)

        await self.create_task(coro=coro, time=time, loop=loop)

    async def create_task(self,
                          coro: Callable[[Any], Any],
                          time: int,
                          loop: asyncio.AbstractEventLoop) -> None:
        """
        Creates a task and adds it to the loop.
        :param coro: The co-routine that needs to be executed.
        :param time: Integer indicating how many seconds before it runs again.
        :param loop: The Asyncio EventLoop that the task should run in.
        """
        await loop.create_task(coro=self.main(coro=coro, time=time, loop=loop))
