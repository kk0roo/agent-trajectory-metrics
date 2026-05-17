import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

INPUT_PATH = Path("results/top5_message_metrics.csv")

def infer_model_name(file_path: str) -> str:
    """Extract the model name from paths like data/<model>/trajectories/<file>.json."""
    parts = file_path.replace("\\", "/").split("/")

    if "data" in parts:
        data_index = parts.index("data")
        if data_index + 1 < len(parts):
            return parts[data_index + 1]

    return "unknown"


def to_int(value: str) -> int:
    return int(float(value))


def main() -> None:
    if not INPUT_PATH.exists():
        raise SystemExit("Missing results/top5_message_metrics.csv")

    grouped = defaultdict(list)

    with INPUT_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            model = infer_model_name(row["file"])
            grouped[model].append(row)

    print(
        "model,trajectories,avg_total_messages,avg_system_messages,"
        "avg_user_messages,avg_assistant_messages,avg_tool_messages,"
        "min_total_messages,max_total_messages"
    )

    for model, rows in sorted(grouped.items()):
        total = [to_int(row["total_messages"]) for row in rows]
        system = [to_int(row["system_messages"]) for row in rows]
        user = [to_int(row["user_messages"]) for row in rows]
        assistant = [to_int(row["assistant_messages"]) for row in rows]
        tool = [to_int(row["tool_messages"]) for row in rows]

        print(
            f"{model},"
            f"{len(rows)},"
            f"{mean(total):.2f},"
            f"{mean(system):.2f},"
            f"{mean(user):.2f},"
            f"{mean(assistant):.2f},"
            f"{mean(tool):.2f},"
            f"{min(total)},"
            f"{max(total)}"
        )


if __name__ == "__main__":
    main()