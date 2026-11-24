# Proofpecker · 证据啄木鸟

**如果代码写错了，这个测试还会通过吗？**

Proofpecker 让 AI 分头审设计、读实现、查证据。你可以让三个角色用同一个模型，也可以各选一个。每条发现都保留对应版本的材料，改完代码还能回到原问题复核。

## 一条命令体验

装有 uv 的电脑可以直接运行离线演示，无需 API Key。

```sh
uvx --from https://github.com/vince-ni/proofpecker/releases/download/v0.1.0/proofpecker-0.1.0-py3-none-any.whl proofpecker demo
```

示例审查一个已经结束的任务。停止标记原本就存在。正确实现不再写入，错误实现把同一个标记又写一次。两种情况的最终快照完全相同。演示实际执行两种情况并输出结果，让你看到这份快照的证明边界。

## 快捷安装

| 使用场景 | 在项目目录执行 |
| --- | --- |
| Codex | `npx skills add vince-ni/proofpecker --skill proofpecker -a codex -y` |
| Claude Code | `npx skills add vince-ni/proofpecker --skill proofpecker -a claude-code -y` |
| Gemini CLI | `npx skills add vince-ni/proofpecker --skill proofpecker -a gemini-cli -y` |
| 终端，macOS / Windows / Linux | `uv tool install https://github.com/vince-ni/proofpecker/releases/download/v0.1.0/proofpecker-0.1.0-py3-none-any.whl` |

Skill 默认装到当前项目，加 `-g` 可装到用户账户。安装后在宿主里说 **“用 Proofpecker 审这个改动，重点核对测试能证明什么。”** 支持独立审查会话的宿主可以使用自己的登录和模型。离线用户可下载 wheel 或 Skill ZIP，命令行和 Skill 脚本均支持 Python 3.10 及以上。[下载发行包](https://github.com/vince-ni/proofpecker/releases/latest)

## 多模型并行审查

已经安装 Ollama 和相应模型时，运行下面这条命令即可对公开示例开始真实三角色审查。

```sh
proofpecker review --example --language 中文 --roles design,implementation,evidence --model ollama/qwen3:14b
```

三个角色也能用不同厂商的模型。下面的 `YOUR_...` 替换为你账户中可调用的模型 ID，先配置对应环境变量。

```sh
proofpecker review --example --language 中文 --roles design,implementation,evidence --engine design=gemini/YOUR_GEMINI_MODEL --engine implementation=anthropic/YOUR_CLAUDE_MODEL --engine evidence=ollama/qwen3:14b
```

| 模型入口 | 环境变量 |
| --- | --- |
| OpenAI Responses | `OPENAI_API_KEY` |
| Anthropic Claude Messages | `ANTHROPIC_API_KEY` |
| Google Gemini generateContent | `GEMINI_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |
| 通义千问 / 阿里云百炼 | `DASHSCOPE_API_KEY` |
| Kimi / 月之暗面 | `MOONSHOT_API_KEY` |
| GLM / 智谱 | `ZHIPUAI_API_KEY` |
| Ollama 本机模型 | 默认使用本机 11434 端口 |
| 其他 Chat Completions 兼容服务 | `PROOFPECKER_COMPATIBLE_URL`，需要时加 `PROOFPECKER_API_KEY` |

`proofpecker models` 打印各入口的配置状态。国内外账户按实际地域设置 `PROOFPECKER_QWEN_URL`、`PROOFPECKER_KIMI_URL` 等。每次运行记录请求的模型和服务端实际返回的型号，未提供的值保留为空。按角色分别发起请求，所选材料会发送给对应服务。首次真实试跑中，Qwen3 完成了三个角色，但漏掉了示例中的证据缺口。[查看验证记录](VERIFICATION.md)

## 审自己的项目

在项目目录运行，显式指定要审的主张和文件。普通改动默认启用实现与证据两种视角，新功能设计可单选 `--roles design`。

```sh
proofpecker review --language 中文 --model ollama/qwen3:14b --claim "任务结束后再次停止不会写入标记" src/worker.py tests/test_stop.py logs/stop.txt
```

多条主张写入 JSON 计划，用 `--plan 路径` 传入。每条主张列出所需证据文件，路径相对计划文件。把没有复审的范围写入 `deferred`。默认材料预算为 160 KB，较大改动按主张拆包。[计划示例](skills/proofpecker/scripts/pecker_example/plan.json)

每次生成独立的运行目录。用 `proofpecker assess 运行目录` 查看报告是否到齐、哪些是未关闭的重要发现、还缺哪些材料。失败可用 `proofpecker resume 运行目录 --model 厂商/型号` 继续。补齐证据或改代码后，用 `--follow-up '旧运行目录#evidence.1' --roles evidence` 对具体问题复核，原报告和原分级会保留。审查结果供人决定是否放行。

源自 Vince Ni 的 Zen 工程审查实践，独立上下文与角色分工借鉴了 Google EGM。初次内部对照发现，按文件种类切分材料让证据角色漏收 13 个原包条目。这是本项目按主张组合证据的由来。[EGM 原项目](https://github.com/google/elephant-goldfish-model) · [英文完整用法](README.md)
