# Replay Buffer

A multi-process capable replay buffer system for storing and sampling experience data.

## Features

- **Multi-process Support**: Safe concurrent access using shared memory and locks
- **Flexible Querying**: Powerful query builder for filtering stored data
- **Task-based Organization**: Data organized by task_id and agent_id
- **Capacity Management**: FIFO eviction when reaching max capacity
- **Custom Sampling**: Implement custom sampling logic through Sampler interface
- **Data Conversion**: Custom data conversion through Converter interface

## Basic Usage

### Writing Data

```python
from aworld.replay_buffer import ReplayBuffer, DataRow, ExpMeta, Experience
from aworld.core.common import ActionModel, Observation

# Create a data row
data = DataRow(
    exp_meta=ExpMeta(
        task_id="task_1",
        task_name="my_task",
        agent_id="agent_1",
        step=1,
        execute_time=time.time()
    ),
    exp_data=Experience(
        state=Observation(),
        action=ActionModel()
    )
)

# Store data
replay_buffer.store(data)
```

### Reading Data

```python
from aworld.replay_buffer.query_filter import QueryBuilder

# Basic example
replay_buffer = ReplayBuffer()
query_condition = QueryBuilder().eq("exp_meta.task_name", "test_task").build()
data = replay_buffer.sample(sampler=RandomTaskSample(),
                            query_condition=query_condition,
                            converter=DefaultConverter(),
                            batch_size=1000)

# Query Task by task_id
query = QueryBuilder().eq("exp_meta.task_id", "task_1").build()
data = replay_buffer.sample_task(query_condition=query, batch_size=10)

# Query Task by agent_id 
query = QueryBuilder().eq("exp_meta.agent_id", "agent_1").build()
data = replay_buffer.sample_task(query_condition=query, batch_size=5)
```
## Multi-processing Example

```python
import multiprocessing
from aworld.replay_buffer.storage.multi_proc_mem import MultiProcMemoryStorage

manager = multiprocessing.Manager()
replay_buffer = ReplayBuffer(
    storage=MultiProcMemoryStorage(
        data_dict=manager.dict(),
        fifo_queue=manager.list(),
        lock=manager.Lock(),
        max_capacity=10000
    )
)

# Start writer processes
processes = [
    multiprocessing.Process(target=write_processing, args=(replay_buffer, f"task_{i}"))
    for i in range(4)
]
```
## Query Builder Examples

### Simple Equality
```python
QueryBuilder().eq("exp_meta.task_id", "123").build()
```

### Complex Conditions
```python
QueryBuilder()
    .eq("exp_meta.task_id", "123")
    .and_()
    .eq("exp_meta.agent_id", "456")
    .build()
```
### Nested Conditions
```python
QueryBuilder()
    .eq("exp_meta.task_id", "123")
    .and_()
    .nested(
        QueryBuilder()
            .eq("exp_meta.agent_id", "111")
            .or_()
            .eq("exp_meta.agent_id", "222")
    )
    .build()
```
