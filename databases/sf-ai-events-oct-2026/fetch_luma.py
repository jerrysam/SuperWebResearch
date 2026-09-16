"""Enumerate Luma events for the Oct 2-16 2026 SF trip.

Sources:
1. Calendars behind every event in the user's September list (resolved from event slugs).
2. Calendar slugs for key AI companies and target customers.
3. Luma discover feed for SF (place feed used by luma.com/discover/sf).

Raw responses are saved under sources/ for provenance.
"""
import json, re, time, urllib.request, urllib.error, pathlib

OUT = pathlib.Path(__file__).parent / "sources"
OUT.mkdir(exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept": "application/json, text/html"}

def get(url, retries=2):
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 301, 302):
                raise
            if i == retries:
                raise
            time.sleep(1.5)
        except Exception:
            if i == retries:
                raise
            time.sleep(1.5)

def jget(url):
    return json.loads(get(url))

# --- 1. calendars from the user's September event list ---------------------
sept_event_slugs = [
    "dd9d1bi8","119fmn5v","the-corgi-cup","BaseDynSGL","islaag11","ra1q3wlf","78cmw2ie",
    "nouxt95e","coreweavehacks","openmodelhack","the-ziz0","fin-dreamforce","spacexai-n2o0",
    "gl1gg0je","5u22it9b","spcforummercor9-16","wgvn22n1","enrich-15lm","7djqpn9h","tejas-rf5u",
    "uaz58gf8","tewv4rbz","bpk7tj30","baseten-f66n","personabianchi","n3go0vqi","zba4aoe2","geminimeetup",
]

# --- 2. candidate calendar slugs (key AI companies + target customers) -----
candidate_calendar_slugs = [
    "baseten","nvidia","anthropic-events","anthropic","openai","openaievents","fireworksai",
    "fireworks-ai","togetherai","together-ai","liquidai","liquid-ai","gradient","xai","grok",
    "coreweave","wandb","mercor","mercor-events","sglang","lmsys","modal","modal-labs",
    "sierra","sierra-ai","decagon","decagonai","elevenlabs","parloa","harvey","harveyai",
    "legora","lovable","lovable-events","replit","cognition","cognition-ai","cognitionai",
    "vercel","v0","spc","southparkcommons","south-park-commons","conviction","arize","arize-ai",
    "ls",  # Latent Space (paper club)
]

calendars = {}   # api_id -> {name, slug}

def note_calendar(cal):
    if cal and cal.get("api_id"):
        calendars[cal["api_id"]] = {"name": cal.get("name"), "slug": cal.get("slug")}

resolved = {}
for slug in sept_event_slugs + candidate_calendar_slugs:
    try:
        d = jget(f"https://api.lu.ma/url?url={slug}")
    except Exception as e:
        resolved[slug] = f"ERROR {e}"
        continue
    kind = d.get("kind")
    resolved[slug] = kind
    if kind == "calendar":
        cal = (d.get("data") or {})
        cal = cal.get("calendar") or cal
        note_calendar(cal)
    elif kind == "event":
        note_calendar(d["data"].get("calendar"))
    time.sleep(0.25)

(OUT / "resolved_slugs.json").write_text(json.dumps(resolved, indent=1))
print(f"resolved {len(resolved)} slugs -> {len(calendars)} unique calendars")
for k, v in sorted(calendars.items(), key=lambda x: (x[1]["name"] or "")):
    print(f"  {k}  {v['name']}  (slug={v['slug']})")

# --- 3. upcoming events per calendar ---------------------------------------
all_entries = {}
for api_id, meta in calendars.items():
    try:
        d = jget(f"https://api.lu.ma/calendar/get-items?calendar_api_id={api_id}&period=future&pagination_limit=50")
    except Exception as e:
        print(f"get-items FAILED for {meta['name']}: {e}")
        continue
    entries = d.get("entries", [])
    (OUT / f"calendar-{api_id}.json").write_text(json.dumps(d, indent=1))
    for e in entries:
        ev = e.get("event") or {}
        if ev.get("api_id"):
            e["_source_calendar"] = meta["name"]
            all_entries[ev["api_id"]] = e
    print(f"{meta['name']}: {len(entries)} future events")
    time.sleep(0.25)

# --- 4. discover feed for SF ------------------------------------------------
try:
    html = get("https://luma.com/discover/sf/ai")
    place_ids = sorted(set(re.findall(r"discplace-[A-Za-z0-9]+", html)))
    print("\ndiscover place ids found:", place_ids)
    for pid in place_ids[:3]:
        try:
            d = jget(f"https://api.lu.ma/discover/get-paginated-events?discover_place_api_id={pid}&pagination_limit=100")
            (OUT / f"discover-{pid}.json").write_text(json.dumps(d, indent=1))
            entries = d.get("entries", [])
            print(f"discover {pid}: {len(entries)} events")
            for e in entries:
                ev = e.get("event") or {}
                if ev.get("api_id") and ev["api_id"] not in all_entries:
                    e["_source_calendar"] = "(discover-sf-ai)"
                    all_entries[ev["api_id"]] = e
        except Exception as ex:
            print(f"discover {pid} FAILED: {ex}")
        time.sleep(0.3)
except Exception as ex:
    print("discover page FAILED:", ex)

(OUT / "all_entries.json").write_text(json.dumps(all_entries, indent=1))
print(f"\nTOTAL unique future events collected: {len(all_entries)}")
