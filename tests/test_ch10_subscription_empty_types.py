import pytest
"""Regression test: Subscription with empty types list [] must filter out all message types."""
import sys
from pathlib import Path

ch10_pwr = Path(__file__).resolve().parent.parent / "chapter10" / "parallel-web-research"
if str(ch10_pwr) not in sys.path:
    sys.path.insert(0, str(ch10_pwr))

from message_bus import Subscription, Envelope, MessageBus, BROADCAST  # noqa: E402


def test_subscription_type_filtering():
    # None = wildcard (accept all)
    sub_wildcard = Subscription("owner1", None)
    assert sub_wildcard.types is None
    assert sub_wildcard.accepts(Envelope(sender_id="sender", target=BROADCAST, type="event_a", payload={}))
    assert sub_wildcard.accepts(Envelope(sender_id="sender", target=BROADCAST, type="event_b", payload={}))

    # Empty list [] = accept no types
    sub_empty = Subscription("owner2", [])
    assert sub_empty.types == set()
    assert not sub_empty.accepts(Envelope(sender_id="sender", target=BROADCAST, type="event_a", payload={}))
    assert not sub_empty.accepts(Envelope(sender_id="sender", target=BROADCAST, type="event_b", payload={}))

    # Specific list = accept only listed types
    sub_specific = Subscription("owner3", ["event_a"])
    assert sub_specific.types == {"event_a"}
    assert sub_specific.accepts(Envelope(sender_id="sender", target=BROADCAST, type="event_a", payload={}))
    assert not sub_specific.accepts(Envelope(sender_id="sender", target=BROADCAST, type="event_b", payload={}))


@pytest.mark.asyncio
async def test_message_bus_empty_types_subscription():
    bus = MessageBus(verbose=False)
    sub_none = bus.subscribe("agent_all", types=None)
    sub_empty = bus.subscribe("agent_none", types=[])

    env = Envelope(sender_id="main", target=BROADCAST, type="test_event", payload={"data": 123})
    await bus.publish(env)

    env_all = await sub_none.get()
    assert env_all.type == "test_event"
    assert env_all.payload == {"data": 123}

    assert sub_empty.inbox.empty()
