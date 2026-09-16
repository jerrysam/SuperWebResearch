"""Load entity library, drop skips, and print the day-by-day trip calendar."""
import pathlib, yaml
from datetime import date

ENT = pathlib.Path(__file__).parent / "entities"
PRI = {"must_go": 0, "strong": 1, "optional": 2}
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

events = []
for f in sorted(ENT.glob("*.yaml")):
    e = yaml.safe_load(f.read_text())
    if e["priority"] == "skip":
        continue
    events.append(e)

events.sort(key=lambda e: (e["start_date"], PRI[e["priority"]], e.get("start_time") or "99"))

by_day = {}
for e in events:
    by_day.setdefault(e["start_date"], []).append(e)

for day in sorted(by_day):
    y, m, d = map(int, day.split("-"))
    print(f"\n=== {DOW[date(y, m, d).weekday()]} {day} ===")
    for e in by_day[day]:
        t = e.get("start_time") or "?"
        end = f" (until {e['end_date']})" if e.get("end_date") else ""
        reg = {"sold_out": " [SOLD OUT]", "waitlist_or_approval": " [approval]", "invite_only": " [invite only]"}.get(e["registration_status"], "")
        print(f"  {e['priority'].upper():8} {t:>7}  {e['name']}{end}{reg}")
        print(f"           {e['relevance_category']} | {e['url']}")

counts = {}
for e in events:
    counts[e["priority"]] = counts.get(e["priority"], 0) + 1
print(f"\nTotals: {counts}")
