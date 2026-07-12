# Provenance — every frozen value and the runs that justified it

Frozen config hash: `2e5a782618fe49a2ce10cb35a532e8d6cefb276c5ab570c12fca9d22cbe6a152` (= `harness/configs/frozen.json` over shipped defaults). Primary metric: fresh-split correctness (judge: google/gemini-3.5-flash, prompt `v2-simpleqa-3way-acceptable`, temp 0). All numbers below are v2-judge numbers from `analysis/scores.jsonl`. Dev models: qwen3-1.7b, ministral-3-3b; weak-model tiebreak: qwen3-06b, gemma-4-e2b. Dataset v1 (sha256 d3502755…), 44 fresh / 30 stable / 15 no_search.

**Evidence tiers** (post-adversarial-review framing): what is validated at full n (44 fresh) is the **a2 bundle** — enriched tool descriptions + brave + markdown — pooled over 4 models: 162/176 vs shipped 139/176 (0.920 vs 0.790, one-sided Fisher p=0.0004). Individual factor increments inside the bundle were not isolated at full n (no markdown-only or brave-only arms; the a1 run shows factors do not compose naively). Screening rows (n=20, 17 uncorrected arms) are hypothesis-tier.

## The bundle (changed from shipped)

| Parameter | Frozen value | Evidence |
|---|---|---|
| `tool_desc` | **enriched** (usage guidance + keyword-query hint) | Screening-tier: largest single-arm effect, 0.95/1.00 vs shipped 0.70/0.80 (`20260710-231840`, `20260711-000342` vs `20260710-224310`, `20260710-234546`). Present in every winning full-n bundle. Caveat: a1 (enriched+brave, no markdown) ≤ shipped at full n (0.750/0.932 vs 0.773/0.977; `20260711-090347/095619`) — not separable from the bundle. |
| `provider` | **brave** (recommended default; tavily supported) | Screening-tier pooled: 36/40 vs 30/40 (p=0.07 uncorrected; `20260710-232202`, `20260711-000529`). Full-n bundle-tier: tavily variant of the guided bundle lost (a5 2-dev 0.784 vs a3 0.909; `2026071*-ablate-a5/a3-*`). Token cost model-dependent (ministral −24%, qwen +10%). |
| `result_format` | **markdown** | Bundle-tier: a2 is the best full-n config on all 4 models — qwen3-1.7b 0.886, ministral 0.977 (`20260711-091254/100015-ablate-a2-*`), qwen3-06b 0.886, gemma-4-e2b 0.932 (`20260711-105748/110745-tiebreak-a2-*`) vs shipped 0.773/0.977/0.568/0.841. a2-vs-a1 increment (+6/44 qwen, +2/44 ministral) suggestive, not individually significant. Screen eliminated json (0.75/0.85) and compact (0.70/0.80). |

## Retained shipped defaults (tested, no improvement found)

| Parameter | Frozen value | Evidence (screening-tier unless noted) |
|---|---|---|
| `result_count` | 5 | rc3 0.75/0.85, rc8 0.65/0.80 +tokens, vs shipped 0.70/0.80 (`20260710-224903/225215`, `20260710-234816/234943`). NB: >5 is silently capped by the 1000-token menu ceiling. |
| `snippet_chars` | 280 | snip140 0.70/0.85 mixed; snip-full 0.70/0.75 at +50% tokens (`20260710-230531/230830`, `20260710-235613/235825`). |
| `menu_token_ceiling` | 1000 | No winner needed it raised. |
| `read_url_policy` | available | Bundle-tier: a4 (disabled) 1.000 on ministral (44/44) but engagement 0.86 on qwen3-1.7b; a2 (available) matches composite; read_url is a shipped product feature (`20260711-092819/100632-ablate-a4-*`). "Encouraged" no gain (`20260710-232857`, `20260711-000759`). |
| `read_content_chars` | 4800 | 2400/9600 within ±0.05 (`20260710-233220/233552`, `20260711-001056/001208`). Reads are rare for qwen (≤0.01/q), 0.17–0.46/q for ministral. |
| `max_turns` | 5 | turns3 ~neutral, turns8 no gain (`20260710-233916/234230`, `20260711-001340/001547`). Winners average 1.7–1.9 turns. |
| `system_prompt` | shipped grounding line | guided-v1: +correctness at screen but 0.29 false-search (`20260710-231536`, `20260711-000159`). guided-v2 fixed false-search and won on qwen3-06b (0.909 tiebreak) but stacking with markdown hurt (a6 2-dev 0.864 vs a2 0.932; `2026071*-ablate-a6-*`) — anti-synergy, prompt stays shipped. guided-v2 = documented prompt-only runner-up (`harness/configs.py`). |
| `untrusted_wrapper` | on | Security-load-bearing in PocketPal; held constant (factors.md). |
| generation | temp 0.7, top_p 0.95, max_tokens 1024, seed 42 | Mirrors app behavior (PocketPal forwards Pal completionSettings; loop sets nothing). |

## Anti-recommendations (measured, do not ship)

- JSON tool-result formatting (screen: no gain, more tokens).
- result_count 8 without raising the menu token ceiling (silently truncated; and no gain even with the ceiling raised).
- Stacking the guided-v2 system prompt with markdown formatting (a6 anti-synergy, `2026071*-ablate-a6-*`).
