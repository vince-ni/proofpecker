# v0.1.0 verification

| What we checked | Observed result |
| --- | --- |
| CLI installation from the wheel | The installed command ran the offline stop-marker demo outside the source tree. |
| Python and operating systems | The GitHub Actions matrix installed the package, ran the workflow tests, demo, and provider configuration listing on Ubuntu, macOS and Windows with Python 3.11. |
| Agent skill distribution | The skills installer installed the project-scoped skill for Codex, Claude Code and Gemini CLI. The installed helper ran in a clean project. The clients' in-chat review sessions were not exercised in this check. |
| Live model | Three separate local Ollama requests to Qwen3 14B completed and produced readable, version-bound design, implementation and evidence receipts. |
| Other models | Offline tests exercise the OpenAI Responses, Claude Messages, Gemini generateContent and Chat Completions request/response formats. Role routing is tested with different providers. Individual commercial accounts and model IDs have not been live-tested in this release. |

## What the example actually showed

The fixture's stop marker is present before the call. Writing that marker again leaves the same snapshot as doing nothing. The offline example reproduces both paths.

In the live Qwen3 run the evidence reviewer treated the matching snapshots as confirmation. It missed the gap that the deterministic example demonstrates. All three reports arrived successfully. This is one case and provides no estimate of overall review accuracy.

Reproduce with `proofpecker demo` and, with the model available locally, `proofpecker review --example --roles design,implementation,evidence --model ollama/qwen3:14b`. Compare the evidence role's raw receipt with the two outcomes in the demo.
