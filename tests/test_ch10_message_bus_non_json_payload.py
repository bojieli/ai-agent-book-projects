import sys
import os

sys.path.insert(0, os.path.abspath("chapter10/parallel-web-research"))

from message_bus import Envelope, MessageBus


def test_envelope_short_handles_non_json_payload():
    """Contract: Envelope.short does not raise TypeError when payload contains non-JSON serializable objects."""
    class CustomObject:
        def __str__(self):
            return "<CustomObject>"

    payload = {
        "tags": {"python", "asyncio"},
        "object": CustomObject(),
        "bytes": b"raw_data",
    }

    env = Envelope(
        sender_id="agent_1",
        target="agent_2",
        type="data_sync",
        payload=payload,
    )

    short_str = env.short()
    assert isinstance(short_str, str)
    assert "agent_1" in short_str
    assert "data_sync" in short_str
    assert "agent_2" in short_str


def test_message_bus_publish_verbose_non_json_payload(capsys):
    """Contract: MessageBus.publish in verbose mode logs without crashing on non-JSON payload."""
    bus = MessageBus(verbose=True)
    env = Envelope(
        sender_id="sender",
        target="*",
        type="broadcast_event",
        payload={"set_val": {1, 2, 3}},
    )

    import asyncio
    asyncio.run(bus.publish(env))

    captured = capsys.readouterr()
    assert "BUS" in captured.out
    assert "broadcast_event" in captured.out
