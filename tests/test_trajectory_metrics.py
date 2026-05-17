import json
from pathlib import Path
from trajectory_metrics import compute_metrics

def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")

def test_counts_standard_roles(tmp_path: Path) -> None:
    path = tmp_path / "trajectory.json"

    write_json(
        path,
        {
            "trajectory_format": "mini-swe-agent-1.1",
            "messages": [
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "task"},
                {"role": "assistant", "content": "I will inspect the code."},
                {"role": "tool", "content": "file list"},
            ],
        },
    )

    metrics = compute_metrics(path)

    assert metrics.system_messages == 1
    assert metrics.user_messages == 1
    assert metrics.assistant_messages == 1
    assert metrics.tool_messages == 1
    assert metrics.total_messages == 4

def test_normalizes_user_message_with_returncode_to_tool(tmp_path: Path) -> None:
    path = tmp_path / "trajectory.json"

    write_json(
        path,
        {
            "messages": [
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "task"},
                {"role": "assistant", "content": "run ls"},
                {
                    "role": "user",
                    "content": "<returncode>0</returncode><output>main.py</output>",
                    "extra": {"returncode": 0},
                },
            ],
        },
    )

    metrics = compute_metrics(path, normalize_tool_observations=True)

    assert metrics.system_messages == 1
    assert metrics.user_messages == 1
    assert metrics.assistant_messages == 1
    assert metrics.tool_messages == 1
    assert metrics.total_messages == 4

def test_counts_failed_tool_observation(tmp_path: Path) -> None:
    path = tmp_path / "trajectory.json"

    write_json(
        path,
        {
            "messages": [
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "task"},
                {"role": "assistant", "content": "run tests"},
                {
                    "role": "tool",
                    "content": "pytest failed",
                    "extra": {"returncode": 1},
                },
            ],
        },
    )

    metrics = compute_metrics(path)

    assert metrics.failed_tool_observations == 1