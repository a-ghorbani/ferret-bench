# Factors — agentic web-search config for small on-device LLMs

DECOMPOSE output. Levels marked *(shipped)* mirror PocketPal PR #808 and form the default config; exact shipped values pinned in `harness/CONTRACT.md` once extracted.

## Controlled factors (varied in SCREEN/ABLATE)

| Factor | Levels | Expected effect | Cost to vary |
| ------ | ------ | --------------- | ------------ |
| `result_count` | 3 / 5 *(shipped: TBD)* / 10 | More results = more coverage but context burn + distraction for small models; expect inverted-U | cheap (harness param) |
| `result_format` | shipped format / compact numbered text / markdown list / JSON | Token efficiency and parseability by small models; JSON suspected wasteful | cheap |
| `snippet_length` | full provider description / truncated ~160 chars | Long snippets may substitute for read_url or may drown 1–2B models | cheap |
| `system_prompt` | shipped / minimal (tools speak for themselves) / guided (explicit search→read→cite strategy) | Large expected effect on *when* small models search and whether they iterate | cheap |
| `tool_description` | shipped / enriched (usage guidance + arg hints in description) | Small models rely heavily on descriptions; enrichment may fix bad queries | cheap |
| `provider` | brave / tavily | Tavily returns LLM-ready content chunks; hypothesis: helps small models more than large | cheap to vary, metered API |
| `read_url_policy` | disabled (snippet-only) / available *(shipped)* / prompt-encouraged | Reading pages should improve grounding iff content truncation is right | cheap |
| `read_content_limit` | ~2k / ~4k / ~8k chars *(shipped: TBD)* | Page text is the biggest context consumer; small-ctx models need low limits | cheap |
| `max_turns` | shipped TBD / 5 / 10 | Higher caps rescue hard questions but risk loops; on-device each turn = full prefill | cheap |

## Sweep factor (CONFIRM)

| Factor | Levels | Notes |
| ------ | ------ | ----- |
| `model` | Qwen3-1.7B, Qwen3-4B(mlabonne), Qwen3.5-2B, Qwen3.5-4B, Gemma-3-1B, Gemma-3-4B, Gemma-4-E2B, Ministral-3-3B, Phi-4-mini, SmolLM3-3B, LFM2.5-1.2B, Hermes-3-3B (final list at CONFIRM; all Q4-class GGUF) | Capability gate first: valid tool-call emission; gate failure is a reported result, not an exclusion to hide |

## Held constant

| Factor | Value | Why |
| ------ | ----- | --- |
| Generation params | PocketPal loop defaults (extracted; else temp 0.7 top_p 0.95) | Mirror the app |
| Context size | 8192 (with prompt-size telemetry so 4k feasibility is derivable) | Phone-realistic ceiling |
| Quantization | Q4_K_M class | What phones actually run |
| Judge | frozen model+prompt, temp 0, versioned in manifests | Comparability |
| Dataset version | pinned by hash per run | Comparability |
| Web state | record-replay HTTP cache | Comparability + API budget |

## Nuisance factors (controlled by procedure)

- **Web drift** — live results change hourly → replay cache captured once per dataset version; all configs replay the same capture where queries overlap. Note: different queries (model-generated) can't be fully pre-captured → cache is capture-on-miss; drift risk logged per run window.
- **llama-swap cold loads / flakiness** — warm-up request with retries before each model batch; generous timeouts; strict serialization (one model id in flight, ever).
- **Search API rate limits** — throttle live calls; replay cache absorbs re-runs.
- **Judge nondeterminism** — temp 0, pinned prompt, spot-validated vs human labels.

## Failure modes & confounds (watch explicitly)

- **Total-context confound**: `result_count`, `snippet_length`, `result_format` all move *prompt chars* — the real variable may be context size, not structure. Log prompt tokens per turn; analyze format effects at matched token budgets.
- **Provider confound**: Tavily content chunks are longer than Brave snippets — provider effect entangled with content length; compare at matched truncation too.
- **No-search answering**: model answers fresh questions from (wrong) memory — measured by engagement rate + floor baseline, not assumed away.
- **Loop pathologies**: repeated identical searches, read_url on nonsense URLs, never finalizing — all counted mechanically.
- **Judge leniency to verbosity** — judge prompt requires grading against gold answer, not plausibility; spot-validation checks this.
- **Contamination**: pre-cutoff questions answerable from memory inflate all configs equally but mask config differences — freshness split keeps a subset where retrieval is necessary.
