"""
Helper script used to export full transcript JSON files from Docent.

This script is not required for running the metric tool itself. It is included
to make the data collection process reproducible for the analysis of the top
five mini-SWE-agent-v2 models.
"""

import json
import os
from pathlib import Path
from typing import Any

from docent import Docent


COLLECTIONS_PATH = Path("collection_ids.json")
ENV_PATH = Path("docent.env")
DATA_DIR = Path("data")


QUERY = """
SELECT
  t.id AS transcript_id,
  t.name AS transcript_name,
  t.messages,
  t.metadata_json AS transcript_metadata,
  ar.id AS agent_run_id,
  ar.name AS agent_run_name,
  ar.metadata_json AS agent_run_metadata
FROM transcripts t
JOIN agent_runs ar ON ar.id = t.agent_run_id
"""


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def parse_jsonish(value: Any) -> Any:
    """Parse fields that may be returned either as JSON strings or native objects."""
    
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    return value


def safe_name(value: Any) -> str:
    """Convert an ID or name into a filesystem-safe file name."""
    
    text = str(value)
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in text)


def main() -> None:
    load_env_file(ENV_PATH)

    api_key = os.environ.get("DOCENT_API_KEY")
    if not api_key:
        raise SystemExit(
            "DOCENT_API_KEY is missing"
        )

    collections = json.loads(COLLECTIONS_PATH.read_text(encoding="utf-8"))

    client = Docent(api_key=api_key)

    for model_name, collection_id in collections.items():
        print(f"Downloading transcripts for {model_name}...")

        result = client.execute_dql(collection_id, QUERY)
        rows = client.dql_result_to_dicts(result)

        out_dir = DATA_DIR / model_name / "trajectories"
        out_dir.mkdir(parents=True, exist_ok=True)

        saved = 0

        for row in rows:
            transcript_id = row.get("transcript_id")
            agent_run_id = row.get("agent_run_id")

            messages = parse_jsonish(row.get("messages"))
            transcript_metadata = parse_jsonish(row.get("transcript_metadata"))
            agent_run_metadata = parse_jsonish(row.get("agent_run_metadata"))

            if not isinstance(messages, list):
                print(
                    f"Skipping transcript {transcript_id}: messages field is not a list"
                )
                continue

            trajectory = {
                "trajectory_format": "docent-transcript-export",
                "info": {
                    "model_name": model_name,
                    "collection_id": collection_id,
                    "transcript_id": transcript_id,
                    "transcript_name": row.get("transcript_name"),
                    "agent_run_id": agent_run_id,
                    "agent_run_name": row.get("agent_run_name"),
                    "transcript_metadata": transcript_metadata,
                    "agent_run_metadata": agent_run_metadata,
                },
                "messages": messages,
            }

            filename = safe_name(agent_run_id or transcript_id or saved)
            out_path = out_dir / f"{filename}.json"

            out_path.write_text(
                json.dumps(trajectory, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )

            saved += 1

        print(f"Saved {saved} trajectories to {out_dir}")


if __name__ == "__main__":
    main()