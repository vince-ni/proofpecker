# v0.1.0 verification

| What we checked | Observed result |
| --- | --- |
| CLI installation from the wheel | The installed command ran the offline stop-marker demo outside the source tree. |
| Python and operating systems | The GitHub Actions matrix installed the package, ran the workflow tests, demo, and provider configuration listing on Ubuntu, macOS and Windows with Python 3.11. |
| Agent skill distribution | The skills installer installed the project-scoped skill for Codex, Claude Code and Gemini CLI. The installed helper ran in a clean project. |
| Codex CLI invocation | Codex CLI 0.170.0 loaded the installed skill when prompted with `$proofpecker`, built a review packet, and recorded implementation and evidence receipts. The desktop client and in-chat execution in Claude Code and Gemini CLI remain untested. |
| Live model | Three separate local Ollama requests to Qwen3 14B completed and produced readable, version-bound design, implementation and evidence receipts. |
| Other models | Offline tests exercise the OpenAI Responses, Claude Messages, Gemini generateContent and Chat Completions request/response formats. Role routing is tested with different providers. Individual commercial accounts and model IDs have not been live-tested in this release. |

## What the example actually showed

The fixture's stop marker is present before the call. Writing that marker again leaves the same snapshot as doing nothing. The offline example reproduces both paths.

In the live Qwen3 run the evidence reviewer treated the matching snapshots as confirmation. It missed the gap that the deterministic example demonstrates. All three reports arrived successfully. This is one case and provides no estimate of overall review accuracy.

Reproduce with `proofpecker demo` and, with the model available locally, `proofpecker review --example --roles design,implementation,evidence --model ollama/qwen3:14b`. Compare the evidence role's raw receipt with the two outcomes in the demo.

## Codex CLI follow-up

In a clean Git project, the eight installed skill files matched the v0.1.0 release ZIP byte for byte. A fresh Codex CLI session received a prompt beginning with `$proofpecker` and a copy of the bundled stop-marker fixture. The prompt requested the implementation and evidence roles. Both receipts identified the same gap in `capture.txt`: adding an existing marker can leave the final snapshot unchanged.

Re-running `assess` reproduced the saved assessment. It reported `review_execution: complete` with both roles present. It exited with code 2 because the evidence reviewer requested an observation of attempted writes, such as a count of calls to `markers.add`. The first attempt to launch nested CLI processes encountered a sandbox restriction. The successful receipts declared different reviewer sessions and recorded the model as `unknown`. The captured native events did not expose two child thread IDs for independent verification.
