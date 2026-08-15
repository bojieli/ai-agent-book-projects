from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, create_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime
from typing import Optional
from base import AworldTask, AworldTaskResult

Base = declarative_base()


class AworldTaskModel(Base):
    __tablename__ = 'aworld_tasks'

    task_id = Column(String, primary_key=True)
    agent_id = Column(String)
    agent_input = Column(Text)
    session_id = Column(String)
    user_id = Column(String)
    llm_provider = Column(String)
    llm_model_name = Column(String)
    llm_api_key = Column(String)
    llm_base_url = Column(String)
    llm_custom_input = Column(Text)
    task_system_prompt = Column(Text)
    mcp_servers = Column(JSON)
    node_id = Column(String)
    client_id = Column(String)
    status = Column(String, default='INIT')
    history_messages = Column(Integer, default=100)
    max_steps = Column(Integer, default=100)
    max_retries = Column(Integer, default=5)
    ext_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AworldTaskResultModel(Base):
    __tablename__ = 'aworld_tasks_results'

    task_result_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String)
    server_host = Column(String)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


def orm_to_pydantic_task(orm_obj: AworldTaskModel) -> AworldTask:
    return AworldTask(**{c.name: getattr(orm_obj, c.name) for c in orm_obj.__table__.columns})


def pydantic_to_orm_task(pydantic_obj: AworldTask) -> AworldTaskModel:
    return AworldTaskModel(**pydantic_obj.model_dump())


def orm_to_pydantic_result(orm_obj: AworldTaskResultModel) -> AworldTaskResult:
    return AworldTaskResult(
        server_host=orm_obj.server_host,
        data=orm_obj.data
    )


def pydantic_to_orm_result(pydantic_obj: AworldTaskResult) -> AworldTaskResultModel:
    return AworldTaskResultModel(
        task_id=pydantic_obj.task.task_id if pydantic_obj.task else None,
        server_host=pydantic_obj.server_host,
        data=pydantic_obj.data
    )
