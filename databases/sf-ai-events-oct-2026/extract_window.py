"""Filter collected entries to 2026-10-02..2026-10-16 (America/Los_Angeles),
fetch full event details for each, and save a normalised window.json."""
import json, time, urllib.request, pathlib
from datetime import datetime
from zoneinfo import ZoneInfo

SRC = pathlib.Path(__file__).parent / "sources"
LA = ZoneInfo("America/Los_Angeles")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept": "application/json"}

TARGETS = ["sierra","decagon","elevenlabs","eleven labs","parloa","harvey","legora",
           "lovable","replit","cognition","vercel","v0 "]
KEY_COS = ["baseten","nvidia","sglang","fireworks","together ai","anthropic","openai",
           "open ai","liquid","gradient","grok","xai","coreweave","weights & biases",
           "wandb","mercor","claude","gemini","gpt","deepmind","mistral","modal"]

def jget(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())

def la_local(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(LA)
    return dt

all_entries = json.loads((SRC / "all_entries.json").read_text())
window = []
for e in all_entries.values():
    ev = e.get("event") or {}
    start = ev.get("start_at")
    if not start:
        continue
    local = la_local(start)
    day = local.strftime("%Y-%m-%d")
    if not ("2026-10-02" <= day <= "2026-10-16"):
        continue
    geo = ev.get("geo_address_info") or {}
    window.append({
        "api_id": ev["api_id"],
        "name": ev.get("name"),
        "slug": ev.get("url"),
        "date": day,
        "dow": local.strftime("%a"),
        "time": local.strftime("%H:%M"),
        "end_at": ev.get("end_at"),
        "city": geo.get("city") or geo.get("city_state") or "Unknown",
        "calendar": e.get("_source_calendar") or (e.get("calendar") or {}).get("name") or "Unknown",
        "waitlist": ev.get("waitlist_status") or e.get("waitlist_active"),
        "location_type": ev.get("location_type"),
    })

window.sort(key=lambda x: (x["date"], x["time"]))
print(f"{len(window)} events in window before detail fetch\n")

# fetch details: description, hosts, registration status, target/key-co mentions
for w in window:
    try:
        d = jget(f"https://api.lu.ma/url?url={w['slug']}")
        data = d.get("data") or {}
        desc = (data.get("description_mirror") and json.dumps(data["description_mirror"])) or ""
        w["hosts"] = [h.get("name") for h in (data.get("hosts") or [])]
        w["calendar_full"] = ((data.get("calendar") or {}).get("name")) or w["calendar"]
        ticket = data.get("ticket_info") or {}
        w["sold_out"] = ticket.get("is_sold_out")
        w["require_approval"] = ticket.get("require_approval")
        ev2 = data.get("event") or {}
        geo2 = ev2.get("geo_address_info") or {}
        if w["city"] == "Unknown":
            w["city"] = geo2.get("city") or geo2.get("city_state") or "Unknown"
        blob = (w["name"] + " " + desc + " " + " ".join(str(h) for h in w["hosts"])).lower()
        w["target_hits"] = sorted({t.strip() for t in TARGETS if t in blob})
        w["keyco_hits"] = sorted({k.strip() for k in KEY_COS if k in blob})
        w["desc_first400"] = "".join(
            t.get("text", "") for blk in (data.get("description_mirror") or {}).get("content", [])
            for t in (blk.get("content") or []) if isinstance(t, dict)
        )[:400]
    except Exception as ex:
        w["detail_error"] = str(ex)
    time.sleep(0.3)

(SRC / "window.json").write_text(json.dumps(window, indent=1))
for w in window:
    flags = []
    if w.get("target_hits"): flags.append("TARGET:" + ",".join(w["target_hits"]))
    if w.get("keyco_hits"): flags.append("KEY:" + ",".join(w["keyco_hits"]))
    if w.get("sold_out"): flags.append("SOLD_OUT")
    if w.get("require_approval"): flags.append("APPROVAL")
    print(f"{w['date']} {w['dow']} {w['time']} | {w['city'][:13]:13} | {(w.get('calendar_full') or '')[:22]:22} | {w['name'][:60]:60} | {w['slug']} | {' '.join(flags)}")
