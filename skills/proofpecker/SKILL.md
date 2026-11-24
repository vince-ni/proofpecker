---
name: proofpecker
description: Run a claim-by-claim independent design, implementation or evidence review for a code change, review packet, or targeted finding recheck. Use when the user asks for Proofpecker, 证据啄木鸟, or an evidence-bound multi-model review.
---

# Proofpecker

Use the Python 3.10+ helper `scripts/proofpecker.py` relative to this skill. It ships with the skill and works without a separate installation. Run it from the project under review. For a walkthrough run `demo`.

1. Express the intended behavior as a checkable claim. Select explicit project-relative UTF-8 files that together show the requirement, implementation, relevant tests and actual output where available. Use a JSON plan for several claims (see `scripts/pecker_example/plan.json`). Record exclusions in `deferred`. For a proposed feature review the design first. An ordinary code change may need only implementation. Add evidence for persistent state, concurrency, cross-layer behavior, or claims about what ran.
2. If the user has selected API models or set `PROOFPECKER_MODEL`, run `review --plan PLAN --roles ROLES --language LANGUAGE`. Add `--engine role=provider/model` for overrides. This sends the selected project texts to each configured model. Honor the user's model, access and data-sharing choices.
3. For review inside an agent host, run `pack` with the same inputs. For each role run `prompt RUN ROLE` and give its full output to a fresh, independent reviewer in a new context. Keep the author's commentary, earlier verdicts and other role reports out of that context. Use the model/routing the user selected and record what the host actually exposes. With no suitable fresh-session mechanism, provide the generated prompts for separate sessions and mark missing roles incomplete.
4. Save each returned JSON envelope exactly as received and run `record RUN ROLE --receipt FILE`. Run `assess RUN`. Retain the original findings and IDs when grouping overlapping observations. Report review execution, unresolved findings, missing material and deferred scope separately.
5. For a disputed observation, add the absent source/test/log to a new plan and run a targeted review with `--follow-up 'OLD_RUN#evidence.1' --roles evidence` (use the finding's actual role). Reference the prior packet and new receipt. Keep previous reports. A source inference, model self-report and observed runtime behavior support different conclusions.
