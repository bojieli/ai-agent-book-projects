#!/usr/bin/env python3
"""Run one pinned AndroidWorld task with the upstream HumanAgent and evaluator."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


def load_uiautomator_env(args):
    from android_env import loader
    from android_env.components import config_classes
    from android_world.env import android_world_controller
    from android_world.env import env_launcher
    from android_world.env import interface

    config = config_classes.AndroidEnvConfig(
        task=config_classes.FilesystemTaskConfig(
            path=android_world_controller._write_default_task_proto()
        ),
        simulator=config_classes.EmulatorConfig(
            emulator_launcher=config_classes.EmulatorLauncherConfig(
                emulator_console_port=args.console_port,
                adb_port=args.console_port + 1,
                grpc_port=args.grpc_port,
            ),
            adb_controller=config_classes.AdbControllerConfig(adb_path=args.adb_path),
        ),
    )
    base_env = loader.load(config)
    controller = android_world_controller.AndroidWorldController(
        base_env,
        a11y_method=android_world_controller.A11yMethod.UIAUTOMATOR,
        install_a11y_forwarding_app=False,
    )
    env = interface.AsyncAndroidEnv(controller)
    env_launcher.setup_env(env, emulator_setup=False, freeze_datetime=False)
    return env


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--tier", choices=("easy", "medium", "hard"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--adb-path", default="/opt/android/platform-tools/adb")
    parser.add_argument("--console-port", type=int, default=5554)
    parser.add_argument("--grpc-port", type=int, default=8554)
    args = parser.parse_args()

    sys.path.insert(0, str(args.checkout))
    from android_world import registry
    from android_world import suite_utils
    from android_world.agents import human_agent

    env = load_uiautomator_env(args)
    task_registry = registry.TaskRegistry()
    suite = suite_utils.create_suite(
        task_registry.get_registry(task_registry.ANDROID_WORLD_FAMILY),
        n_task_combinations=1,
        seed=args.seed,
        tasks=[args.task],
        use_identical_params=True,
    )
    suite.suite_family = task_registry.ANDROID_WORLD_FAMILY
    agent = human_agent.HumanAgent(env)
    agent.name = "human_agent_codex"
    started = datetime.now(timezone.utc)
    try:
        episodes = suite_utils.run(suite, agent)
    finally:
        env.close()
    finished = datetime.now(timezone.utc)

    result = {
        "benchmark": "AndroidWorld",
        "operator": "Codex acting as the human operator",
        "task_id": args.task,
        "tier": args.tier,
        "seed": args.seed,
        "source_commit": "0e95d641e244504c22087cc29b013f3b2428a261",
        "observation_compatibility_path": "upstream UIAUTOMATOR controller; task and evaluator unchanged",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": finished.isoformat(),
        "episodes": episodes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps(result, indent=2, default=str))
    return 0 if episodes and episodes[0].get("is_successful") == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
