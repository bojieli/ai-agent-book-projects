# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import argparse
import json
import os
from pathlib import Path

import pandas as pd


def load_gaia_dataset(path: str, split: str = "validation", total_num_dataset: int = 300):
    data_dir = Path(path) / split

    split_dataset = []
    rl_dataset = {
        "prompt": [],
        "data_source": [],
        "ability": [],
        "reward_model": [],
        "extra_info": [],
        "agent_name": [],
    }
    cnt = 0
    with open(data_dir / "metadata.jsonl", "r", encoding="utf-8") as metaf:
        lines = metaf.readlines()
        for line in lines:
            data = json.loads(line)
            if data["task_id"] == "0-0-0-0-0":
                continue
            if data["file_name"]:
                data["file_name"] = data_dir / data["file_name"]
            split_dataset.append(data)
            rl_dataset["prompt"].append(data["Question"])
            rl_dataset["extra_info"].append(
                {"task_id": data["task_id"], "split": split, "level": data["Level"], "answer": data["Final answer"]}
            )
            rl_dataset["agent_name"].append("gaia_agent")
            rl_dataset["data_source"].append("gaia")
            rl_dataset["ability"].append("agi")
            rl_dataset["reward_model"].append({"style": "GAIA", "ground_truth": data['Final answer']})

            cnt += 1
            if cnt >= total_num_dataset:
                break

    rl_dataset = pd.DataFrame(data=rl_dataset)
    return rl_dataset

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GAIA Dataset Generator")
    parser.add_argument("--train_size", type=int, default=300, help="Number of training samples")
    parser.add_argument("--test_size", type=int, default=100, help="Number of testing samples")
    parser.add_argument("--output_dir", default="gaia_data/", help="Directory to save the dataset")
    parser.add_argument("--dataset_path", default="./gaia_dataset", help="GAIA dataset path")
    args = parser.parse_args()

    gaia_dataset_path = args.dataset_path

    train_dataset = load_gaia_dataset(path=gaia_dataset_path, split="validation", total_num_dataset=args.train_size)
    test_dataset = load_gaia_dataset(path=gaia_dataset_path, split="test", total_num_dataset=args.test_size)

    # Make sure the dataset directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Save the datasets to parquet files
    train_dataset.to_parquet(os.path.join(args.output_dir, "train.parquet"))
    test_dataset.to_parquet(os.path.join(args.output_dir, "test.parquet"))
