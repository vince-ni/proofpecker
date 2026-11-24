# Proofpecker · 证据啄木鸟

**If the code were wrong, would this test still pass?**

Proofpecker gives AI reviewers three jobs. One checks the design, one traces the implementation, and one asks what the tests actually prove. Use the same model for all three or choose one for each role. Every finding keeps the version of the evidence its reviewer saw, so you can revisit it after a fix.

[中文使用指南](README.zh-CN.md) · [Download the CLI or skill](https://github.com/vince-ni/proofpecker/releases/latest) · [Read the example capture](skills/proofpecker/scripts/pecker_example/capture.txt)

## Try it in one command

With [uv](https://docs.astral.sh/uv/), run the offline example without installing a project or setting an API key.

```sh
uvx --from https://github.com/vince-ni/proofpecker/releases/download/v0.1.0/proofpecker-0.1.0-py3-none-any.whl proofpecker demo
```

A finished job already has a stop marker. Correct code leaves it alone. Faulty code writes the same marker again. Both runs end with the same snapshot. The demo executes both cases, prints the result, and saves the review material. It makes zero model calls.

## Install once

| Where you work | One-time install |
| --- | --- |
| Codex | `npx skills add vince-ni/proofpecker --skill proofpecker -a codex -y` |
| Claude Code | `npx skills add vince-ni/proofpecker --skill proofpecker -a claude-code -y` |
| Gemini CLI | `npx skills add vince-ni/proofpecker --skill proofpecker -a gemini-cli -y` |
| Terminal on macOS, Windows or Linux | `uv tool install https://github.com/vince-ni/proofpecker/releases/download/v0.1.0/proofpecker-0.1.0-py3-none-any.whl` |

The skill installer targets the current project. Add `-g` for your user account. After installation ask **“Use Proofpecker to review this change and check what the tests prove.”** The skill bundles its Python helper. An agent host with fresh reviewer sessions can use its own models and login. The separate API runner uses the credentials below.

For pipx, replace `uv tool install` with `pipx install`. For an offline install, download the wheel from Releases and install its local path in a Python 3.10+ environment. The CLI has zero runtime dependencies. The release also includes a zip of the standalone skill.

## Run a real review

With a local Ollama model already installed, this command launches three independent requests against the example. Replace the model ID with one available to you.

```sh
proofpecker review --example --roles design,implementation,evidence --model ollama/qwen3:14b
```

For your own project, name a claim and its source files. The selected text goes to each model you choose. Each role receives the source, test and capture together. Runs are saved under `.proofpecker/` in the current directory.

```sh
proofpecker review --claim "Stopping a finished job performs no write" --model ollama/qwen3:14b src/worker.py tests/test_stop.py logs/stop.txt
```

The default roles are implementation and evidence. Use design for a proposal or architectural change. Use `--plan FILE` for multiple claims and deferred scope. Paths are relative to the plan. Each packet accepts up to 160 KB of serialized UTF-8 material. Split larger projects by claim and keep its proof together. [Example plan](skills/proofpecker/scripts/pecker_example/plan.json)

## Mix models in one run

Choose a default with `--model provider/model-id` or `PROOFPECKER_MODEL`. Override any selected role using `--engine role=provider/model-id`. The models run concurrently and receive separate requests without previous messages or tools. Use IDs your account actually exposes.

```sh
proofpecker review --example --roles design,implementation,evidence \
  --engine design=gemini/YOUR_GEMINI_MODEL \
  --engine implementation=anthropic/YOUR_CLAUDE_MODEL \
  --engine evidence=ollama/qwen3:14b
```

Run `proofpecker models` to see local configuration. It checks settings without making a network request. Change an endpoint with `PROOFPECKER_<PROVIDER>_URL`. Use a base URL with its API version where required.

| Provider name | Adapter | Credential |
| --- | --- | --- |
| `openai` | Responses | `OPENAI_API_KEY` |
| `anthropic` | Claude Messages | `ANTHROPIC_API_KEY` |
| `gemini` | Gemini generateContent | `GEMINI_API_KEY` |
| `deepseek` | Chat Completions | `DEEPSEEK_API_KEY` |
| `qwen` | Alibaba Cloud Model Studio, Beijing default | `DASHSCOPE_API_KEY` |
| `kimi` | Moonshot, China default | `MOONSHOT_API_KEY` |
| `glm` | Zhipu BigModel, China default | `ZHIPUAI_API_KEY` |
| `ollama` | Local Chat Completions on port 11434 | none |
| `compatible` | Custom Chat Completions endpoint, including local LM Studio | `PROOFPECKER_COMPATIBLE_URL`, optional `PROOFPECKER_API_KEY` |

Regional endpoints and available model IDs depend on your account. For a China or international workspace set the corresponding preset URL to match your key. Offline contract tests exercise request shapes, response parsing, failure handling and mixed routing. Read the [verification results](VERIFICATION.md) for the live model run and its missed finding.

## Inspect and follow up

- `proofpecker pack --example --out first` freezes inputs locally. `prompt first evidence` emits a role prompt for a fresh external session. `record first evidence --receipt reply.json` imports its JSON envelope. For these commands use the `proofpecker` prefix.
- `proofpecker assess RUN` verifies the packet and receipts, lists findings by original role and ID, and separates missing roles, missing material, blocking findings and deferred scope. Exit 0 means the selected reports and requested material are present. Read the findings for severity. Exit 2 means missing input or a workflow error.
- `proofpecker resume RUN --model provider/id` retries missing roles. Errors and earlier successful reports remain available.
- `proofpecker review --plan updated.json --roles evidence --follow-up 'OLD_RUN#evidence.1' --model provider/id` sends a specific finding to a fresh reviewer with current evidence. The new packet links to the original receipt. Open both runs to see the original severity and the new disposition.

SHA-256 binds the exact supplied files and prompts within a trusted workspace. Human-imported receipts carry the reviewer's model/session declaration. Keep original reports when grouping repeated findings. Review execution, finding resolution and release authorization are separate decisions.

## Origins

Developed from Vince Ni’s Zen review workflow. In its first internal comparison, splitting files by role left the evidence reviewer without 13 items the full reviewer had received. That experience led to the shared evidence bundle per claim in this release. The stop-marker example is a small, public reconstruction of one observation. The comparison involved two Zen workflows and was a single case.

Fresh-context review and role separation draw inspiration from [Google's Elephant–Goldfish Model](https://github.com/google/elephant-goldfish-model). The public implementation and example are independently authored. [MIT license](LICENSE)
