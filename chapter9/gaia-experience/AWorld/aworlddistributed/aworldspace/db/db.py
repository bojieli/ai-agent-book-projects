from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from base import AworldTask, AworldTaskResult
from aworldspace.db.models import (
    Base, AworldTaskModel, AworldTaskResultModel,
    orm_to_pydantic_task, pydantic_to_orm_task,
    orm_to_pydantic_result, pydantic_to_orm_result
)


class AworldTaskDB(ABC):

    @abstractmethod
    async def query_task_by_id(self, task_id: str) -> AworldTask:
        pass

    @abstractmethod
    async def query_latest_task_result_by_id(self, task_id: str) -> Optional[AworldTaskResult]:
        pass

    @abstractmethod
    async def insert_task(self, task: AworldTask):
        pass

    @abstractmethod
    async def query_tasks_by_status(self, status: str, nums: int) -> list[AworldTask]:
        pass

    @abstractmethod
    async def update_task(self, task: AworldTask):
        pass

    @abstractmethod
    async def page_query_tasks(self, filter: dict, page_size: int, page_num: int) -> dict:
        pass

    @abstractmethod
    async def save_task_result(self, result: AworldTaskResult):
        pass


class SqliteTaskDB(AworldTaskDB):
    def __init__(self, db_path: str):
        self.engine = create_engine(db_path, echo=False, future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    async def query_task_by_id(self, task_id: str) -> Optional[AworldTask]:
        with self.Session() as session:
            orm_task = session.query(AworldTaskModel).filter_by(task_id=task_id).first()
            return orm_to_pydantic_task(orm_task) if orm_task else None

    async def query_latest_task_result_by_id(self, task_id: str) -> Optional[AworldTaskResult]:
        with self.Session() as session:
            orm_result = (
                session.query(AworldTaskResultModel)
                .filter_by(task_id=task_id)
                .order_by(AworldTaskResultModel.created_at.desc())
                .first()
            )
            return orm_to_pydantic_result(orm_result) if orm_result else None

    async def insert_task(self, task: AworldTask):
        with self.Session() as session:
            orm_task = pydantic_to_orm_task(task)
            session.add(orm_task)
            session.commit()

    async def query_tasks_by_status(self, status: str, nums: int) -> list[AworldTask]:
        with self.Session() as session:
            orm_tasks = (
                session.query(AworldTaskModel)
                .filter_by(status=status)
                .limit(nums)
                .all()
            )
            return [orm_to_pydantic_task(t) for t in orm_tasks]

    async def update_task(self, task: AworldTask):
        with self.Session() as session:
            orm_task = session.query(AworldTaskModel).filter_by(task_id=task.task_id).first()
            if orm_task:
                for k, v in task.model_dump().items():
                    setattr(orm_task, k, v)
                orm_task.updated_at = datetime.utcnow()
                session.commit()

    async def save_task_result(self, result: AworldTaskResult):
        with self.Session() as session:
            orm_task = pydantic_to_orm_result(result)
            session.add(orm_task)
            session.commit()

    async def page_query_tasks(self, filter: dict, page_size: int, page_num: int) -> dict:
        with self.Session() as session:
            query = session.query(AworldTaskModel)
            
            # Handle special filters for time ranges
            start_time = filter.pop('start_time', None)
            end_time = filter.pop('end_time', None)
            
            # Apply regular filters
            for k, v in filter.items():
                if hasattr(AworldTaskModel, k):
                    query = query.filter(getattr(AworldTaskModel, k) == v)
            
            # Apply time range filters
            if start_time:
                query = query.filter(AworldTaskModel.created_at >= start_time)
            if end_time:
                query = query.filter(AworldTaskModel.created_at <= end_time)
            
            total = query.count()
            orm_tasks = query.offset((page_num - 1) * page_size).limit(page_size).all()
            items = [orm_to_pydantic_task(t) for t in orm_tasks]
            return {
                "total": total,
                "page_num": page_num,
                "page_size": page_size,
                "items": items
            }


class PostgresTaskDB(AworldTaskDB):
    def __init__(self, db_url: str):
        # db_url example: 'postgresql+psycopg2://user:password@host:port/dbname'
        self.engine = create_engine(db_url, echo=False, future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    async def query_task_by_id(self, task_id: str) -> Optional[AworldTask]:
        with self.Session() as session:
            orm_task = session.query(AworldTaskModel).filter_by(task_id=task_id).first()
            return orm_to_pydantic_task(orm_task) if orm_task else None

    async def query_latest_task_result_by_id(self, task_id: str) -> Optional[AworldTaskResult]:
        with self.Session() as session:
            orm_result = (
                session.query(AworldTaskResultModel)
                .filter_by(task_id=task_id)
                .order_by(AworldTaskResultModel.created_at.desc())
                .first()
            )
            return orm_to_pydantic_result(orm_result) if orm_result else None

    async def insert_task(self, task: AworldTask):
        with self.Session() as session:
            orm_task = pydantic_to_orm_task(task)
            session.add(orm_task)
            session.commit()

    async def query_tasks_by_status(self, status: str, nums: int) -> list[AworldTask]:
        with self.Session() as session:
            orm_tasks = (
                session.query(AworldTaskModel)
                .filter_by(status=status)
                .limit(nums)
                .all()
            )
            return [orm_to_pydantic_task(t) for t in orm_tasks]

    async def update_task(self, task: AworldTask):
        with self.Session() as session:
            orm_task = session.query(AworldTaskModel).filter_by(task_id=task.task_id).first()
            if orm_task:
                for k, v in task.model_dump().items():
                    setattr(orm_task, k, v)
                orm_task.updated_at = datetime.utcnow()
                session.commit()

    async def save_task_result(self, result: AworldTaskResult):
        with self.Session() as session:
            orm_task = pydantic_to_orm_result(result)
            session.add(orm_task)
            session.commit()

    async def page_query_tasks(self, filter: dict, page_size: int, page_num: int) -> dict:
        with self.Session() as session:
            query = session.query(AworldTaskModel)
            
            # Handle special filters for time ranges
            start_time = filter.pop('start_time', None)
            end_time = filter.pop('end_time', None)
            
            # Apply regular filters
            for k, v in filter.items():
                if hasattr(AworldTaskModel, k):
                    query = query.filter(getattr(AworldTaskModel, k) == v)
            
            # Apply time range filters
            if start_time:
                query = query.filter(AworldTaskModel.created_at >= start_time)
            if end_time:
                query = query.filter(AworldTaskModel.created_at <= end_time)
            
            total = query.count()
            orm_tasks = query.offset((page_num - 1) * page_size).limit(page_size).all()
            items = [orm_to_pydantic_task(t) for t in orm_tasks]
            return {
                "total": total,
                "page_num": page_num,
                "page_size": page_size,
                "items": items
            }

