# Agent Trajectory Metrics

This repository contains a small command-line tool for computing message-level metrics from mini-SWE-agent trajectory JSON files.

The goal of the project is to move beyond a simple resolved/not-resolved score and inspect the structure of an agent's execution trajectory. The tool counts how many messages of each role appear in a trajectory: `system`, `user`, `assistant`, and `tool`.

## Repository structure

```text
agent-trajectory-metrics/
├── trajectory_metrics.py
├── download_docent_trajectories.py
├── summarize_message_metrics.py
├── collection_ids.json
├── requirements.txt
├── README.md
├── sample_data/
│   └── tiny_trajectory.json
├── tests/
│   └── test_trajectory_metrics.py
├── results/
│   ├── sample_message_metrics.csv
│   ├── top5_message_metrics.csv
│   └── top5_message_summary.csv
└── reports/
    ├── top5_models_report.md
    └── paper_summary.md
```

## Main tool

The main tool is:

```text
trajectory_metrics.py
```

It takes as input either a single trajectory JSON file or a directory containing trajectory JSON files. For each trajectory, it computes:

- number of `system` messages,
- number of `user` messages,
- number of `assistant` messages,
- number of `tool` messages,
- total number of messages.

It can print results in three formats:

- human-readable text,
- CSV,
- JSON.

## Example usage

Run the tool on one sample trajectory:

```bash
python trajectory_metrics.py sample_data/tiny_trajectory.json
```

Example output:

```text
System messages:    1
User messages:      1
Assistant messages: 1
Tool messages:      1
=======================
Total messages:     4
```

Run the tool on a directory recursively:

```bash
python trajectory_metrics.py sample_data --recursive
```

Export results to CSV:

```bash
python trajectory_metrics.py sample_data --recursive --format csv > results/sample_message_metrics.csv
```

On PowerShell, I used `Set-Content -Encoding utf8` to preserve UTF-8 encoding:

```powershell
python .\trajectory_metrics.py .\sample_data --recursive --format csv | Set-Content -Encoding utf8 .\results\sample_message_metrics.csv
```

## Role normalization

Some trajectories may encode shell observations as `user` messages with an `extra.returncode` field. By default, the tool treats such messages as tool observations, because semantically they represent feedback from the environment.

To count roles exactly as they appear in the JSON file, use:

```bash
python trajectory_metrics.py sample_data --recursive --format csv --raw-roles
```

## Processing the top-five models

For the top-five mini-SWE-agent-v2 models, I exported full transcript JSON files from Docent and processed them with `trajectory_metrics.py`.

The analyzed models were:

1. Claude 4.5 Opus high reasoning
2. Gemini 3 Flash high reasoning
3. MiniMax M2.5 high reasoning
4. Claude Opus 4.6
5. GPT5-2-Codex

For each model, I processed 500 trajectories, so the analysis covers 2500 trajectories in total.

## Local raw data layout

The raw transcript JSON files are not committed to the repository because they are large. They can be regenerated with the helper script `download_docent_trajectories.py`.

The raw transcript JSON files were stored locally in the following structure:

```text
data/
├── claude_4_5_opus_high_reasoning/
│   └── trajectories/
├── claude_opus_4_6/
│   └── trajectories/
├── gemini_3_flash_high_reasoning/
│   └── trajectories/
├── gpt5_2_codex/
│   └── trajectories/
└── minimax_m2_5_high_reasoning/
    └── trajectories/
```


The helper script is:

```text
download_docent_trajectories.py
```

It downloads full transcript JSON files from Docent using the collection IDs stored in:

```text
collection_ids.json
```

The Docent API key should be stored locally in a file named:

```text
docent.env
```

with the following structure:

```text
DOCENT_API_KEY=your_api_key_here
DOCENT_DOMAIN=docent.transluce.org
```

This file is intentionally ignored by Git and should not be committed.

To export the trajectories:

```bash
python download_docent_trajectories.py
```

## Generating the top-five results

After downloading the trajectories, I computed message-level metrics with:

```bash
python trajectory_metrics.py data --recursive --format csv > results/top5_message_metrics.csv
```

On PowerShell:

```powershell
python .\trajectory_metrics.py .\data --recursive --format csv | Set-Content -Encoding utf8 .\results\top5_message_metrics.csv
```

Then I generated a per-model summary with:

```bash
python summarize_message_metrics.py > results/top5_message_summary.csv
```

On PowerShell:

```powershell
python .\summarize_message_metrics.py | Set-Content -Encoding utf8 .\results\top5_message_summary.csv
```

## Results

The generated result files are:

```text
results/top5_message_metrics.csv
results/top5_message_summary.csv
```

`top5_message_metrics.csv` contains one row per trajectory.  
`top5_message_summary.csv` contains aggregate results for each of the five models.

The short report based on these results is available in:

```text
reports/top5_models_report.md
```

The paper summary is available in:

```text
reports/paper_summary.md
```

## Tests

The project includes a small test suite for the trajectory parser and message-counting logic.

Install test dependency:

```bash
pip install pytest
```

Run tests:

```bash
python -m pytest
```

Expected result:

```text
4 passed
```

## Dependencies

The core metric tool uses only the Python standard library.

For running tests:

```bash
pip install pytest
```

For exporting data from Docent:

```bash
pip install docent-python
```

The Docent export script is optional. The metric tool itself does not require Docent.

## Notes

The main results used in the report are message-level metrics generated from full trajectory JSON files. The repository includes the derived CSV results and reports, but not the full raw transcript JSON files.