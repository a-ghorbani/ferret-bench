# study-1 — HUMAN QUEUE

Anchor 2026-07-14. Every item here is `needs_human` (or an ambiguous cluster). Splits contain only `admit` items; nothing here is in dev/holdout yet.

Totals: 28 needs_human receipts + 0 ambiguous cluster pairs.

## 1. Disputed / uncertain golds (6) — panel did not confirm our gold
The panel (with search) either agreed on a DIFFERENT answer (disputed) or split (uncertain). Decide: fix gold, or drop.

- **fr2-news-02** (fresh, gold_disputed_panel_agrees_other)  our_gold='Evian-les-Bains, France'
  - Q: Which town hosted the G7 summit in June 2026?
  - panel: claude-sonnet-5='Évian-les-Bains, France' | gpt-5.6-sol='Évian-les-Bains, France'
- **fr2-news-08** (fresh, gold_disputed_panel_agrees_other)  our_gold='Azerbaijan'
  - Q: Which country's president was invited to the July 2026 NATO summit in Ankara but did not attend?
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **fr2-tech-08** (fresh, gold_disputed_panel_agrees_other)  our_gold='$91 billion'
  - Q: When Nvidia reported earnings in May 2026, how much revenue did it forecast for the following quarter?
  - panel: claude-sonnet-5='$78.0 billion' | gpt-5.6-sol='NObodyKNOWS'
- **fr2-tech-14** (fresh, gold_uncertain_panel_split)  our_gold="Salesforce's Fin acquisition"
  - Q: Which deal was announced first in June 2026: Salesforce buying Fin, or SpaceX buying Cursor's maker?
  - panel: claude-sonnet-5="Salesforce's acquisition of Fin was announced first. Salesfo" | gpt-5.6-sol='**Salesforce buying Fin was announced first**, on **June 15,'
- **fr3-col-02** (fresh, gold_disputed_panel_agrees_other)  our_gold='Google Gemini'
  - Q: whats siri actually running on now after the apple event
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='iOS 27 public beta'
- **fr3-und-11** (fresh, gold_disputed_panel_agrees_other)  our_gold='macOS Golden Gate'
  - Q: what's the new macos called?
  - panel: claude-sonnet-5='macOS 26 Tahoe' | gpt-5.6-sol='macOS 26 Tahoe'

## 2. Recurring-event items needing valid_until (9)
Gold is confirmed but the question is time-relative; sign a `valid_until` (proposed = event_date + ~358d).

- **fr3-und-01**  gold='Paris Saint-Germain (beat Arsenal on penalties)'  proposed valid_until=2027-05-23
  - Q: who won the champions league?
- **fr3-und-02**  gold='New York Knicks'  proposed valid_until=2027-06-06
  - Q: who won the nba finals?
- **fr3-und-03**  gold='Carolina Hurricanes'  proposed valid_until=2027-06-07
  - Q: who won the stanley cup?
- **fr3-und-04**  gold='Alexander Zverev'  proposed valid_until=2027-05-31
  - Q: who won the french open?
- **fr3-und-05**  gold='Belgium, 4-1 in the round of 16'  proposed valid_until=2027-06-23
  - Q: who knocked the usa out of the world cup?
- **fr3-und-06**  gold='Charles Leclerc'  proposed valid_until=2027-06-28
  - Q: who won the british grand prix?
- **fr3-und-07**  gold='Wyndham Clark'  proposed valid_until=2027-06-14
  - Q: who won the us open in golf?
- **fr3-und-08**  gold='Toyota #7 (Conway, Kobayashi, de Vries)'  proposed valid_until=2027-06-07
  - Q: who won le mans?
- **fr3-und-18**  gold='Schmigadoon!'  proposed valid_until=2027-05-31
  - Q: what won best musical at the tonys?

## 3. Unanswerable items — sign the negative (13)
Panel with search did not surface a specific answer. Human confirms the negative against the archived evidence URLs and the expires_on.

- **un-fp-01**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: How much did OpenAI pay to acquire Perplexity AI, and when did the deal close?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2099-01-01)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-fp-02**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: What price did Apple announce for the Vision Pro 3 headset it unveiled at the WWDC 2026 keynote?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2099-01-01)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-fp-03**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: Who did Elon Musk name as his successor as Tesla CEO when he stepped down in 2026?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2099-01-01)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-fp-04**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: Which city was selected to host the 2036 Summer Olympics at the IOC session in June 2026?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2029-01-01)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-fp-05**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: How many seats did Reform UK win in the June 2026 UK general election?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2029-08-15)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-ud-01**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: Who won the 2026 Nobel Peace Prize?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2026-10-09)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-ud-02**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: Who won the 2026 Ballon d'Or?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2026-10-26)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-ud-03**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: Which party won control of the US Senate in the 2026 midterm elections?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2026-11-03)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-uf-01**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: What did Tim Cook eat for breakfast on the morning of Apple's WWDC 2026 keynote on June 8?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2099-01-01)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-uf-02**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: Exactly how many parameters does OpenAI's GPT-5 have?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2099-01-01)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-uf-03**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: How many paying Claude subscribers did Anthropic have on 1 July 2026?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2099-01-01)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-uf-04**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: How many strides did John Korir take over the full course while winning the 2026 Boston Marathon?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2099-01-01)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'
- **un-uf-05**  (unanswerable_confirmed_awaiting_negative_signoff)
  - Q: What exactly did Mexico's head coach say to his players in the dressing room at half-time of the World Cup opening match against South Africa?
  - all_declined=True  src_urls=True  expires_ok=True (expires_on=2099-01-01)
  - panel: claude-sonnet-5='NObodyKNOWS' | gpt-5.6-sol='NObodyKNOWS'

## 4. Ambiguous fact clusters (0 near-threshold pairs)
Question similarity in [0.80, 0.85): possibly the same fact. Human decides whether to merge fact_ids (matters for holdout leakage).


## 5. Multi-item fact clusters to confirm (15)
These admitted items were auto-merged into one fact_id (shared source URL / identical gold / Q-sim>0.85). Confirm they are truly variants (holdout is split by fact_id).

- fact_001: fr2-news-01, fr2-news-03, fr2-news-10, fr2-news-13, fr2-news-15, fr3-col-12
- fact_002: fr2-news-04, fr2-news-12, fr2-news-14, fr2-news-17
- fact_009: fr2-sport-01, fr2-sport-08, fr2-sport-10, fr2-sport-12, fr2-sport-14, fr2-sport-17, fr3-col-08
- fact_010: fr2-sport-02, fr2-sport-13, fr2-sport-16, fr3-col-06
- fact_011: fr2-sport-03, fr2-sport-04, fr3-col-09
- fact_012: fr2-sport-05, fr2-sport-18
- fact_014: fr2-sport-07, fr2-sport-15
- fact_016: fr2-sport-11, fr3-und-19
- fact_018: fr2-tech-02, fr2-tech-09, fr2-tech-15, fr3-col-01
- fact_019: fr2-tech-03, fr2-tech-13, fr3-und-10
- fact_020: fr2-tech-04, fr2-tech-11, fr2-tech-12
- fact_022: fr2-tech-06, fr2-tech-16
- fact_023: fr2-tech-07, fr2-tech-10, fr2-tech-18
- fact_027: fr3-col-05, fr3-und-15
- fact_061: st-09, st-24
