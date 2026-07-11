# Provenance — every frozen value and the runs that justified it

Frozen config hash: `2e5a782618fe49a2ce10cb35a532e8d6cefb276c5ab570c12fca9d22cbe6a152` (= `harness/configs/frozen.json` over shipped defaults). Primary metric: fresh-split correctness (gemini-3.5-flash judge, v1-simpleqa-3way, temp 0). Dev models: qwen3-1.7b, ministral-3-3b; weak-model tiebreak: qwen3-06b, gemma-4-e2b. Dataset v1 (sha256 d3502755…), 44 fresh / 30 stable / 15 no_search.

| Parameter | Frozen value | Levels tested | Justification (run ids) |
|---|---|---|---|
| `tool_desc` | **enriched** (usage guidance + keyword-query hint in description) | shipped, enriched | Screen: 0.95/1.00 vs shipped 0.75/0.80 (20260710-231840-screen-td-enriched-qwen3-1.7b, 20260711-000342-screen-td-enriched-ministral-3-3b vs 20260710-224310/20260710-234546). Carried in every winning ablate combo (a1–a6). |
| `provider` | **brave** (recommended default; tavily supported) | tavily (shipped), brave | Screen: 0.90/0.90 vs 0.75/0.80 shipped, ~25% fewer prompt tokens (20260710-232202, 20260711-000529). Ablate: a5 (tavily variant of a3) composite 0.795 vs a3 0.909 (20260711-0*-ablate-a5-td-guided2-*, a3-*). |
| `result_format` | **markdown** (bulleted list, bold title, date, snippet, angle-bracket URL) | shipped labeled-blocks, compact, markdown, json | Ablate: a2 best composite 0.921 across dev models (20260711-…-ablate-a2-td-brave-md-qwen3-1.7b 0.864, -ministral-3-3b 0.977); tiebreak: 0.932 on gemma-4-e2b, 0.864 on qwen3-06b (20260711-105748-tiebreak-a2-* runs) vs a3 0.864/0.886 and shipped 0.841/0.568. Screen eliminated json (0.75/0.85) and compact (0.70/0.80). |
| `result_count` | **5** (shipped retained) | 3, 5, 8 | Screen: rc3 0.75/0.85, rc8 0.70/0.80 (+tokens) vs shipped 0.75/0.80 — no significant improvement (20260710-224903/225215, 20260710-234816/234943). |
| `snippet_chars` | **280** (shipped retained) | 140, 280, 2000 | Screen: snip140 mixed (0.70/0.85), snip-full worse + 50% more tokens (0.75/0.75) (20260710-230531/230830, 20260710-235613/235825). |
| `menu_token_ceiling` | **1000** (shipped retained) | 1000; 1600/3000 only as rc8/snip-full escorts | No winner needed it raised. |
| `read_url_policy` | **available** (shipped retained) | disabled, available, encouraged | Ablate: a4 (disabled) 1.000 on ministral but engagement 0.86 on qwen3-1.7b; a2 (available) matches composite (0.921 vs 0.909) and read_url is a shipped product feature (20260711-…-ablate-a4-*, a2-*). Screen: encouraged no gain (20260710-232857, 20260711-000759). |
| `read_content_chars` | **4800** (shipped retained) | 2400, 4800, 9600 | Screen: both variants ±0.05 of shipped, reads are rare (20260710-233220/233552, 20260711-001056/001208). |
| `max_turns` | **5** (shipped retained) | 3, 5, 8 | Screen: turns3 ~neutral, turns8 mixed no-gain (20260710-233916/234230, 20260711-001340/001547). |
| `system_prompt` | **shipped grounding line retained** | date-only, shipped, guided(v1), guided-v2 | guided-v1 caused 0.29 false-search (screen 20260710-231536, 20260711-000159). guided-v2 fixed that and won on qwen3-06b (0.886, tiebreak) but lost to markdown formatting on gemma-4-e2b (0.864 vs 0.932) and stacking it WITH markdown hurt (a6 composite 0.852 < either alone) — anti-synergy, so the prompt stays shipped. guided-v2 is the documented runner-up for prompt-only integrations (kept in harness/configs.py). |
| `untrusted_wrapper` | **on** (shipped retained) | on only | Security-load-bearing in PocketPal; never varied (held constant, factors.md). |
| generation | temp 0.7, top_p 0.95, max_tokens 1024, seed 42 | held constant | Mirrors app-typical Pal settings (PocketPal forwards Pal completionSettings; loop sets nothing). |

Anti-recommendations (measured, do not ship): JSON tool-result formatting; result_count 8 (token cost, no gain — and the shipped 1000-token menu ceiling silently truncates it anyway); stacking guided-v2 prompt with markdown formatting (a6, 20260711 ablate runs).
