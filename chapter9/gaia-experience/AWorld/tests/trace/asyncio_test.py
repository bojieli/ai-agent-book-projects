import asyncio

import pytest

import aworld.trace as trace
from aworld.logs.util import logger

trace.configure()


async def async_handler(name):
    async with trace.span("async_handler") as span:
        logger.info(f"async_handler start {name}")
        await asyncio.sleep(1)
        logger.info(f"async_handler end {name}")


async def async_handler2(name):
    span = trace.get_current_span()
    logger.info(f"async_handler2 span: {span.get_trace_id()}")
    logger.info(f"async_handler2 start {name}")
    await asyncio.sleep(1)
    logger.info(f"async_handler2 end {name}")


@pytest.mark.asyncio
async def test1():
    logger.info(f"hello test1")
    task = asyncio.create_task(async_handler('test1'))
    # await task
    logger.info(f"hello test1 end")


@pytest.mark.asyncio
async def test2():
    async with trace.span("test2") as span:
        logger.info(f"hello test2")
        task = asyncio.create_task(async_handler2(
            'test2'))
        # await task
        logger.info(f"hello test2 end")
