from abc import ABC


class SandboxApiBase(ABC):

    @staticmethod
    def _get_sandbox_id(sandbox_id: str) -> str:
        return f"{sandbox_id}"