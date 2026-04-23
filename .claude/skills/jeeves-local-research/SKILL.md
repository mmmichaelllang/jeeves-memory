---
name: jeeves-local-research
description: Run the Jeeves local research phase (v6.0). Requires local Tavily and Gmail MCP tools. Fetches weather, news, career, family, journals, wearable AI, UAP, and Talk of the Town. Saves session JSON as a Gmail draft for the local write phase. Use on Mac with full local MCP access.
disable-model-invocation: true
allowed-tools: Bash WebFetch WebSearch ToolSearch
---

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
- Set `TAVILY_AVAILABLE=true` only if ToolSearch("tavily") returned at least one tool. Also set `TAVILY_QUOTA_OK=true`.
- Set `IMESSAGE_AVAILABLE=true` only if ToolSearch("imessage") returned at least one tool.
- Do not call any tool not returned by ToolSearch — calling non-existent tools aborts the pipeline.
- If all three return empty: continue in WebSearch-only mode.

**DYNAMIC TAVILY DOWNGRADE (applies to every tavily_* call in this pipeline):**
If ANY tavily_search / tavily_research / tavily_extract call returns a quota, rate-limit, usage-limit, 429, or "plan limit exceeded" error, immediately set `TAVILY_QUOTA_OK=false`. For the remainder of the pipeline treat `TAVILY_AVAILABLE=true AND TAVILY_QUOTA_OK=true` as the gate — if either is false, use the WebSearch / WebFetch fallback branch. Do not retry Tavily after a quota failure.

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

Run these WebSearches in parallel:
- `"site:newyorker.com/magazine/2026 talk of the town"`
- `"newyorker.com \"Talk of the Town\" [CURRENT_MONTH] [CURRENT_YEAR]"`
- `"site:newyorker.com/magazine/talk-of-the-town"`

From the combined results, pick the first URL that (a) is on `newyorker.com/magazine/`, (b) is NOT in NYR_COVERED, and (c) appears to be a single article (not the index `/talk-of-the-town` page and not `/news/...`). **Prefer** `YYYY/MM/DD/[slug]` format but do not require it — any `newyorker.com/magazine/...` article URL is acceptable. Record `ARTICLE_URL`, `ARTICLE_TITLE`, and `ARTICLE_SNIPPET` (the search result's excerpt) — the snippet is the guaranteed-available fallback.

If NO article URL passes the filter, still record the highest-relevance search result's `title + snippet` as `ARTICLE_TITLE` and `ARTICLE_SNIPPET` with `ARTICLE_URL=""` and skip the fetch cascade — go straight to the snippet-fallback populate branch below (set `fetch_method="search_result"`, `available=true`).

**Fetch full text — robust cascade, try in order, stop at first success (text ≥ 800 chars):**
1. If TAVILY_AVAILABLE=true AND TAVILY_QUOTA_OK=true: `tavily_extract({"urls":[ARTICLE_URL]})`.
2. `WebFetch("https://r.jina.ai/" + ARTICLE_URL)` — Jina anonymous reader.
3. `WebFetch(ARTICLE_URL)` — direct fetch (often paywalled but try).
4. `WebFetch("https://webcache.googleusercontent.com/search?q=cache:" + ARTICLE_URL)` — Google cache.

**Populate the newyorker object:**
- Success (any of 1–4 returned ≥ 800 chars of article body): `newyorker = {available:true, title:ARTICLE_TITLE, text:<fetched>, source:"The New Yorker", url:ARTICLE_URL, fetch_method:"tavily|jina|direct|cache"}`.
- All four failed: use the WebSearch snippet — `newyorker = {available:true, title:ARTICLE_TITLE, text:"[SNIPPET ONLY — full article unavailable from cloud IP] " + ARTICLE_SNIPPET, source:"The New Yorker", url:ARTICLE_URL, fetch_method:"snippet"}`. **Never set available=false if a URL was identified** — the write phase renders the snippet verbatim, which is better than omitting the sector.
- Only set `newyorker.available=false` if ALL three WebSearches returned zero results. Otherwise always populate with at least snippet-level content.

**BLOCK G — VAULT INSIGHT:**
Use data already loaded in Step 0 (vault_insight fields).

---

## STEP 3 — ENRICHMENT

From all search results, identify the **3** most important or novel articles not in the dedup set. For each, record `url`, `title`, and `snippet` (the WebSearch result excerpt) before attempting fetch — the snippet is the guaranteed-available fallback.

**Robust cascade per URL, stop at first success (text ≥ 600 chars):**
1. If TAVILY_AVAILABLE=true AND TAVILY_QUOTA_OK=true: `tavily_extract({"urls":[URL]})` (may batch up to 3 URLs in one call to save budget).
2. `WebFetch("https://r.jina.ai/" + URL)`.
3. `WebFetch(URL)` direct.
4. Fallback: set `text = "[SNIPPET ONLY] " + snippet`, `fetch_method = "snippet"`. Never skip the entry — always populate all three slots so the write phase has material.

Always emit exactly 3 entries in `enriched_articles`. Never fewer.

---

## FIELD TRUNCATION — APPLY BEFORE STEP 4

Truncate every `findings`, `text`, and `insight` field before assembling the session JSON. Limits are tightened to keep total JSON under ~25 KB and prevent stream-idle timeouts during the create_draft tool call:
- Default maximum: **1,500 characters** per field. If exceeded: keep first 1,500 chars, append ` [TRUNCATED]`.
- `enriched_articles[].text`: maximum **1,200 characters** each.
- `newyorker.text`: maximum **4,000 characters**.
- `correspondence.text`: maximum **2,000 characters**.
- Apply to: all `findings` in local_news, global_news, intellectual_journals, wearable_ai; career fields; family fields; weather; triadic_ontology.findings; ai_systems.findings; uap.findings; vault_insight.insight; every `text` in enriched_articles; newyorker.text; correspondence.text.

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
    {"url": "", "title": "", "text": "", "fetch_method": ""},
    {"url": "", "title": "", "text": "", "fetch_method": ""},
    {"url": "", "title": "", "text": "", "fetch_method": ""}
  ],
  "write_complete": false
}
```

══════════════════════════════════════════════
CRITICAL ANTI-IDLE RULE — READ BEFORE PROCEEDING
══════════════════════════════════════════════
After truncation, your NEXT action is the create_draft tool call. Do NOT pause to summarize, reflect, review, or narrate. Do NOT output analysis prose before the tool call. Emit the tool invocation immediately. A stream idle of more than 60 seconds aborts the session. Continuous token production during JSON assembly prevents timeout.
══════════════════════════════════════════════

Fill every field with actual research data. Apply the truncation rules above. Then emit the tool call on the very next turn.

**If GMAIL_AVAILABLE=true:** Call the gmail create_draft tool in ONE invocation:
- subject: `🔬 Jeeves Session [SESSION_DATE]`
- to: lang.mc@gmail.com
- contentType: text/plain
- body: the complete JSON string of the object above

**If GMAIL_AVAILABLE=false:** Write to `/tmp/session-[SESSION_DATE].json` using the Write tool.

Output one line after the draft is saved:
`RESEARCH COMPLETE: [SESSION_DATE] | enriched=[count] | tavily=[yes/no] | vault=[available/unavailable] | newyorker=[available/unavailable]`

Set FILE_WRITE_SUCCESS=true if the draft was saved. Set FILE_WRITE_SUCCESS=false only if the draft call failed.

---

## STEP 5 — HANDOFF

No explicit chain call is needed. The `news-jeeves-write` trigger has its own cron (`30 12 * * *` UTC) and will fire 30 minutes after this research run begins. It reads the `🔬 Jeeves Session [SESSION_DATE]` Gmail draft saved in Step 4.

If FILE_WRITE_SUCCESS=false, do nothing — the write phase will detect the missing draft and emit its own failure draft.

---

## TOOL BUDGET

- WebSearch: unlimited (included in session cost)
- tavily_search: max 4 calls (Block D only, if available)
- tavily_research: max 3 calls (Block E only, if available)
- tavily_extract: max 5 calls (Step 3 enrichment + Block F, if available)
- tavily_crawl, tavily_map: do not use
