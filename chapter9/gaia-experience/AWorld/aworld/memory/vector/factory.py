from typing import Optional

from pydantic import BaseModel

from aworld.core.memory import VectorDBConfig
from aworld.memory.vector.dbs.base import VectorDB





class VectorDBFactory:

    @staticmethod
    def get_vector_db(vector_db_config: VectorDBConfig) -> Optional[VectorDB]:
        if not vector_db_config:
            return None
        if vector_db_config.provider == "chroma":
            from aworld.memory.vector.dbs.chroma import ChromaVectorDB
            return ChromaVectorDB(vector_db_config.config)
        else:
            raise ValueError(f"Vector database {vector_db_config.provider} is not supported")