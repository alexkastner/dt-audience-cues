# phil_sycophancy

Does the implied audience of a prompt change which decision theory Claude / GPT says it endorses?

- **Reports:** `results/REPORT_v2.md` (full, with complete exchanges) and `results/REPORT_1page.md` (one page). Commentable HTML: run `uv run python -m philsyc.serve_report`, open http://127.0.0.1:8791/report_v2.html or `/report_1page.html`; select text, press Cmd+Option+M, type, Cmd+Enter; click a note to edit or delete. Comments autosave to `results/comments/comments_<doc>.md`. Earlier draft: `results/EXPERT_REPORT.md` (first-round comments in `results/comments/comments_expert_report_round1.md`).
- **Working report with every phase:** `results/REPORT.md` (TL;DR at the top; phases 1-2 in sections 1-6, phase 3 follow-ups in section 7).
- **Design, confounds, factors, pre-planned contrasts:** `DESIGN.md`.
- **All per-condition tables** (Wilson CIs, Fisher tests): `results/summary.md`; flat CSV `results/summary.csv`.
- **Cross-model headline table:** `results/headline.md`.
- **Thinking-summary annotations:** `results/thinking_judge_summary.md`; **explanation-balance annotations:** `results/balance_judge_summary.md`.
- **Raw samples** (prompt, response, summarized thinking, usage, request id; multi-turn rows also carry `prior_responses` and `fu_records`): `results/raw_*.jsonl` (~28,000 rows).

## Setup

1. Keys go in `.env` (gitignored):
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-6-astra
   ```
2. Dependencies are managed by `uv` (`uv sync`).

## Commands

```bash
uv run python -m philsyc prompts --sets A C            # inspect the prompt bank (257 prompts, sets A-X)
uv run python -m philsyc list-models --provider openai
uv run python -m philsyc smoke                         # one call per model, verifies keys
uv run python -m philsyc run --models claude-fable-5-1 --n 20 --effort high            # sets A-F
uv run python -m philsyc run --models claude-fable-5-1 --n 20 --effort high --sets G H I J K L L2 M N P S
uv run python -m philsyc run --models gpt-6-astra --n 20 [--openai-effort medium]
uv run python -m philsyc run --models claude-fable-5-1 --n 20 --effort max --max-tokens 32000 --sets A B C E
uv run python -m philsyc judge                         # LLM-label <theory> tags the regex couldn't
uv run python -m philsyc run --models claude-fable-5-1 --n 20 --effort high --sets T U1 U2 U3 U4 U5 U6 V W X H3   # phase 3
uv run python -m philsyc judge-thinking                # annotate Claude thinking summaries (persona sets)
uv run python -m philsyc judge-balance                 # annotate explanation prose (CDT vs FDT balance)
uv run python -m philsyc analyze                       # -> results/summary.md + summary.csv
uv run python -m philsyc.headline                      # -> results/headline.md
```

`run` writes one file per model/effort (`results/raw_<model>_<effort>.jsonl`, or `--out`), is resumable
(skips (prompt, model, effort, sample) keys already present; retries rows that errored or hit the token
cap), and runs `--concurrency` requests at once. `analyze` and `judge*` read `results/raw*.jsonl`.

## Layout

```
philsyc/prompts.py        prompt bank: questions, personas, problems, phase-2 probes; PromptSpec.render()
philsyc/providers.py      Anthropic + OpenAI async clients (multi-turn replay; no refusal fallbacks, on purpose)
philsyc/parse.py          <theory> headline + stance coding; <action>/<answer> choices; credences; asker
philsyc/run.py            resumable sampler (single-turn, two-turn pushback, per-prompt system prompts)
philsyc/judge.py          LLM judge for unparsed <theory> tags        -> results/judge_cache.jsonl
philsyc/judge_thinking.py LLM judge over thinking summaries           -> results/judge_thinking.jsonl
philsyc/judge_balance.py  LLM judge over explanation prose            -> results/judge_balance.jsonl
philsyc/analyze.py        phase-1 tables + planned contrasts          -> results/summary.md
philsyc/analyze2.py       phase-2 and phase-3 sections (sets G-X)
philsyc/headline.py       cross-model headline table                  -> results/headline.md
```
