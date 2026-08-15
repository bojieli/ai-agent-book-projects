from typing import TypeVar
from aworld.trace.base import Carrier
from aworld.logs.util import logger

T = TypeVar("T")


class ListTupleCarrier(Carrier):

    def __init__(self, headers: list[tuple[str, T]]):
        self.headers = headers

    def get(self, key: str) -> T:
        for header, value in self.headers:
            header_str = header.decode(
                'utf-8') if isinstance(header, bytes) else header
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            if header_str.lower() == key_str.lower():
                return value.decode('utf-8') if isinstance(value, bytes) else value
        return None

    def set(self, key: str, value: T) -> None:
        for i, (header, _) in enumerate(self.headers):
            header_str = header.decode(
                'utf-8') if isinstance(header, bytes) else header
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            if header_str.lower() == key_str.lower():
                self.headers[i] = (header, value)
                return
        self.headers.append((key, value))


class DictCarrier(Carrier):
    def __init__(self, headers: dict[str, T]):
        self.headers = headers

    def get(self, key: str) -> T:
        return self.headers.get(key)

    def set(self, key: str, value: T) -> None:
        logger.info(f"set header {key}={value}")
        self.headers[key] = value
