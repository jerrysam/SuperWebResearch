"""Paginate the SF discover feed until events pass 2026-10-17, merging into all_entries.json."""
import json, time, urllib.request, pathlib

SRC = pathlib.Path(__file__).parent / "sources"
PID = "discplace-BDj7GNbGlsF7Cka"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept": "application/json"}

def jget(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())

all_entries = json.loads((SRC / "all_entries.json").read_text())
cursor = json.loads((SRC / f"discover-{PID}.json").read_text()).get("next_cursor")

pages = 0
last_date = ""
while cursor and pages < 40:
    d = jget(f"https://api.lu.ma/discover/get-paginated-events?discover_place_api_id={PID}&pagination_limit=100&pagination_cursor={urllib.parse.quote(cursor)}")
    pages += 1
    entries = d.get("entries", [])
    (SRC / f"discover-{PID}-page{pages+1}.json").write_text(json.dumps(d, indent=1))
    for e in entries:
        ev = e.get("event") or {}
        if ev.get("api_id") and ev["api_id"] not in all_entries:
            e["_source_calendar"] = "(discover-sf-ai)"
            all_entries[ev["api_id"]] = e
    if entries:
        last_date = (entries[-1]["event"].get("start_at") or "")[:10]
    print(f"page {pages+1}: {len(entries)} events, up to {last_date}")
    cursor = d.get("next_cursor") if d.get("has_more") else None
    if last_date > "2026-10-17":
        break
    time.sleep(0.4)

(SRC / "all_entries.json").write_text(json.dumps(all_entries, indent=1))
print(f"TOTAL unique events now: {len(all_entries)}")
