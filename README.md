# Frontier models state different decision theory preferences depending on who's asking

Companion repository for the LessWrong post of that title (Alex Kastner, 2026). It holds everything behind the
post's tables: the exact prompts, every raw sample from every model, the judge's classification of each answer,
and the code that turns them into the tables.

## What is here

| Path | Contents |
|---|---|
| `post/lesswrong_post.md` | The post. |
| `post/tables_generated_notags.md` | Every table the code can generate from the tag-free data, one section per table key (the post uses a trimmed selection). |
| `post/prompts_verbatim.md` | Every prompt behind the post's tables, verbatim. |
| `results/OTHER_MODELS.md` | The post's first table (one sentence about the user, then the question) and the concrete-problems table for every model tested. |
| `results/DEEP_PREFERENCE_OTHER_MODELS.md` | The "FDT/UDT preference runs deeper" tests (thinking effort, book praise at the highest effort, anti-tailoring system prompts, reasoning summaries) repeated on Opus 5.5, Opus 5 and GPT-6 Astra, with a reading. |
| `results/NAMED_PERSONS.md` | Named public figures as the cue ("I'm Dario Amodei." in the user turn or "The user is Dario Amodei." as the system prompt), 28 names on four models, with a reading. |
| `results/NAMED_ACTIONS.md` | Concrete problems posed to named decision theorists (10 names, 6 problems, user-turn and system-prompt formats) on four models, with a reading. |
| `results/AUDIENCE_PDOOM_TIMELINES.md` | Do stated P(loss of control) and AI timelines depend on the audience? 80 cues (personas, system prompts, openers, conversations, named people) on four models, with a reading. |
| `results/THIRD_PERSON_MATRIX.md` | Second-person versus third-person wording ("do you think a rational agent should…") of the concrete problems under the post's unnamed cues, Fable 5.1 and Opus 5.5. |
| `results/MODEL_COMPARISON.md` | Every table for Fable 5.1, Opus 5.5 and Opus 5 side by side, with a narrative of what changed in Opus 5.5 (`results/MODEL_COMPARISON_header.md`). |
| `post/tables_generated_notags_<model>.md` | The full table set built from another model's samples (Opus 5.5: all 355 cells of the post; Opus 5: the cells it was run on). |
| `results/*.md` | Analysis notes for individual experiments, e.g. `AHMED_JOYCE.md` (book praise), `SYSPROMPT_CROSS.md` (system prompts), `REASONING_NOTES.md` (reasoning summaries), `BW_wording_then_act.md`, `BBMAX_followthrough.md`, `NOTAGS_CHECK.md` (tag-free vs tagged numbers). |
| `data/*.jsonl.gz` | All raw samples and judge caches, gzipped (about 220 MB packed, 1 GB unpacked). `data/MANIFEST.json` lists row counts and SHA-256 checksums. |
| `dtcues/` | The code: prompt bank, sampling, judges, table generation, preview server. |
| `scripts/pack_data.py` | Packs `results/*.jsonl` into `data/` and back. |

## Reproducing the tables

```bash
uv sync
uv run python scripts/pack_data.py unpack                           # data/*.jsonl.gz -> results/*.jsonl
POST_MODE=notags uv run python -m dtcues.post_tables --no-splice   # -> post/tables_generated_notags.md
POST_MODE=notags uv run python -m dtcues.other_models              # -> results/OTHER_MODELS.md
POST_MODEL=claude-opus-5-5 POST_MODE=notags uv run python -m dtcues.post_tables   # -> post/tables_generated_notags_claude-opus-5-5.md
uv run python -m dtcues.compare_models claude-opus-5-5 claude-opus-5             # -> results/MODEL_COMPARISON.md
uv run python -m dtcues.post_prompts                               # -> post/prompts_verbatim.md
uv run python -m dtcues.serve_report                               # preview of the post at http://localhost:8791/post.html
```

No API key is needed for any of that. To sample new answers, copy `.env.example` to `.env`, add keys, and run for example

```bash
uv run python -m dtcues run --models claude-fable-5-1 --effort high --n 100 --notags \
    --ids B__Q_neutral__acad_prof --concurrency 20 --out results/raw_claude-fable-5-1_high_notags_example.jsonl
uv run python -m dtcues.judge_notags        # classify every unjudged free-text answer with Claude Sonnet 5
```

`--topup-to 100` instead of `--n 100` adds samples until every prompt has 100 valid ones across all raw files.
To replicate the whole post on another model, `POST_MODE=notags uv run python -m dtcues.model_plan --model <id> --launch --chunks 12 --concurrency 100`
records every (prompt, effort) cell the table generators read and tops that model up in parallel processes; then run the judges
(`dtcues.judge_notags`, `dtcues.judge_fav <id>`, `dtcues.judge_thinking_notags <id>`) and build its tables with `POST_MODEL=<id>`.

## How the data was produced

**Prompts.** `dtcues/prompts.py` (`build_prompts()`) defines every prompt. Ids have the form `SET__QUESTION__CUE[__VARIANT]`,
for example `B__Q_neutral__acad_prof` is the fixed question preceded by "I'm a philosophy professor who works on decision theory."
The main sets: `A` no cue, `B`/`M`/`X` one-sentence personas, `S` system prompts, `U1`/`U6` earlier conversation turns
(answered live by the model), `AA` concrete decision problems and the acausal-trade questions with cues, `BB`
name-a-theory-then-face-a-problem, `AH` book praise, `WR` remediation system prompts, `V` other philosophical debates,
`BW` question wordings. `post/prompts_verbatim.md` lists the rendered text of everything the post uses.

**Tag-free answers.** The post's numbers come from prompts run with `--notags`, which strips every "put your answer in
`<theory></theory>` tags" instruction, so the model answers in free text as it would for a normal user. Each answer is
classified by Claude Sonnet 5 with the fixed rubrics in `dtcues/judge_notags.py` (which theory is named, which option
is chosen, yes/no, and so on); labels are cached in `judge_notags.jsonl`, keyed by a hash of the answer text.
Files without `notags` in the name are the earlier tagged runs (the model answers inside tags, parsed by
`dtcues/parse.py`); `results/NOTAGS_CHECK.md` compares the two per prompt.

**Sampling.** Claude models: Anthropic Messages API with adaptive thinking (summarized) and `output_config.effort`
set to low, high (the default and the setting for every table unless stated), xhigh or max. GPT-6 Astra: OpenAI
Responses API with default settings. Output cap 16,000 tokens for high effort (never reached), 128,000 for max effort.
Every percentage is computed over the first 100 valid samples per prompt (by timestamp), excluding API errors and
answers cut off by the output cap; `rows()` in `dtcues/post_tables.py` implements this.

**Reasoning summaries.** `thinking` holds the summarized reasoning the API returns (raw chains of thought are not
available); `dtcues/judge_thinking.py` and `dtcues/judge_fav.py` annotate them.

## Row format

One JSON object per line. The fields that matter:

| Field | Meaning |
|---|---|
| `prompt_id`, `set`, `persona`, `question`, `fmt`, `system`, `prefix`, `prior_turns`, `followups` | Which prompt (see `dtcues/prompts.py`). |
| `prompt_text` | The exact final user turn sent. `prior_responses` holds the model's live replies to any earlier turns. |
| `model`, `served_model`, `effort`, `sample_idx`, `ts`, `request_id` | Model id as requested and as served, thinking effort, sample index, Unix timestamp. |
| `response_text`, `thinking`, `stop_reason`, `usage` | The answer, its reasoning summary, why generation stopped, token counts. |
| `fu_records` | For two-turn prompts: the follow-up turn(s) and their answers. |
| `notags` | `true` for tag-free runs. |

The judge caches (`judge_notags.jsonl`, `judge_thinking*.jsonl`, `judge_fav.jsonl`) map a hash of the judged text to the label.

## Where each table in the post comes from

| Post section | Table key in `post/tables_generated_notags.md` |
|---|---|
| A sentence identifying the user as an academic | `personas` |
| Academic-philosophy-coded topics; question wording | `openers`, `tasks`, `wording` |
| Anti-sycophancy overcorrection | `views`, `ahmed` (and `results/AHMED_JOYCE.md`) |
| Concrete decision problems; acausal trade | `matrix`, `acausal` |
| Consistency after naming a theory | `second_turn` (max effort: `results/BBMAX_followthrough.md`) |
| Thinking effort; reasoning summaries; system prompts | `effort`, `reasoning_fav`, `sysprompts2` (and `results/REASONING_NOTES.md`, `results/SYSPROMPT_CROSS.md`) |
| Other philosophical debates | `realism` |
| Other models | `opus_personas`, `astra_personas`, `results/OTHER_MODELS.md` |

## Licenses

Code: MIT (`LICENSE`). Data, notes and generated tables: CC BY 4.0 (`LICENSE-DATA`).
