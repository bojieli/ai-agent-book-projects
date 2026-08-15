# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
from asyncio import Queue, PriorityQueue, QueueEmpty
from inspect import isfunction
from typing import Callable, Any, Dict, List

from aworld.core.singleton import InheritanceSingleton

from aworld.core.common import Config
from aworld.core.event.base import Message, Messageable
from aworld.logs.util import logger


class Eventbus(Messageable, InheritanceSingleton):
    __metaclass__ = abc.ABCMeta

    def __init__(self, conf: Config = None, **kwargs):
        super().__init__(conf, **kwargs)
        # {task_id: {event_type: {topic: [handler1, handler2]}}}
        self._subscribers: Dict[str, Dict[str, Dict[str, List[Callable[..., Any]]]]] = {}

        # {task_id: {event_type, handler}}
        self._transformer: Dict[str, Dict[str, Callable[..., Any]]] = {}

    async def send(self, message: Message, **kwargs):
        return await self.publish(message, **kwargs)

    async def receive(self, message: Message, **kwargs):
        return await self.consume(message)

    async def publish(self, messages: Message, **kwargs):
        """Publish a message, equals `send`."""

    async def consume(self, message: Message, **kwargs):
        """Consume the message queue."""

    async def subscribe(self, event_type: str, topic: str, handler: Callable[..., Any], task_id: str, **kwargs):
        """Subscribe the handler to the event type and the topic.

        NOTE: The handler list is executed sequentially in the topic, the output
              of the previous one is the input of the next one.

        Args:
            event_type: Type of events, fixed ones(task, agent, tool, error).
            topic: Classify messages through the topic.
            handler: Function of handle the event type and topic message.
            kwargs:
                - transformer: Whether it is a transformer handler.
                - order: Handler order in the topic.
        """

    async def unsubscribe(self, event_type: str, topic: str, handler: Callable[..., Any], task_id: str, **kwargs):
        """Unsubscribe the handler to the event type and the topic.

        Args:
            event_type: Type of events, fixed ones(task, agent, tool, error).
            topic: Classify messages through the topic.
            handler: Function of handle the event type and topic message.
            kwargs:
                - transformer: Whether it is a transformer handler.
        """

    def get_handlers(self, task_id: str, event_type: str) -> Dict[str, List[Callable[..., Any]]]:
        return self._subscribers.get(task_id, {}).get(event_type, {})

    def get_topic_handlers(self, task_id: str, event_type: str, topic: str) -> List[Callable[..., Any]]:
        return self._subscribers.get(task_id, {}).get(event_type, {}).get(topic, [])

    def get_transform_handler(self, task_id: str, key: str) -> Callable[..., Any]:
        return self._transformer.get(task_id, {}).get(key, None)

    def close(self):
        pass


class InMemoryEventbus(Eventbus):
    def __init__(self, conf: Config = None, **kwargs):
        super().__init__(conf, **kwargs)

        # use asyncio Queue as default
        # use asyncio Queue as default, isolation based on session_id
        # self._message_queue: Queue = Queue()
        self._message_queue: Dict[str, Queue] = {}

    def wait_consume_size(self, id: str) -> int:
        return self._message_queue.get(id, Queue()).qsize()

    async def publish(self, message: Message, **kwargs):
        logger.info(f"publish taskid: {message.task_id}, message: {message}")
        queue = self._message_queue.get(message.task_id)
        if not queue:
            queue = PriorityQueue()
            self._message_queue[message.task_id] = queue
        logger.debug(f"publish message: {message.task_id}:  {message.session_id}, queue: {id(queue)}")
        await queue.put(message)

    async def consume(self, message: Message, **kwargs):
        return await self._message_queue.get(message.task_id, PriorityQueue()).get()

    async def consume_nowait(self, message: Message):
        return self._message_queue.get(message.task_id, PriorityQueue()).get_nowait()

    async def done(self, id: str):
        # Only operate on an existing queue; avoid creating a new temporary queue via dict.get default
        queue = self._message_queue.get(id)
        if not queue:
            return
        # Drain all remaining items and mark them done to balance unfinished_tasks
        while True:
            try:
                queue.get_nowait()
                queue.task_done()
            except QueueEmpty:
                break

    async def subscribe(self, task_id: str, event_type: str, topic: str, handler: Callable[..., Any], **kwargs):
        if kwargs.get("transformer"):
            # Initialize task_id dict if not exists
            if task_id not in self._transformer:
                self._transformer[task_id] = {}
                
            if event_type in self._transformer[task_id]:
                logger.warning(f"{event_type} transform already subscribe for task {task_id}.")
                return

            if isfunction(handler):
                self._transformer[task_id][event_type] = handler
            else:
                logger.warning(f"{event_type} {topic} subscribe fail, handler {handler} is not a function.")
            return

        order = kwargs.get('order', 99999)
        task_handlers = self._subscribers.get(task_id)
        if not task_handlers:
            task_handlers = {}
            self._subscribers[task_id] = task_handlers

        handlers = task_handlers.get(event_type)
        if not handlers:
            task_handlers[event_type] = {}
        topic_handlers = task_handlers[event_type].get(topic)
        if not topic_handlers:
            task_handlers[event_type][topic] = []

        if order >= len(self._subscribers[task_id][event_type][topic]):
            self._subscribers[task_id][event_type][topic].append(handler)
        else:
            self._subscribers[task_id][event_type][topic].insert(order, handler)
        logger.info(f"subscribe {event_type} {topic} {handler} success.")
        logger.info(f"subscribers {task_id}: {self._subscribers}")

    async def unsubscribe(self, task_id: str, event_type: str, topic: str, handler: Callable[..., Any], **kwargs):
        if kwargs.get("transformer"):
            if task_id not in self._transformer:
                logger.warning(f"{task_id} transform not subscribe.")
                return

            self._transformer[task_id].pop(event_type, None)
            return

        if task_id not in self._subscribers:
            logger.warning(f"{task_id} handler not register.")
            return

        if event_type not in self._subscribers[task_id]:
            logger.warning(f"{event_type} handler not register.")
            return

        handlers = self._subscribers[task_id][event_type]
        topic_handlers: List = handlers.get(topic, [])
        topic_handlers.remove(handler)
