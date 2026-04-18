# JEEVES DAILY INTELLIGENCE — RESEARCH PHASE 1b (Cloud v2.0)

**TASK:** Research phase 2 of 2. Read partial session JSON from Phase 1a. Run Tavily blocks + enrichment. Save complete session JSON. Chain to write phase immediately.

---

## GITHUB CONFIG

**Repo:** `mmmichaelllang/jeeves-memory`
**Token:** `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`

**Read a file:**
```bash
curl -s -H "Authorization: Bearer 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" \
  "https://api.github.com/repos/mmmichaelllang/jeeves-memory/contents/PATH" \
  -o /tmp/gh_out.json
python3 -c "import json,base64; d=json.load(open('/tmp/gh_out.json')); print(base64.b64decode(d['content']).decode())"
```

---

## STEPS (execute in strict order)

### STEP 0 — READ PARTIAL SESSION JSON

```bash
TODAY=$(date +%Y-%m-%d)
curl -s -H "Authorization: Bearer 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" \
  "https://api.github.com/repos/mmmichaelllang/jeeves-memory/contents/sessions/session-${TODAY}-partial.json" \
  -o /tmp/partial_raw.json
python3 -c "
import json, base64
d = json.load(open('/tmp/partial_raw.json'))
if 'content' not in d:
    print('NOT_FOUND')
else:
    content = json.loads(base64.b64decode(d['content']).decode())
    print(json.dumps(content, indent=2))
"
```

**If output is `NOT_FOUND` or `status != "partial"`:**
Write `{"status":"failed","phase":"1b","date":"[TODAY]","error":"partial session missing or 1a failed"}` to `sessions/session-[TODAY].json` and stop.

Parse from partial JSON:
- `block_a_top_urls[]` — URLs from Phase 1a WebSearch for enrichment
- `newyorker_url_candidate` — NYer article URL to fetch (empty string if none)
- `jina_key` — Jina API key
- All other fields (dedup, correspondence, weather, local_news, career, family, global_news, intellectual_journals, vault_insight) — carry forward into complete session

---

### STEP 1 — TAVILY BLOCKS (run all in parallel)

**Block B — tavily_search (exactly 4):**
1. `"wearable AI pendants pins lifelogging devices"`
2. `"AI tools classroom teacher productivity high school"`
3. `"AI-assisted lesson plans high school English History EdTech"`
4. `"best EdTech resources teachers"`

**Block C — tavily_research (exactly 3):**
1. `"Relational ontologies" "Triadic logic" "Quantum perichoresis" "Non-linear triadic dynamics" "Trinitarianism in contemporary metaphysics"`
2. `"multi-agent research systems" "reasoning models LLM 2026" "autonomous research pipelines" "prompt engineering advances 2026"`
3. `"UAP disclosure 2026" "UAP congressional hearings" "non-human intelligence declassification"`

**Block D — Sector 7 content fetch (only if `newyorker_url_candidate` is non-empty):**

Step 1: Download script from GitHub:
```bash
curl -s -H "Authorization: Bearer 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" \
  "https://api.github.com/repos/mmmichaelllang/jeeves-memory/contents/scripts/sector7-fetch.py" \
  -o /tmp/sector7_raw.json
python3 -c "import json,base64; open('/tmp/sector7-fetch.py','w').write(base64.b64decode(json.load(open('/tmp/sector7_raw.json'))['content']).decode())"
```

Step 2: Run with URL via env var (stdout = JSON result):
```bash
SECTOR7_URL="[newyorker_url_candidate]" python3 /tmp/sector7-fetch.py > /tmp/sector7_result.json 2>/tmp/sector7_err.txt
```

Step 3: Parse result:
```bash
python3 -c "import json; d=json.load(open('/tmp/sector7_result.json')); print(json.dumps(d, indent=2))"
```

If `available=true`: store full result as `sector7` in session JSON. If `available=false` or file missing: set `sector7={"available": false}`.

To update Sector 7 logic: edit `scripts/sector7-fetch.py` in `mmmichaelllang/jeeves-memory`. Script reads URL from `SECTOR7_URL` env var and prints JSON to stdout.

---

### STEP 2 — CONTENT ENRICHMENT

Pick the 5 most novel URLs NOT in `dedup.covered_urls[]` from `block_a_top_urls[]` + Block B results combined. Run `tavily_extract` on those 5 URLs. Store each as `{"url":"...","title":"...","content":"..."}`.

---

### STEP 3 — SAVE COMPLETE SESSION JSON

Merge all data. Save to `sessions/session-[TODAY].json`:

```bash
python3 -c "
import json, base64, urllib.request

TODAY = '$(date +%Y-%m-%d)'
TOKEN = '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'
PATH = f'sessions/session-{TODAY}.json'
URL = f'https://api.github.com/repos/mmmichaelllang/jeeves-memory/contents/{PATH}'

session = {COMPLETE_SESSION_DICT_HERE}

content_b64 = base64.b64encode(json.dumps(session, indent=2, ensure_ascii=False).encode()).decode()
try:
    req = urllib.request.Request(URL, headers={'Authorization': f'Bearer {TOKEN}'})
    with urllib.request.urlopen(req) as r: sha = json.load(r).get('sha', '')
except: sha = ''
body = {'message': f'jeeves 1b complete {TODAY}', 'content': content_b64}
if sha: body['sha'] = sha
req = urllib.request.Request(URL, data=json.dumps(body).encode(),
    headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}, method='PUT')
with urllib.request.urlopen(req) as r:
    print('Session saved:', json.load(r).get('content', {}).get('sha', 'unknown'))
"
```

Replace `{COMPLETE_SESSION_DICT_HERE}` with the actual merged Python dict. Schema:
```json
{
  "status": "complete",
  "date": "YYYY-MM-DD",
  "dedup": { "covered_urls": [], "covered_headlines": [] },
  "correspondence": { "found": false, "fallback_used": false, "text": "" },
  "weather": "",
  "local_news": "",
  "career": "",
  "family": { "choir": "", "toddler": "" },
  "global_news": "",
  "intellectual_journals": "",
  "enriched_articles": [],
  "triadic_ontology": "",
  "ai_systems": "",
  "uap": "",
  "wearable_ai": "",
  "vault_insight": { "available": false, "insight": "", "context": "", "note_path": "", "topic": "" },
  "sector7": { "available": false, "title": "", "text": "", "source": "", "url": "" },
  "search_notes": ""
}
```

If save fails: write `{"status":"failed","phase":"1b","date":"[TODAY]","error":"..."}` to same path.

---

### STEP 4 — DONE

Complete session JSON saved. Stop here. The monitoring session will detect the complete JSON and fire the write phase immediately with a fresh context window.

Do not fetch or execute any more prompts. Your work for Phase 1b is complete.

---

## SEARCH BUDGET
- `tavily_search`: exactly 4 (Block B)
- `tavily_research`: exactly 3 (Block C)
- `tavily_extract`: up to 5 (Block D + Step 2 combined — Jina preferred over extract for New Yorker)
- `tavily_crawl`: 0 / `tavily_map`: 0

---

## BEGIN

Execute Steps 0 through 4 in strict order. Begin now.
