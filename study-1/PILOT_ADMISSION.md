# study-1 — PILOT ADMISSION (isolated)

Anchor 2026-07-14. Panel openrouter:z-ai/glm-5.2, openrouter:openai/gpt-5.6-luna. Pilot kept OUT of the verified pool: no clustering/split/merge. Receipts in `verification/receipts_pilot/`.

## Verdicts per split (post-resolve)

| split | admit | drop | needs_human | total |
|---|---|---|---|---|
| fresh | 32 | 13 | 0 | 45 |
| unanswerable | 7 | 5 | 0 | 12 |
| stable | 4 | 0 | 0 | 4 |
| no_search | 4 | 0 | 0 | 4 |
| **all** | **47** | **18** | **0** | **65** |

## Dropped (18)

- **g1f-business-01** (fresh): gold_uncertain_panel_split — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-business-01v1** (fresh): gold_disputed_panel_agrees_other — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-entertainment-01** (fresh): gold_disputed_panel_agrees_other — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-entertainment-01v1** (fresh): gold_disputed_panel_agrees_other — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-news-01v1** (fresh): gold_uncertain_panel_split — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-news-02** (fresh): gold_disputed_panel_agrees_other — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-news-02v1** (fresh): gold_disputed_panel_agrees_other — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-news-03** (fresh): gold_disputed_panel_agrees_other — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-news-03v1** (fresh): gold_disputed_panel_agrees_other — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-sports-03v2** (fresh): gold_disputed_panel_agrees_other — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-tech-01** (fresh): gold_disputed_panel_agrees_other — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-tech-02v2** (fresh): gold_disputed_panel_agrees_other — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1f-tech-03** (fresh): gold_uncertain_panel_split — gold disputed/uncertain at probe -> drop (overwrite-recovery disabled)
- **g1u-04** (unanswerable): panel_found_confident_answer_item_is_answerable
- **g1u-05** (unanswerable): unanswerable_confirmed_awaiting_negative_signoff — a panel model (glm-5.2) found a credible specific answer -> answerable -> drop
- **g1u-09** (unanswerable): unanswerable_confirmed_awaiting_negative_signoff — a panel model (glm-5.2) found a credible specific answer -> answerable -> drop
- **g1u-10** (unanswerable): panel_found_confident_answer_item_is_answerable
- **g1u-11** (unanswerable): unanswerable_confirmed_awaiting_negative_signoff — a panel model (gpt-5.6-luna) found a credible specific answer -> answerable -> drop

## Golds overwritten by panel during resolve (0)


## Admitted fresh items (32) — spot check

- **g1f-business-01v2** (business, 2026-06-22) gold='Webster Financial' — What company was involved in Santander's largest U.S. acquisition?
- **g1f-business-02** (business, 2026-06-22) gold='$4 billion' — How much was SoftBank's planned acquisition of DigitalBridge valued at in June 2026?
- **g1f-business-02v1** (business, 2026-06-22) gold='$4 billion' — What was the approximate valuation of SoftBank's DigitalBridge acquisition?
- **g1f-business-02v2** (business, 2026-06-22) gold='$4 billion' — SoftBank agreed to buy DigitalBridge for approximately how much?
- **g1f-business-03** (business, 2026-06-30) gold='$60 billion' — What was the value of the largest transaction listed among the top IT transactions of June 2026?
- **g1f-business-03v1** (business, 2026-06-30) gold='$60 billion' — How large was the SpaceX–Anysphere transaction listed for June 2026?
- **g1f-business-03v2** (business, 2026-06-30) gold='$60 billion' — What amount was associated with the largest June IT transaction?
- **g1f-entertainment-02** (entertainment, 2026-06-20) gold='ATEEZ' — Who won the Grand Prize (Daesang) at the 35th Seoul Music Awards held on June 20, 2026?
- **g1f-entertainment-02v1** (entertainment, 2026-06-20) gold='ATEEZ' — Which K-pop group won the top prize at the Seoul Music Awards?
- **g1f-news-01** (news, 2026-06-24) gold='more than 100' — How many buildings collapsed in the twin earthquakes that struck northwestern Venezuela on June 24, 2026?
- **g1f-other-01** (other, 2026-06-12) gold='$75 billion' — What was the record amount raised by SpaceX's IPO on June 12, 2026?
- **g1f-other-01v1** (other, 2026-06-12) gold='$75 billion' — How much did SpaceX raise in its record-breaking IPO in June 2026?
- **g1f-other-01v2** (other, 2026-06-12) gold='$75 billion' — What was the size of SpaceX's IPO in June 2026?
- **g1f-politics-01** (politics, 2026-06-16) gold='Evian, France' — Where was the 2026 G7 Leaders' Summit held?
- **g1f-politics-01v1** (politics, 2026-06-16) gold='Evian, France' — Which French town hosted the 2026 G7 summit?
- **g1f-politics-01v2** (politics, 2026-06-16) gold='Evian, France' — Where did G7 leaders meet in June 2026?
- **g1f-politics-02** (politics, 2026-06-16) gold='Forging New Partnerships and Rebuilding International Solidarity' — What was the title of the working session at the G7 summit on June 16, 2026, attended by G7 countries and partner countries?
- **g1f-politics-02v1** (politics, 2026-06-16) gold='Forging New Partnerships and Rebuilding International Solidarity' — What was the name of the G7 working session on June 16, 2026, that included partner countries?
- **g1f-sports-01** (sports, 2026-06-07) gold='Alexander Zverev' — Who won the 2026 French Open men's singles title?
- **g1f-sports-01v1** (sports, 2026-06-07) gold='Alexander Zverev' — Who won the French Open men's singles?
- **g1f-sports-01v2** (sports, 2026-06-07) gold='Alexander Zverev' — Who won the men's singles title at Roland-Garros in 2026?
- **g1f-sports-02** (sports, 2026-06-13) gold='New York Knicks' — Which team won the 2026 NBA Finals?
- **g1f-sports-02v1** (sports, 2026-06-13) gold='New York Knicks' — Who won the NBA championship in 2026?
- **g1f-sports-02v2** (sports, 2026-06-13) gold='New York Knicks' — Which team won the NBA Finals?
- **g1f-sports-03** (sports, 2026-06-14) gold='Carolina Hurricanes' — Which team won the 2026 Stanley Cup?
- **g1f-sports-03v1** (sports, 2026-06-14) gold='Carolina Hurricanes' — Who won the Stanley Cup in 2026?
- **g1f-tech-01v1** (tech, 2026-06-03) gold='Project Glasswing' — What was the name of Anthropic's June 2026 project announcement?
- **g1f-tech-01v2** (tech, 2026-06-03) gold='Project Glasswing' — Which project did Anthropic announce in early June 2026?
- **g1f-tech-02** (tech, 2026-06-02) gold='June 2–5, 2026' — When did COMPUTEX 2026 run in Taipei?
- **g1f-tech-02v1** (tech, 2026-06-02) gold='June 2–5, 2026' — What were the dates of COMPUTEX 2026?
- **g1f-tech-03v1** (tech, 2026-07-09) gold='Muse Image' — What image generator did Meta release in July 2026?
- **g1f-tech-03v2** (tech, 2026-07-09) gold='Muse Image' — What is Meta's new image-generation model called?
