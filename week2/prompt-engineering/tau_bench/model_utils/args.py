import argparse

from tau_bench.model_utils.model.model import Platform


def api_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str)
    parser.add_argument("--base-url", type=str)
    parser.add_argument("--platform", type=str, required=True, choices=[e.value for e in Platform])
    return parser
