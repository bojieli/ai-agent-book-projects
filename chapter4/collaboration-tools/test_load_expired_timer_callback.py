import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytest
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

import timer_tools
from config import config


@pytest.mark.asyncio
async def test_load_timers_expired_active_timer_triggers_callback():
    storage = Path(config.timer.storage_path).expanduser()
    storage.parent.mkdir(parents=True, exist_ok=True)

    past_expiry = (datetime.now() - timedelta(seconds=10)).isoformat()
    timer_id = "test-expired-timer-restore"
    callback_fired = False

    async def mock_callback(timer_data):
        nonlocal callback_fired
        callback_fired = True

    timer_tools._active_timers.clear()
    timer_tools._trigger_timer_callback = mock_callback

    timer_data = {
        "timer_id": timer_id,
        "name": "Expired Active Timer",
        "duration_seconds": 10,
        "start_time": (datetime.now() - timedelta(seconds=20)).isoformat(),
        "expiry_time": past_expiry,
        "callback_message": "Timer expired message!",
        "status": "active",
        "created_at": (datetime.now() - timedelta(seconds=20)).isoformat()
    }

    with open(storage, "w") as f:
        json.dump({timer_id: timer_data}, f)

    await timer_tools._load_timers()

    loaded = timer_tools._active_timers.get(timer_id)
    assert loaded is not None
    assert loaded["status"] == "expired"
    assert loaded.get("completed_at") is not None
    assert callback_fired is True

    with open(storage, "r") as f:
        on_disk = json.load(f)
    assert on_disk[timer_id]["status"] == "expired"


if __name__ == "__main__":
    asyncio.run(test_load_timers_expired_active_timer_triggers_callback())
