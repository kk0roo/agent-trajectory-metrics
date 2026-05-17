from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


KNOWN_ROLES = {"system", "user", "assistant", "tool"}


@dataclass
class TrajectoryMetrics:
    file: str
    trajectory_format: str | None

    system_messages: int
    user_messages: int
    assistant_messages: int
    tool_messages: int
    other_messages: int
    total_messages: int

    exit_status: str | None
    api_calls: int | None
    instance_cost: float | None
    failed_tool_observations: int


class TrajectoryError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise TrajectoryError(f"{path}: invalid JSON file: {exc}") from exc
    except OSError as exc:
        raise TrajectoryError(f"{path}: could not read file: {exc}") from exc


def extract_messages(data: Any, path: Path) -> list[dict[str, Any]]:
    """Extracts and validates the message list from one trajectory file."""
    
    if isinstance(data, dict) and isinstance(data.get("messages"), list):
        messages = data["messages"]
    elif isinstance(data, list):
        messages = data
    else:
        raise TrajectoryError(
            f"{path}: expected JSON object with a 'messages' list"
        )

    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise TrajectoryError(
                f"{path}: message at index {index} is not a JSON object"
            )

    return messages


def get_extra(message: dict[str, Any]) -> dict[str, Any]:
    extra = message.get("extra")
    if isinstance(extra, dict):
        return extra
    return {}


def is_tool_observation(message: dict[str, Any]) -> bool:
    """Return True if the message looks like a tool output."""

    if message.get("role") == "tool":
        return True

    tool_call_id = message.get("tool_call_id")
    if tool_call_id not in (None, ""):
        return True

    extra = get_extra(message)
    if "returncode" in extra:
        return True

    content = message.get("content")
    if isinstance(content, str):
        if "<returncode>" in content and "</returncode>" in content:
            return True

    return False


def classify_role(message: dict[str, Any], normalize_tool_observations: bool) -> str:
    """Classify one message by role, optionally normalizing shell observations as tool messages."""
    
    if normalize_tool_observations and is_tool_observation(message):
        return "tool"

    role = message.get("role")
    if isinstance(role, str) and role in KNOWN_ROLES:
        return role

    return "other"


def count_failed_tool_observations(messages: list[dict[str, Any]]) -> int:
    """Count tool observations with a non-zero return code."""
    
    failed = 0

    for message in messages:
        if not is_tool_observation(message):
            continue

        extra = get_extra(message)
        returncode = extra.get("returncode")

        if isinstance(returncode, int) and returncode != 0:
            failed += 1

    return failed


def compute_metrics(
    path: Path,
    normalize_tool_observations: bool = True,
) -> TrajectoryMetrics:
    """Compute all message-count metrics for a single trajectory JSON file."""
    
    data = load_json(path)
    messages = extract_messages(data, path)

    role_counts = Counter(
        classify_role(message, normalize_tool_observations)
        for message in messages
    )

    info = data.get("info", {}) if isinstance(data, dict) else {}
    if not isinstance(info, dict):
        info = {}

    model_stats = info.get("model_stats", {})
    if not isinstance(model_stats, dict):
        model_stats = {}

    api_calls = model_stats.get("api_calls")
    if not isinstance(api_calls, int):
        api_calls = None

    instance_cost = model_stats.get("instance_cost")
    if isinstance(instance_cost, (int, float)):
        instance_cost = float(instance_cost)
    else:
        instance_cost = None

    exit_status = info.get("exit_status")
    if exit_status is not None:
        exit_status = str(exit_status)

    trajectory_format = None
    if isinstance(data, dict):
        trajectory_format_raw = data.get("trajectory_format")
        if trajectory_format_raw is not None:
            trajectory_format = str(trajectory_format_raw)

    return TrajectoryMetrics(
        file=str(path),
        trajectory_format=trajectory_format,
        system_messages=role_counts["system"],
        user_messages=role_counts["user"],
        assistant_messages=role_counts["assistant"],
        tool_messages=role_counts["tool"],
        other_messages=role_counts["other"],
        total_messages=len(messages),
        exit_status=exit_status,
        api_calls=api_calls,
        instance_cost=instance_cost,
        failed_tool_observations=count_failed_tool_observations(messages),
    )


def find_json_files(input_path: Path, recursive: bool) -> list[Path]:
    """Return JSON files from a single file path or from a directory."""
    
    if input_path.is_file():
        return [input_path]

    if not input_path.is_dir():
        raise TrajectoryError(f"{input_path}: path does not exist")

    if recursive:
        files = list(input_path.rglob("*.json"))
    else:
        files = list(input_path.glob("*.json"))

    return sorted(files)


def print_text(metrics: list[TrajectoryMetrics]) -> None:
    for index, metric in enumerate(metrics):
        if len(metrics) > 1:
            if index > 0:
                print()
            print(f"File: {metric.file}")

        print(f"System messages:    {metric.system_messages}")
        print(f"User messages:      {metric.user_messages}")
        print(f"Assistant messages: {metric.assistant_messages}")
        print(f"Tool messages:      {metric.tool_messages}")
        print("=======================")
        print(f"Total messages:     {metric.total_messages}")

        if metric.other_messages:
            print(f"Other messages:     {metric.other_messages}")

        optional_lines = []

        if metric.exit_status is not None:
            optional_lines.append(f"Exit status:        {metric.exit_status}")

        if metric.api_calls is not None:
            optional_lines.append(f"API calls:          {metric.api_calls}")

        if metric.instance_cost is not None:
            optional_lines.append(f"Instance cost:      {metric.instance_cost:.6f}")

        if metric.failed_tool_observations:
            optional_lines.append(
                f"Failed tool obs.:   {metric.failed_tool_observations}"
            )

        if optional_lines:
            print("-----------------------")
            for line in optional_lines:
                print(line)


def print_csv(metrics: list[TrajectoryMetrics]) -> None:
    if not metrics:
        return

    writer = csv.DictWriter(
    sys.stdout,
    fieldnames=list(asdict(metrics[0]).keys()),
    lineterminator="\n",
)
    writer.writeheader()

    for metric in metrics:
        writer.writerow(asdict(metric))


def print_json(metrics: list[TrajectoryMetrics]) -> None:
    json.dump([asdict(metric) for metric in metrics], sys.stdout, indent=2)
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute message-count metrics for mini-SWE-agent trajectory JSON files"
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Path to a trajectory JSON file or a directory with trajectory JSON files",
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search directories recursively",
    )

    parser.add_argument(
        "--format",
        choices=["text", "csv", "json"],
        default="text",
        help="Output format.",
    )

    parser.add_argument(
        "--raw-roles",
        action="store_true",
        help=(
            "Count roles exactly as stored in JSON. By default, shell observations "
            "encoded as user messages are counted as tool messages"
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        files = find_json_files(args.input, args.recursive)

        if not files:
            raise TrajectoryError(f"{args.input}: no JSON files found")

        metrics = [compute_metrics(path, normalize_tool_observations=not args.raw_roles) for path in files]

        if args.format == "text":
            print_text(metrics)
        elif args.format == "csv":
            print_csv(metrics)
        elif args.format == "json":
            print_json(metrics)
        else:
            raise AssertionError("unreachable output format")

        return 0

    except TrajectoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())