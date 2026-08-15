

from aworld.core.memory import MemoryItem


def build_history_context(history_messages: list[MemoryItem]) -> str:
    """
    Build history context from history messages.
    """
    history_context = ""
    for message in history_messages:
        if message.role == "user":
            history_context += f"User: {message.content}\n"
        else:
            history_context += f"Agent: {message.content}\n"
    return history_context