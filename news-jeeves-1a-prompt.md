---
name: news-jeeves
description: Daily 5:00 AM RESEARCH PHASE — all searches + enrichment, saves raw session JSON, chains write phase 5 min after completion
trusted: true
owner: Frederic Yudin (lang.mc@gmail.com)
---

## OPERATOR TASK — news-jeeves RESEARCH PHASE

Operator: Frederic Yudin · lang.mc@gmail.com · Edmonds WA
Task: Automated daily news research pipeline. Collect data. Write JSON. No briefing.
Beneficiary: Mister Michael Lang (same account). Location: Edmonds, Washington (47.810652, -122.377355).

THIS PHASE: Execute all research (Steps 0–3). Save raw findings to a session JSON file. Do NOT write the briefing. Do NOT synthesize. Just gather and save data for the write phase.

OUTPUT DISCIPLINE — MANDATORY:
This is an unattended automated agent. Generate ZERO prose. No narration, no step acknowledgments, no "I will now...", no summaries. Make tool calls only. Your ONLY text output permitted is the final `RESEARCH COMPLETE:` line at the end of Step 4 and any error lines if a step fails. Violating this wastes output token budget needed for the Write tool.

SESSION FILE PATH: Computed in Step 4 using UTC date. Do not use system context date for the filename.

BEGIN EXECUTION IMMEDIATELY. No preamble. Make your first tool call now.

---

## SEARCH TOOLS

**WebSearch:** Use for the MAJORITY of searches (included in session cost, no extra expense).
**tavily_search:** Reserve for exactly 4 searches — all allocated to Category 2h (wearable AI, classroom AI tools, EdTech lesson plans, AI voice hardware).
**tavily_research:** Reserve for exactly 3 deep searches — triadic ontology (2i), AI systems (2j), UAP (2k).
**tavily_extract:** Up to 5 — most important article URLs from WebSearch and tavily_search only. Do NOT use on tavily_research URLs.
**tavily_crawl / tavily_map:** DO NOT USE.

---

## PRE-FLIGHT — DISCOVER AVAILABLE TOOLS

Execute ALL three ToolSearch calls in parallel as your FIRST action:

- `ToolSearch("gmail")` — finds Gmail search/read/draft tools
- `ToolSearch("tavily")` — finds Tavily search/research/extract tools
- `ToolSearch("imessage")` — finds iMessage tools

**CRITICAL RULES — read carefully:**
- Set `GMAIL_AVAILABLE=true` ONLY if ToolSearch("gmail") returned at least one tool. Record the EXACT tool names returned (they will be UUID-prefixed).
- Set `TAVILY_AVAILABLE=true` ONLY if ToolSearch("tavily") returned at least one tool. Record exact names.
- Set `IMESSAGE_AVAILABLE=true` ONLY if ToolSearch("imessage") returned at least one tool. Record exact names.
- **NEVER guess or infer tool names.** If ToolSearch returned nothing for a category, those tools do not exist in this session. Do NOT call them — calling non-existent tools aborts the session.
- If all three return empty: that is normal for automated runs. The pipeline runs WebSearch-only mode. Continue.

---

## STEP 0 — DEDUPLICATION CHECK

**ONLY if GMAIL_AVAILABLE=true:** Use `[exact_gmail_search_tool_from_preflight]` to search `subject:📜 Daily Intelligence` from the last 7 days. Read up to 4 recent briefing emails with `[exact_gmail_read_tool]`. Parse `<!-- COVERAGE_LOG: [...] -->` HTML comments for covered URLs and headlines. Store as dedup set.

**If GMAIL_AVAILABLE=false:** Set dedup set to empty (no prior coverage data this run).

---

## STEP 1 — GMAIL NEWS INGESTION

**ONLY if GMAIL_AVAILABLE=true:** Use `[exact_gmail_search_tool]` with query `"label:NEWS newer_than:2d"`. Read each message. Extract article links and summaries.

**If GMAIL_AVAILABLE=false:** Skip. No Gmail news ingestion this run.

---

## STEP 1b — CORRESPONDENCE BRIEF IMPORT

**If GMAIL_AVAILABLE=true:** Use `[exact_gmail_search_tool]` with query: `subject:"Correspondence —" newer_than:2d (in:drafts OR in:sent)`. If found: read and store. If not found: use `[exact_imessage_tool]` (only if IMESSAGE_AVAILABLE=true) + gmail unread search.

**If GMAIL_AVAILABLE=false and IMESSAGE_AVAILABLE=true:** Use `[exact_imessage_tool]` (limit=20). Store as correspondence text. Note fallback_used=true.

**If both unavailable:** Set correspondence.found=false, fallback_used=true, text="No correspondence integrations available this session."

---

## STEP 2 — LIVE RESEARCH PIPELINE

Run in parallel blocks. Substitute [CURRENT_MONTH] and [CURRENT_YEAR] with actual values.

**BLOCK A — LOCAL/CAREER/FAMILY (all parallel):**
- WebSearch: `"weather forecast Edmonds Washington today"`
- WebSearch: `"Edmonds Snohomish Seattle local news this week" site:seattletimes.com OR site:myedmondsnews.com OR site:crosscut.com OR site:kuow.org OR site:lynnwoodtimes.com`
- WebSearch: `"Edmonds Washington city council meeting [CURRENT_MONTH] [CURRENT_YEAR]"`
- WebSearch: `"Edmonds Washington public safety crime report [CURRENT_MONTH] [CURRENT_YEAR]"`
- WebSearch: `"high school English teacher jobs [CURRENT_YEAR] Edmonds Shoreline Mukilteo Everett Northshore Lake Washington Bellevue Snohomish Marysville Monroe Lake Stevens Renton Highline Mercer Island Issaquah Riverview Tukwila school district"`
- WebSearch: `"Seattle Public Schools high school English teacher positions [CURRENT_YEAR]"`
- WebSearch: `"Seattle Puget Sound choir auditions Washington state [CURRENT_MONTH] [CURRENT_YEAR]"`
- WebSearch: `"toddler activities Edmonds WA [CURRENT_MONTH] [CURRENT_YEAR] library zoo children's museum storytime"`

**BLOCK B — GLOBAL NEWS (all parallel):**
- WebSearch: `"BBC breaking news"`
- WebSearch: `"CNN top stories"`
- WebSearch: `"Al Jazeera breaking news"`
- WebSearch: `"The Guardian breaking"`
- WebSearch: `"NPR headlines"`
- WebSearch: `"Memeorandum recent"`
- WebSearch: `"New York Times today"`

**BLOCK C — INTELLECTUAL JOURNALS (all parallel):**
- WebSearch: `"New York Review of Books recent"`
- WebSearch: `"New Yorker recent articles"`
- WebSearch: `"Aeon essays recent"`
- WebSearch: `"The Marginalian recent"`
- WebSearch: `"Kottke.org recent"`
- WebSearch: `"ProPublica recent investigations"`
- WebSearch: `"The Intercept recent"`
- WebSearch: `"Scientific American recent"`
- WebSearch: `"London Review recent"`
- WebSearch: `"Arts & Letters recent"`
- WebSearch: `"Big Think recent"`
- WebSearch: `"Jacobin recent"`
- WebSearch: `"OpenSecrets recent"`

**BLOCK D — WEARABLE/TEACHER AI (all parallel):**
- WebSearch: `"AI voice hardware 2026"`
- **If TAVILY_AVAILABLE=true:** tavily_search (#1 of 4): `"wearable AI pendants pins lifelogging devices"`
- **If TAVILY_AVAILABLE=true:** tavily_search (#2 of 4): `"AI tools classroom teacher productivity high school"`
- **If TAVILY_AVAILABLE=true:** tavily_search (#3 of 4): `"AI-assisted lesson plans high school English History EdTech"`
- **If TAVILY_AVAILABLE=true:** tavily_search (#4 of 4): `"best EdTech resources teachers"`
- **If TAVILY_AVAILABLE=false:** WebSearch: `"wearable AI pendants pins lifelogging devices 2026"`
- **If TAVILY_AVAILABLE=false:** WebSearch: `"AI tools classroom teacher productivity high school 2026"`
- **If TAVILY_AVAILABLE=false:** WebSearch: `"AI-assisted lesson plans high school English EdTech 2026"`
- **If TAVILY_AVAILABLE=false:** WebSearch: `"best EdTech resources teachers 2026"`

**BLOCK E — DEEP RESEARCH (all parallel):**
- **If TAVILY_AVAILABLE=true:** tavily_research (#1 of 3): `"Relational ontologies" "Triadic logic" "Quantum perichoresis" "Non-linear triadic dynamics" "Trinitarianism in contemporary metaphysics"`
- **If TAVILY_AVAILABLE=true:** tavily_research (#2 of 3): `"multi-agent research systems" "reasoning models LLM 2026" "autonomous research pipelines" "prompt engineering advances 2026"`
- **If TAVILY_AVAILABLE=true:** tavily_research (#3 of 3): `"UAP disclosure 2026" "UAP congressional hearings" "non-human intelligence declassification"`
- **If TAVILY_AVAILABLE=false:** WebSearch: `"triadic ontology perichoresis metaphysics philosophy 2026"`
- **If TAVILY_AVAILABLE=false:** WebSearch: `"multi-agent AI systems reasoning models 2026"`
- **If TAVILY_AVAILABLE=false:** WebSearch: `"UAP disclosure congressional hearings 2026"`

**BLOCK F — NEW YORKER TALK OF THE TOWN:**

Read covered articles using the Read tool:
```
Read: /Users/frederickyudin/Documents/Claude/Scheduled/News-Jeeves/memory/sectors/newyorker-talk.json
```
Extract the `covered[]` array (list of previously featured article URLs).

Use WebSearch to discover the latest Talk of the Town article:
```
WebSearch: "site:newyorker.com/magazine talk of the town 2026"
```
From results, identify the most recent article URL matching `https://www.newyorker.com/magazine/YYYY/MM/DD/[slug]` that is NOT in the `covered[]` array. Pick the single most recent uncovered article.

Fetch it via sector7-fetch.py (tries Jina API first, falls back to archive.ph):
```bash
python3 /Users/frederickyudin/Documents/Claude/Scheduled/News-Jeeves/scripts/sector7-fetch.py --url "[ARTICLE_URL]"
```

Capture the JSON output. If `available: false` or the script fails: set `newyorker.available=false`.

**BLOCK G — VAULT INSIGHTS:**
Read `/Users/frederickyudin/Documents/Claude/Scheduled/News-Jeeves/memory/sectors/vault-insights.json`.
Find first item with `"status": "pending"`. If none, set vault_insight.available=false.

---

## STEP 3 — CONTENT ENRICHMENT

From ALL WebSearch and tavily_search results, identify 5 most important/novel articles NOT in the dedup set.

**If TAVILY_AVAILABLE=true:** Use `tavily_extract` on those 5 URLs for full text.
**If TAVILY_AVAILABLE=false:** Use WebFetch on those 5 URLs for full text. If WebFetch fails for a URL, skip it and note `fetch_failed=true` for that entry.

---

## FIELD TRUNCATION — MANDATORY BEFORE STEP 4

Before assembling the session JSON, truncate ALL individual `findings`, `text`, and `insight` fields:
- Maximum length per field: 2,500 characters
- If a field exceeds 2,500 chars: keep the first 2,500 chars, append ` [TRUNCATED]`
- Apply to: every `findings` in `local_news[]`, `global_news[]`, `intellectual_journals[]`, `wearable_ai[]`; `career.district_jobs`, `career.sps_jobs`, `family.choir`, `family.toddler`, `weather`, `triadic_ontology.findings`, `ai_systems.findings`, `uap.findings`, `vault_insight.insight`, and every `text` in `enriched_articles[]` and `newyorker.text`
- Exception: `newyorker.text` max is 8,000 chars (it's long-form, needed for Sector 7)
- This keeps total session JSON under 40KB and prevents Write tool timeout

---

## STEP 4 — SAVE SESSION FILE

**⚠ THIS PHASE WRITES A JSON FILE TO DISK. NO Gmail draft. NO HTML. NO briefing. JSON only.**

First, compute the session date using **UTC**:
```bash
python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%d'))"
```
Use printed output as SESSION_DATE. Also run:
```bash
mkdir -p /Users/frederickyudin/Documents/Claude/Scheduled/News-Jeeves/session
```

**Write the session file using INCREMENTAL BASH CALLS — do NOT use the Write tool or generate the full JSON in one shot (that causes stream idle timeout).**

Execute these 5 Bash calls sequentially. Each call writes one section and updates the file on disk. Inline actual data from your research — substitute real content for every placeholder.

**Call 1 — scaffold + metadata:**
```bash
python3 -c "
import json
d = {
  'date': 'SESSION_DATE',
  'status': 'complete',
  'dedup': {'covered_urls': [], 'covered_headlines': []},
  'correspondence': {'found': False, 'fallback_used': True, 'text': ''},
  'weather': '',
  'local_news': [], 'career': {}, 'family': {},
  'global_news': [], 'intellectual_journals': [], 'wearable_ai': [],
  'triadic_ontology': {}, 'ai_systems': {}, 'uap': {},
  'newyorker': {'available': False}, 'vault_insight': {'available': False},
  'enriched_articles': []
}
open('/Users/frederickyudin/Documents/Claude/Scheduled/News-Jeeves/session/session-SESSION_DATE.json','w').write(json.dumps(d))
print('CALL1_OK')
"
```

**Call 2 — weather + local + career + family + correspondence:**
```bash
python3 -c "
import json
p = '/Users/frederickyudin/Documents/Claude/Scheduled/News-Jeeves/session/session-SESSION_DATE.json'
d = json.load(open(p))
d['weather'] = 'WEATHER_TEXT'
d['correspondence'] = {'found': FOUND_BOOL, 'fallback_used': FALLBACK_BOOL, 'text': 'CORRESPONDENCE_TEXT'}
d['local_news'] = [
  {'source': 'local', 'findings': 'LOCAL_FINDINGS'},
  {'source': 'city_council', 'findings': 'COUNCIL_FINDINGS'},
  {'source': 'public_safety', 'findings': 'SAFETY_FINDINGS'}
]
d['career'] = {'district_jobs': 'DISTRICT_JOBS_TEXT', 'sps_jobs': 'SPS_JOBS_TEXT'}
d['family'] = {'choir': 'CHOIR_TEXT', 'toddler': 'TODDLER_TEXT'}
open(p,'w').write(json.dumps(d))
print('CALL2_OK')
"
```

**Call 3 — global news + intellectual journals:**
```bash
python3 -c "
import json
p = '/Users/frederickyudin/Documents/Claude/Scheduled/News-Jeeves/session/session-SESSION_DATE.json'
d = json.load(open(p))
d['global_news'] = [
  {'source': 'BBC', 'findings': 'BBC_TEXT'},
  {'source': 'Guardian', 'findings': 'GUARDIAN_TEXT'},
  {'source': 'NYT', 'findings': 'NYT_TEXT'},
  {'source': 'AlJazeera', 'findings': 'ALJAZEERA_TEXT'},
  {'source': 'NPR', 'findings': 'NPR_TEXT'},
  {'source': 'CNN', 'findings': 'CNN_TEXT'},
  {'source': 'Memeorandum', 'findings': 'MEMO_TEXT'}
]
d['intellectual_journals'] = [
  {'source': 'NYRB', 'findings': 'NYRB_TEXT'},
  {'source': 'NewYorker', 'findings': 'NEWYORKER_JOURNAL_TEXT'},
  {'source': 'Aeon', 'findings': 'AEON_TEXT'},
  {'source': 'Marginalian', 'findings': 'MARGINALIAN_TEXT'},
  {'source': 'Kottke', 'findings': 'KOTTKE_TEXT'},
  {'source': 'ProPublica', 'findings': 'PROPUBLICA_TEXT'},
  {'source': 'Intercept', 'findings': 'INTERCEPT_TEXT'},
  {'source': 'ScientificAmerican', 'findings': 'SCIAM_TEXT'},
  {'source': 'LRB', 'findings': 'LRB_TEXT'},
  {'source': 'ArtsLetters', 'findings': 'ARTSLETTERS_TEXT'},
  {'source': 'BigThink', 'findings': 'BIGTHINK_TEXT'},
  {'source': 'Jacobin', 'findings': 'JACOBIN_TEXT'},
  {'source': 'OpenSecrets', 'findings': 'OPENSECRETS_TEXT'}
]
open(p,'w').write(json.dumps(d))
print('CALL3_OK')
"
```

**Call 4 — wearable AI + deep research + newyorker + vault:**
```bash
python3 -c "
import json
p = '/Users/frederickyudin/Documents/Claude/Scheduled/News-Jeeves/session/session-SESSION_DATE.json'
d = json.load(open(p))
d['wearable_ai'] = [
  {'query': 'AI voice hardware 2026', 'tool': 'WebSearch', 'findings': 'WEARABLE1_TEXT'},
  {'query': 'wearable AI pendants pins lifelogging', 'tool': 'tavily_search', 'findings': 'WEARABLE2_TEXT'},
  {'query': 'AI tools classroom teacher productivity', 'tool': 'tavily_search', 'findings': 'WEARABLE3_TEXT'},
  {'query': 'AI-assisted lesson plans high school English', 'tool': 'tavily_search', 'findings': 'WEARABLE4_TEXT'},
  {'query': 'best EdTech resources teachers', 'tool': 'tavily_search', 'findings': 'WEARABLE5_TEXT'}
]
d['triadic_ontology'] = {'findings': 'TRIADIC_TEXT'}
d['ai_systems'] = {'findings': 'AISYSTEMS_TEXT'}
d['uap'] = {'findings': 'UAP_TEXT'}
d['newyorker'] = {'available': NEWYORKER_AVAILABLE_BOOL, 'title': 'NEWYORKER_TITLE', 'text': 'NEWYORKER_TEXT', 'source': 'The New Yorker', 'url': 'NEWYORKER_URL'}
d['vault_insight'] = {'available': VAULT_AVAILABLE_BOOL, 'insight': 'VAULT_INSIGHT_TEXT', 'context': 'VAULT_CONTEXT_TEXT', 'note_path': 'VAULT_NOTE_PATH'}
open(p,'w').write(json.dumps(d))
print('CALL4_OK')
"
```

**Call 5 — enriched articles:**
```bash
python3 -c "
import json
p = '/Users/frederickyudin/Documents/Claude/Scheduled/News-Jeeves/session/session-SESSION_DATE.json'
d = json.load(open(p))
d['enriched_articles'] = [
  {'url': 'URL1', 'title': 'TITLE1', 'text': 'TEXT1'},
  {'url': 'URL2', 'title': 'TITLE2', 'text': 'TEXT2'},
  {'url': 'URL3', 'title': 'TITLE3', 'text': 'TEXT3'},
  {'url': 'URL4', 'title': 'TITLE4', 'text': 'TEXT4'},
  {'url': 'URL5', 'title': 'TITLE5', 'text': 'TEXT5'}
]
open(p,'w').write(json.dumps(d))
print('CALL5_OK')
"
```

**Call 6 — verify:**
```bash
python3 -c "
import os, sys
p = '/Users/frederickyudin/Documents/Claude/Scheduled/News-Jeeves/session/session-SESSION_DATE.json'
s = os.path.getsize(p) if os.path.exists(p) else 0
print(f'WRITE_VERIFIED size={s}')
sys.exit(0 if s > 500 else 1)
"
```

If Call 6 exits with code 1: retry by re-running any failed call above.

Output:
`RESEARCH COMPLETE: [SESSION_DATE] | enriched=[count] | vault=[available/unavailable] | newyorker=[available/unavailable] | write_method=Bash-incremental | file_size=[bytes]`

Set FILE_WRITE_SUCCESS=true if verification passed.
Set FILE_WRITE_SUCCESS=false only if all retries failed.

---

## STEP 5 — CHAIN TO WRITE PHASE

After confirming the session file was written (verify it exists and is non-empty), fire the write phase immediately.

**GATE:** Proceed to fire write phase ONLY if FILE_WRITE_SUCCESS=true. If FILE_WRITE_SUCCESS=false: do NOT fire write phase. Stop. The fallback cron at 5:50 AM will handle recovery.

Use ToolSearch to load the update tool:
```
ToolSearch: {"query": "select:mcp__scheduled-tasks__update_scheduled_task", "max_results": 1}
```

Compute a cron expression for **5 minutes from now in LOCAL time** (the scheduler interprets cron expressions as LOCAL time, not UTC):
```bash
python3 -c "
from datetime import datetime, timedelta
future = datetime.now() + timedelta(minutes=5)
print(f'{future.minute} {future.hour} * * *')
"
```
Use the printed output as the cronExpression (e.g. `"15 5 * * *"`).

Then call:
```
mcp__scheduled-tasks__update_scheduled_task({
  "taskId": "news-jeeves-write",
  "cronExpression": "[output from python — e.g. '18 5 * * *']"
})
```

**Why cron not fireAt:** `fireAt` one-shot events are silently dropped by the daemon (two confirmed misses). A cron entry is evaluated every minute and cannot be swallowed. The write phase re-arms `news-jeeves-write` to `50 5 * * *` after every run, so tomorrow's schedule is always clean.

If the session file write FAILED (file missing or 0 bytes): skip Step 5. Do NOT fire the write phase on a failed research run.