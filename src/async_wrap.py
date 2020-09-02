"""for wrapping sync code in async"""
#from https://dev.to/0xbf/turn-sync-function-to-async-python-tips-58nn

import asyncio
from functools import wraps, partial

def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run 

'''
example usage:

async_sleep = async_wrap(time.sleep)


async def count():
    print("func start")
    await async_sleep(1)
    print("func end")


async def main():
    await asyncio.gather(count(), count(), count())


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(f"Time elapse: {end-start}")
'''