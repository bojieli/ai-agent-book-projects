# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
import inspect
import os
import asyncio
import traceback
from concurrent.futures import Future
from concurrent.futures.process import ProcessPoolExecutor
from types import MethodType
from typing import List, Callable, Any, Dict

from aworld.config import RunConfig, ConfigDict
from aworld.logs.util import logger
from aworld.utils.common import sync_exec

LOCAL = "local"
SPARK = "spark"
RAY = "ray"
K8S = "k8s"


class RuntimeEngine(object):
    """Lightweight wrapper of computing engine runtime."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, conf: RunConfig):
        """Engine runtime instance initialize."""
        self.conf = ConfigDict(conf.model_dump())
        self.runtime = None
        register(conf.engine_name, self)

        # Initialize clients running on top of distributed computing engines
        pass

    def build_engine(self) -> 'RuntimeEngine':
        """Create computing engine runtime.

        If create more times in the same runtime instance, will get the same engine instance, like getOrCreate.
        """
        if self.runtime is not None:
            return self
        self._build_engine()
        return self

    @abc.abstractmethod
    def _build_engine(self) -> None:
        raise NotImplementedError("Base _build_engine not implemented!")

    @abc.abstractmethod
    def broadcast(self, data: Any):
        """Broadcast the data to all workers."""

    @abc.abstractmethod
    async def execute(self, funcs: List[Callable[..., Any]], *args, **kwargs) -> Dict[str, Any]:
        """Submission focuses on the execution of stateless tasks on the special engine cluster."""
        raise NotImplementedError("Base task execute not implemented!")

    def pre_execute(self):
        """Define the pre execution logic."""
        pass

    def post_execute(self):
        """Define the post execution logic."""
        pass

    @staticmethod
    def func_wrapper(func: Callable[..., Any], *args, **kwargs) -> Any:
        """Function is used to adapter computing form."""
        try:
            if inspect.iscoroutinefunction(func):
                res = sync_exec(func, *args, **kwargs)
            else:
                res = func(*args, **kwargs)
            return res
        except Exception as e:
            logger.error(f"⚠️ Function {getattr(func, '__name__', 'unknown')} execution failed: {e}")
            # Re-raise the exception to be handled by the executor
            raise


class LocalRuntime(RuntimeEngine):
    """Local runtime key is 'local', and execute tasks in local machine.

    Local runtime is used to verify or test locally.
    """

    def _build_engine(self):
        self.runtime = self

    async def execute(self, funcs: List[Callable[..., Any]], *args, **kwargs) -> Dict[str, Any]:
        # opt of the one task process
        if self.conf.get('reuse_process', True):
            results = {}
            coroutine_funcs = []
            sync_funcs = []
            for func in funcs:
                if inspect.iscoroutinefunction(func):
                    coroutine_funcs.append(func(*args, **kwargs))
                else:
                    sync_funcs.append(func)

            for func in sync_funcs:
                try:
                    res = func(*args, **kwargs)
                    results[res.id] = res
                except Exception as e:
                    logger.error(f"⚠️ Task execution failed: {e}, traceback: {traceback.format_exc()}")
                    raise

            try:
                for result in await asyncio.gather(*coroutine_funcs):
                    results[result.id] = result
            except Exception as e:
                logger.error(f"⚠️ Task execution failed: {e}, traceback: {traceback.format_exc()}")
                raise
            return results

        num_executor = self.conf.get('worker_num', os.cpu_count() - 1)
        num_process = len(funcs)
        if num_process > num_executor:
            num_process = num_executor

        if num_process <= 0:
            num_process = 1

        futures = []
        results = {}

        try:
            with ProcessPoolExecutor(num_process) as pool:
                for func in funcs:
                    futures.append(pool.submit(RuntimeEngine.func_wrapper, func, *args, **kwargs))

                # Wait for all futures to complete with timeout
                timeout = self.conf.get('timeout', 300)
                for future in futures:
                    try:
                        res = future.result(timeout=timeout)  # 5 minute timeout per task
                        if res and hasattr(res, 'id'):
                            results[res.id] = res
                    except TimeoutError:
                        logger.error(f"Task execution timed out after {timeout} seconds")
                    except Exception as e:
                        logger.error(f"Task execution failed: {e}, traceback: {traceback.format_exc()}")
                        if future.exception():
                            logger.debug(f"Exception details: {future.exception()}")
        except Exception as e:
            logger.error(f"ProcessPoolExecutor failed: {e}, traceback: {traceback.format_exc()}")
            raise

        return results


class K8sRuntime(LocalRuntime):
    """K8s runtime key is 'k8s', and execute tasks in kubernetes cluster."""


class KubernetesRuntime(LocalRuntime):
    """kubernetes runtime key is 'kubernetes', and execute tasks in kubernetes cluster."""


class SparkRuntime(RuntimeEngine):
    """Spark runtime key is 'spark', and execute tasks in spark cluster.

    Note: Spark runtime must in driver end.
    """

    def __init__(self, engine_options):
        super(SparkRuntime, self).__init__(engine_options)

    def _build_engine(self):
        from pyspark.sql import SparkSession

        conf = self.conf
        is_local = conf.get('in_local', True)
        logger.info('build runtime is_local:{}'.format(is_local))
        spark_builder = SparkSession.builder
        if is_local:
            if 'PYSPARK_PYTHON' not in os.environ:
                import sys
                os.environ['PYSPARK_PYTHON'] = sys.executable

            spark_builder = spark_builder.master('local[1]').config('spark.executor.instances',
                                                                    f'{self.conf.get("worker_num", 1)}')

        self.runtime = spark_builder.appName(conf.get('job_name', 'aworld_spark_job')).getOrCreate()

    def args_process(self, *args):
        re_args = []
        for arg in args:
            if arg:
                options = self.runtime.sparkContext.broadcast(arg)
                arg = options.value
            re_args.append(arg)
        return re_args

    async def execute(self, funcs: List[Callable[..., Any]], *args, **kwargs) -> Dict[str, Any]:
        re_args = self.args_process(*args)
        res_rdd = self.runtime.sparkContext.parallelize(funcs, len(funcs)).map(
            lambda func: RuntimeEngine.func_wrapper(func, *re_args, **kwargs))

        res_list = res_rdd.collect()
        results = {res.id: res for res in res_list}
        return results


class RayRuntime(RuntimeEngine):
    """Ray runtime key is 'ray', and execute tasks in ray cluster.

    Ray runtime in RuntimeEngine only execute function (stateless), can be used to custom
    resource allocation and communication etc. advanced features.
    """

    def __init__(self, engine_options):
        super(RayRuntime, self).__init__(engine_options)

    def _build_engine(self):
        import ray

        if not ray.is_initialized():
            ray.init()

        self.runtime = ray
        self.num_executors = self.conf.get('worker_num', 1)
        logger.info("ray init finished, executor number {}".format(str(self.num_executors)))

    async def execute(self, funcs: List[Callable[..., Any]], *args, **kwargs) -> Dict[str, Any]:
        @self.runtime.remote
        def fn_wrapper(fn, *args):
            if asyncio.iscoroutinefunction(fn):
                return sync_exec(fn, *args, **kwargs)
            else:
                real_args = [arg for arg in args if not isinstance(arg, MethodType)]
                return fn(*real_args, **kwargs)

        params = []
        for arg in args:
            params.append([arg] * len(funcs))

        ray_map = lambda func, fn: [func.remote(x, *y) for x, *y in zip(fn, *params)]
        res_list = self.runtime.get(ray_map(fn_wrapper, funcs))
        return {res.id: res for res in res_list}


RUNTIME: Dict[str, RuntimeEngine] = {}


def register(key, runtime_backend):
    if RUNTIME.get(key, None) is not None:
        logger.debug("{} runtime backend already exists, will reuse the client.".format(key))
        return

    RUNTIME[key] = runtime_backend
    logger.info("register {}:{} success".format(key, runtime_backend))
