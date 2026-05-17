# Top-5 mini-SWE-agent-v2 Trajectory Analysis

I exported full Docent transcript JSON files for the five requested mini-SWE-agent-v2 leaderboard models and processed them with the command-line tool implemented in this repository. The tool counts the number of messages in each trajectory, grouped by role: `system`, `user`, `assistant`, and `tool`. I processed 500 trajectories for each model, so the analysis covers 2500 trajectories in total.

The main result is that the models differ a lot in trajectory length. Claude Opus 4.6 had the shortest trajectories, with 60.84 messages on average. Claude 4.5 Opus high reasoning and GPT5-2-Codex were similar, with around 72 messages per trajectory. Gemini 3 Flash high reasoning and MiniMax M2.5 high reasoning were much longer, with 113.24 and 121.89 messages on average. This shows that models with similar leaderboard positions can still work in very different ways.

| Model | Trajectories | Avg total | Avg assistant | Avg tool | Min total | Max total |
|---|---:|---:|---:|---:|---:|---:|
| Claude 4.5 Opus high reasoning | 500 | 72.41 | 32.89 | 37.51 | 14 | 222 |
| Claude Opus 4.6 | 500 | 60.84 | 28.93 | 29.91 | 11 | 288 |
| Gemini 3 Flash high reasoning | 500 | 113.24 | 56.11 | 55.12 | 2 | 319 |
| GPT5-2-Codex | 500 | 72.88 | 35.04 | 35.84 | 17 | 251 |
| MiniMax M2.5 high reasoning | 500 | 121.89 | 60.44 | 59.44 | 23 | 502 |

The most informative metrics are the assistant and tool message counts, because they show the main agent loop. The assistant chooses an action, and the tool returns feedback from the environment, such as command outputs or file contents. Gemini 3 Flash high reasoning and MiniMax M2.5 high reasoning had almost the same number of assistant and tool messages, which suggests a regular action-observation pattern. Claude Opus 4.6 was much more compact, with only 28.93 assistant messages and 29.91 tool messages on average.

There were also some very long outliers. MiniMax M2.5 high reasoning reached 502 total messages, Gemini 3 Flash high reasoning reached 319, and Claude Opus 4.6 reached 288. These cases may represent difficult tasks, but they may also indicate repeated debugging, inefficient search, or getting stuck in long correction loops.

Overall, the results support the idea that trajectory-level evaluation is useful. A leaderboard score mainly says how many tasks were solved, but not how much work the agent needed to solve them. Message count is a simple metric, and shorter is not always better, but it gives a useful first view of trajectory length, debugging effort, and interaction cost. In this analysis, Claude Opus 4.6 looks the most compact, while MiniMax M2.5 high reasoning and Gemini 3 Flash high reasoning use much longer trajectories.