import asyncio


class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self):
        self._task.cancel()


class Scheduler:
    async def main(self, coro, time, loop):
        Timer(time, coro)
        await asyncio.sleep(time)
        await self.create_task(coro=coro, time=time, loop=loop)

    async def run(self, coro, time):
        loop = asyncio.get_event_loop()
        if not loop:
            loop = asyncio.new_event_loop()
            loop.run_forever()
            asyncio.set_event_loop(loop)

        await self.create_task(coro=coro, time=time, loop=loop)

    async def create_task(self, coro, time, loop):
        await loop.create_task(coro=self.main(coro=coro, time=time, loop=loop))
