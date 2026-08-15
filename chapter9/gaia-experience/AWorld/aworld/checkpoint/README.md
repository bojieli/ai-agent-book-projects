# Checkpoint Module

## Overview
The Checkpoint module provides a robust and extensible framework for managing state snapshots (checkpoints) in Python applications. It is designed for scenarios where you need to persist, restore, and version the state of a process, session, or task.

```mermaid
sequenceDiagram
    participant Application
    participant CheckpointRepository
    participant BackendStorage

    Note over Application,BackendStorage: Create and store a checkpoint
    %% Create and store a checkpoint
    Application->>CheckpointRepository: create checkpoint
    CheckpointRepository->>BackendStorage: put(checkpoint)
    BackendStorage-->>CheckpointRepository: success
    CheckpointRepository-->>Application: ack
    
    Note over Application,BackendStorage: Retrieve the latest checkpoint by session

    %% Retrieve the latest checkpoint by session
    Application->>CheckpointRepository: get checkpoint by session_id
    CheckpointRepository->>BackendStorage: get_by_session(session_id)
    BackendStorage-->>CheckpointRepository: Checkpoint
    CheckpointRepository-->>Application: Checkpoint

```

## Key Features

- **Structured Data Model**: Uses Pydantic's `BaseModel` for strong typing and validation of checkpoint data and metadata.
- **Versioning Support**: Built-in version management utilities for checkpoint evolution and comparison.
- **Extensible Repository Pattern**: Abstract base class (`BaseCheckpointRepository`) defines a standard interface for checkpoint storage, supporting both synchronous and asynchronous operations.
- **In-Memory Implementation**: Includes a simple, ready-to-use in-memory repository for development and testing.
- **Utility Functions**: Helper methods for creating, copying, and managing checkpoints.

## Data Structures

```mermaid
classDiagram
    class Application {
        +CheckpointRepository repo
        +create_checkpoint()
        +get_checkpoint_by_session()
    }
    class CheckpointRepository {
        +put(checkpoint)
        +get_by_session(session_id)
        +delete_by_session(session_id)
        -BackendStorage backend
    }
    class BackendStorage {
        +put(checkpoint)
        +get_by_session(session_id)
        +delete_by_session(session_id)
    }
    Application --> CheckpointRepository : uses
    CheckpointRepository --> BackendStorage : delegates
    class Checkpoint {
        +id: str
        +ts: str
        +metadata: CheckpointMetadata
        +values: dict
        +version: int
        +parent_id: str
        +namespace: str
    }
    class CheckpointMetadata {
        +session_id: str
        +task_id: str
    }
    Checkpoint o-- CheckpointMetadata
    CheckpointRepository o-- Checkpoint
    BackendStorage o-- Checkpoint
```


## Usage Example

```python
from aworld.checkpoint import (
    Checkpoint, CheckpointMetadata, empty_checkpoint, create_checkpoint, InMemoryCheckpointRepository
)

# Create a new checkpoint
metadata = CheckpointMetadata(session_id="session-123", task_id="task-456")
values = {"step": 1, "score": 100}
checkpoint = create_checkpoint(values=values, metadata=metadata)

# Store and retrieve using the in-memory repository
repo = InMemoryCheckpointRepository()
repo.put(checkpoint)
restored = repo.get(checkpoint.id)
```

## Extensibility
- Implement custom repositories by inheriting from `BaseCheckpointRepository` (e.g., for database, file, or cloud storage).
- Extend versioning logic via the `VersionUtils` class.
