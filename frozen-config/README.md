# frozen-config — the deliverable PocketPal consumes

Filled at the FREEZE phase. Contents when frozen:

- `config.json` — every optimized parameter (provider, result_count, snippet_chars, menu_token_ceiling, result_format, read_url policy + content limit, max_turns, generation params), in the same schema the harness runs (`harness/configs.py`).
- `system_prompt.txt` — the recommended grounding/system prompt text, with `${today}` / `${budget}` placeholders as in PocketPal's `systemPromptResolver`.
- `tool_web_search.json`, `tool_read_url.json` — the recommended OpenAI-style tool definitions (name, description, parameters), drop-in for `toToolDefinition()`.
- `PROVENANCE.md` — one row per frozen value: value chosen, levels tested, run ids that justified it, and the margin (with CIs) over the runner-up.

Rule: no value lands here without run-id provenance; anything left at the PocketPal shipped default is annotated "shipped default retained (no significant improvement found)" with the runs that failed to beat it.
