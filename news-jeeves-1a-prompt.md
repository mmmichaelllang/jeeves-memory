# News-Jeeves: Daily Research Pipeline (v6.0)

This is an automated daily news research pipeline. The task is to run web research across multiple categories, collect findings, and save a structured JSON session file as a Gmail draft. A separate write phase (fired after this task completes) will read that draft and compose the final briefing.

**Pipeline overview:** Run research → truncate fields → save session JSON as Gmail draft → chain write phase.

---

## PRE-FLIGHT — DISCOVER AVAILABLE TOOLS

Execute ALL three ToolSearch calls in parallel as your FIRST action:

- `ToolSearch("gmail")` — finds Gmail search/read/draft tools
- `ToolSearch("tavily")` — finds Tavily search/research/extract tools
- `ToolSearch("imessage")` — finds iMessage tools

**Rules:**
- Record the EXACT tool names returned (they are UUID-prefixed and vary by session).
- Set `GMAIL_AVAILABLE=true` only if ToolSearch("gmail") returned at least one tool.
- Set `TAVILY_AVAILABLE=true` only if ToolSearch("tavily") returned at least one tool.
- Set `IMESSAGE_AVAILABLE=true` only if ToolSearch("imessage") returned at least one tool.
- Do not call any tool not returned by ToolSearch — calling non-existent tools aborts the pipeline.
- If all three return empty: continue in WebSearch-only mode.

---

## STEP 0 — COMPUTE DATE AND LOAD CONFIG

**Compute session date (UTC):**
```bash
python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%d'))"
```
Store the printed value as SESSION_DATE.

**Load sector config** — run both in parallel:

```
WebFetch("https://raw.githubusercontent.com/mmmichaelllang/jeeves-memory/main/sectors/vault-insights.json")
```
Parse JSON. Find first item with `"status":"pending"` in `queue[]`. Store `insight`, `context`, `note_path`. If queue is empty: set `vault_insight.available=false`.

```
WebFetch("https://raw.githubusercontent.com/mmmichaelllang/jeeves-memory/main/sectors/newyorker-talk.json")
```
Extract `covered[].url` list → store as NYR_COVERED.

---

## STEP 1 — DEDUPLICATION CHECK

**Only if GMAIL_AVAILABLE=true:** Use the gmail search tool to query `subject:📜 Daily Intelligence` from the last 7 days. Read up to 3 recent briefings. Parse `<!-- COVERAGE_LOG: [...] -->` HTML comments for covered URLs and headlines. Store as dedup set.

**If GMAIL_AVAILABLE=false:** Set dedup set to empty.

---

## STEP 1b — CORRESPONDENCE IMPORT

**If GMAIL_AVAILABLE=true:** Search `subject:"Correspondence —" newer_than:2d (in:drafts OR in:sent)`.
- Found: read it, set `correspondence.found=true`, store text.
- Not found: search `is:unread newer_than:2d -label:promotions -label:spam` (maxResults=15). Set `correspondence.found=false`, `fallback_used=true`.

**If GMAIL_AVAILABLE=false and IMESSAGE_AVAILABLE=true:** Use iMessage tool (limit=20). Set `fallback_used=true`.

**If both unavailable:** Set `correspondence.found=false`, `fallback_used=true`, `text="No correspondence integrations available."`.

---

## STEP 2 — RESEARCH

Substitute [CURRENT_MONTH] and [CURRENT_YEAR] with actual current values.

**BLOCK A — LOCAL / CAREER / FAMILY (all parallel):**
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

**BLOCK D — WEARABLE / TEACHER AI (all parallel):**
- WebSearch: `"AI voice hardware 2026"`
- If TAVILY_AVAILABLE=true: tavily_search (#1/4): `"wearable AI pendants pins lifelogging devices"`
- If TAVILY_AVAILABLE=true: tavily_search (#2/4): `"AI tools classroom teacher productivity high school"`
- If TAVILY_AVAILABLE=true: tavily_search (#3/4): `"AI-assisted lesson plans high school English History EdTech"`
- If TAVILY_AVAILABLE=true: tavily_search (#4/4): `"best EdTech resources teachers"`
- If TAVILY_AVAILABLE=false: WebSearch: `"wearable AI pendants pins lifelogging devices 2026"`
- If TAVILY_AVAILABLE=false: WebSearch: `"AI tools classroom teacher productivity high school 2026"`
- If TAVILY_AVAILABLE=false: WebSearch: `"AI-assisted lesson plans high school English EdTech 2026"`
- If TAVILY_AVAILABLE=false: WebSearch: `"best EdTech resources teachers 2026"`

**BLOCK E — DEEP RESEARCH (all parallel):**
- If TAVILY_AVAILABLE=true: tavily_research (#1/3): `"Relational ontologies" "Triadic logic" "Quantum perichoresis" "Non-linear triadic dynamics" "Trinitarianism in contemporary metaphysics"`
- If TAVILY_AVAILABLE=true: tavily_research (#2/3): `"multi-agent research systems" "reasoning models LLM 2026" "autonomous research pipelines" "prompt engineering advances 2026"`
- If TAVILY_AVAILABLE=true: tavily_research (#3/3): `"UAP disclosure 2026" "UAP congressional hearings" "non-human intelligence declassification"`
- If TAVILY_AVAILABLE=false: WebSearch: `"triadic ontology perichoresis metaphysics philosophy 2026"`
- If TAVILY_AVAILABLE=false: WebSearch: `"multi-agent AI systems reasoning models 2026"`
- If TAVILY_AVAILABLE=false: WebSearch: `"UAP disclosure congressional hearings 2026"`

**BLOCK F — NEW YORKER TALK OF THE TOWN:**

WebSearch: `"site:newyorker.com/magazine talk of the town 2026"`

Identify the most recent article URL matching `https://www.newyorker.com/magazine/YYYY/MM/DD/[slug]` that is NOT in NYR_COVERED.

Fetch full text — try in order:
1. If TAVILY_AVAILABLE=true: use tavily_extract on the article URL.
2. If step 1 unavailable or fails: WebFetch `https://r.jina.ai/[ARTICLE_URL]`
3. If both fail: set `newyorker.available=false`.

If content retrieved: set `newyorker.available=true`, store full text.

**BLOCK G — VAULT INSIGHT:**
Use data already loaded in Step 0 (vault_insight fields).

---

## STEP 3 — ENRICHMENT

From all search results, identify 5 most important or novel articles not in the dedup set.

- If TAVILY_AVAILABLE=true: use tavily_extract on those 5 URLs.
- If TAVILY_AVAILABLE=false: use WebFetch on those 5 URLs. If WebFetch fails for a URL, skip it and note `fetch_failed=true`.

---

## FIELD TRUNCATION — APPLY BEFORE STEP 4

Truncate every `findings`, `text`, and `insight` field before assembling the session JSON:
- Maximum 2,500 characters per field. If exceeded: keep first 2,500 chars, append ` [TRUNCATED]`.
- Exception: `newyorker.text` maximum is 8,000 characters.
- Apply to: all `findings` in local_news, global_news, intellectual_journals, wearable_ai; career fields; family fields; weather; triadic_ontology.findings; ai_systems.findings; uap.findings; vault_insight.insight; every `text` in enriched_articles; newyorker.text.
- This keeps the total JSON under 40KB and prevents Gmail draft timeouts.

---

## STEP 4 — SAVE SESSION AS GMAIL DRAFT

Build the session JSON with actual research data (all fields filled):

```json
{
  "date": "[SESSION_DATE]",
  "status": "complete",
  "dedup": {"covered_urls": [], "covered_headlines": []},
  "correspondence": {"found": false, "fallback_used": false, "text": ""},
  "weather": "",
  "local_news": [
    {"source": "local", "findings": ""},
    {"source": "city_council", "findings": ""},
    {"source": "public_safety", "findings": ""}
  ],
  "career": {"district_jobs": "", "sps_jobs": ""},
  "family": {"choir": "", "toddler": ""},
  "global_news": [
    {"source": "BBC", "findings": ""},
    {"source": "Guardian", "findings": ""},
    {"source": "NYT", "findings": ""},
    {"source": "AlJazeera", "findings": ""},
    {"source": "NPR", "findings": ""},
    {"source": "CNN", "findings": ""},
    {"source": "Memeorandum", "findings": ""}
  ],
  "intellectual_journals": [
    {"source": "NYRB", "findings": ""},
    {"source": "NewYorker", "findings": ""},
    {"source": "Aeon", "findings": ""},
    {"source": "Marginalian", "findings": ""},
    {"source": "Kottke", "findings": ""},
    {"source": "ProPublica", "findings": ""},
    {"source": "Intercept", "findings": ""},
    {"source": "ScientificAmerican", "findings": ""},
    {"source": "LRB", "findings": ""},
    {"source": "ArtsLetters", "findings": ""},
    {"source": "BigThink", "findings": ""},
    {"source": "Jacobin", "findings": ""},
    {"source": "OpenSecrets", "findings": ""}
  ],
  "wearable_ai": [
    {"query": "AI voice hardware 2026", "findings": ""},
    {"query": "wearable AI pendants pins lifelogging", "findings": ""},
    {"query": "AI tools classroom teacher productivity", "findings": ""},
    {"query": "AI-assisted lesson plans high school English", "findings": ""},
    {"query": "best EdTech resources teachers", "findings": ""}
  ],
  "triadic_ontology": {"findings": ""},
  "ai_systems": {"findings": ""},
  "uap": {"findings": ""},
  "newyorker": {"available": false, "title": "", "text": "", "source": "The New Yorker", "url": ""},
  "vault_insight": {"available": false, "insight": "", "context": "", "note_path": ""},
  "enriched_articles": [
    {"url": "", "title": "", "text": ""},
    {"url": "", "title": "", "text": ""},
    {"url": "", "title": "", "text": ""},
    {"url": "", "title": "", "text": ""},
    {"url": "", "title": "", "text": ""}
  ]
}
```

Fill every field with actual research data. Apply the truncation rules above before calling the draft tool.

**If GMAIL_AVAILABLE=true:** Call the gmail create_draft tool:
- subject: `🔬 Jeeves Session [SESSION_DATE]`
- to: lang.mc@gmail.com
- contentType: text/plain
- body: JSON string of the completed object above

**If GMAIL_AVAILABLE=false:** Write to `/tmp/session-[SESSION_DATE].json` using the Write tool.

Output one line after the draft is saved:
`RESEARCH COMPLETE: [SESSION_DATE] | enriched=[count] | tavily=[yes/no] | vault=[available/unavailable] | newyorker=[available/unavailable]`

Set FILE_WRITE_SUCCESS=true if the draft was saved. Set FILE_WRITE_SUCCESS=false only if the draft call failed.

---

## STEP 5 — CHAIN WRITE PHASE

Proceed only if FILE_WRITE_SUCCESS=true. If false, stop — the fallback cron at 5:50 AM handles recovery.

Load the scheduled tasks update tool:
```
ToolSearch: {"query": "select:mcp__scheduled-tasks__update_scheduled_task", "max_results": 1}
```

Compute a cron expression for 5 minutes from now in local time:
```bash
python3 -c "from datetime import datetime, timedelta; f=datetime.now()+timedelta(minutes=5); print(f'{f.minute} {f.hour} * * *')"
```

Call the update tool:
```
mcp__scheduled-tasks__update_scheduled_task({
  "taskId": "news-jeeves-write",
  "cronExpression": "[output from python above, e.g. '18 5 * * *']"
})
```

Note: cron is used instead of a one-shot fireAt because fireAt events are sometimes silently dropped by the scheduler. A cron entry is evaluated every minute and cannot be skipped.

---

## TOOL BUDGET

- WebSearch: unlimited (included in session cost)
- tavily_search: max 4 calls (Block D only, if available)
- tavily_research: max 3 calls (Block E only, if available)
- tavily_extract: max 5 calls (Step 3 enrichment + Block F, if available)
- tavily_crawl, tavily_map: do not use
