"""Generate one entity YAML per Bay Area event in the trip window,
classified per the user's GTM criteria (see schema x-guidelines)."""
import json, pathlib, re
import yaml

BASE = pathlib.Path(__file__).parent
ENT = BASE / "entities"
ENT.mkdir(exist_ok=True)
win = json.loads((BASE / "sources" / "window.json").read_text())

BAY = {"San Francisco", "Berkeley", "Alameda", "Menlo Park", "Oakland", "Palo Alto",
       "Mountain View", "Santa Clara", "Sunnyvale", "Redwood City", "South San Francisco"}

# Detail patches for entries that hit API rate limits (data captured in the
# first extract run, see sources/window_report.txt / first-run output).
PATCH = {
    "Agentic_AI_10-13": {"calendar_full": "Agentic + AI Observability Meetup", "city": "San Francisco", "keyco_hits": ["openai"], "require_approval": True},
    "aibuilders_techcrunch": {"calendar_full": "Modal", "city": "San Francisco", "keyco_hits": ["modal", "together ai"], "require_approval": True},
    "k8u3voz2": {"calendar_full": "Latent.Space", "city": "Virtual (Zoom)", "require_approval": False},
    "sxoqc4og": {"calendar_full": "The Frontier Syndicate", "city": "San Francisco", "require_approval": True},
}

# slug -> (relevance_category, priority, note)
CLASSIFY = {
    "vastsf": ("ai_infra_compute", "strong", "Full-day real-time video agents hack (VAST Builders Challenge); NVIDIA, W&B/CoreWeave, Modal, xAI infra involved."),
    "supabase-select-2026": ("general_ai", "strong", "Supabase's curated builders conference. Supabase is the default backend of the vibecoding stack (Lovable/v0/Replit apps) - high density of vibecoding-ecosystem people."),
    "the-z3sk": ("general_ai", "skip", "Founder coaching session, not networking-relevant."),
    "the-6cst": ("general_ai", "skip", "Film salon."),
    "the-heo3": ("general_ai", "optional", "SF Commons social; low-key way to meet Commons community."),
    "the-gv3j": ("researchers_safety_rationalist", "strong", "Weekly Sunday staple (user's SF Commons public hours). Oct 11 occurrence not yet published on the calendar - it is weekly, expect it."),
    "the-b0lm": ("general_ai", "skip", "Writing club."),
    "rp6x87x7": ("general_ai", "optional", "Generic Tech Week kickoff mingle."),
    "scorx7qo": ("ai_infra_compute", "strong", "MCP infrastructure talk during Tech Week; agent-infra crowd."),
    "Molecules2Agents": ("general_ai", "optional", "AI-for-science; NVIDIA mentioned but science-domain audience."),
    "szg4hzay": ("gtm_growth", "strong", "YC founders mixer - dense intro-exchange room during Tech Week."),
    "demo-night-oct2026": ("general_ai", "optional", "WorkOS demo night; builder crowd."),
    "Oct-SF-agents-APIs-meetup": ("general_ai", "optional", "Postman agents/APIs meetup."),
    "4xjpmq1m": ("gtm_growth", "optional", "Hustle Fund founder social - SOLD OUT."),
    "copilo-y6wx": ("general_ai", "optional", "CopilotKit agentic-dev-tooling night; vibecoding-adjacent."),
    "4o1slrjc": ("gtm_growth", "optional", "Mercury dinner - SOLD OUT."),
    "ozrtk4ne": ("gtm_growth", "optional", "Founder & investor dinner, approval required."),
    "sergey-spc": ("community_spc", "must_go", "SPC forum with Sergey Levine (Physical Intelligence co-founder). SPC is a key community; senior researcher audience."),
    "ejwagfv9": ("general_ai", "optional", "Solo-founder club session."),
    "sf-tech-week-discord-game-development-meetup": ("general_ai", "skip", "Game-dev Discord meetup."),
    "campai-sftw-2026": ("ai_infra_compute", "strong", "Production-ready agents event (Auth0/Okta); Anthropic referenced in programme."),
    "personadinner": ("gtm_growth", "strong", "Persona-hosted private founder dinner (15 seats, approval). User already has a Persona relationship - warm intro likely."),
    "xenl8z74": ("general_ai", "optional", "Hustle Fund batting-cage social."),
    "4ljpaw1d": ("general_ai", "skip", "Berkeley poetry reading."),
    "mngid6og": ("general_ai", "optional", "AI-for-documentation talk."),
    "wandb-mode": ("key_ai_company", "strong", "W&B/CoreWeave fireside on physical AI in engineering workflows. 8am; location listed as unknown - verify whether in-person before planning."),
    "init-conf": ("target_customer", "must_go", "WorkOS init() builders conference; description references Replit, Anthropic and OpenAI (speaker list still publishing). WorkOS sells enterprise-readiness infra to AI-native cos - your exact buyer ecosystem."),
    "bgrmd42f": ("researchers_safety_rationalist", "optional", "Latent.Space LLM Paper Club - VIRTUAL (Zoom), so limited networking value; join if the paper is relevant."),
    "vmjvw2ox": ("general_ai", "optional", "YC founders picnic."),
    "o2u9s9lr": ("general_ai", "skip", "Design roast - SOLD OUT."),
    "smartleadxpump": ("gtm_growth", "optional", "GTM/outbound topic - SOLD OUT."),
    "tzx7utxg": ("general_ai", "optional", "VC Backed Moms happy hour."),
    "82gz0ggu": ("researchers_safety_rationalist", "strong", "Bay Area Frontier Research Club #26: Agents in Production (OpenAI involvement). User attended #23 - same organiser (The Frontier Syndicate)."),
    "BuildBuyorPartner": ("general_ai", "skip", "Biotech infrastructure panel."),
    "exekfdsk": ("general_ai", "skip", "Human-performance exhibition."),
    "egpwc3ua": ("general_ai", "optional", "Generic pitch night."),
    "kle5wsv0": ("general_ai", "skip", "Electronics manufacturing summit."),
    "nssis": ("general_ai", "optional", "NatSec/space summit (Fleet Week x Tech Week); Cognition and OpenAI mentioned in programme but defense-focused audience."),
    "5p58mktn": ("target_customer", "must_go", "SF's German founders/operators on stage - Sierra and Vercel referenced among speakers; German AI ecosystem is the warm path to Parloa and Legora. SOLD OUT but application-based - apply/chase a ticket."),
    "qzct3ybt": ("general_ai", "optional", "Sales-copilot hackathon."),
    "jszu8o9a": ("general_ai", "optional", "Founder/VC padel night."),
    "workbuddysf": ("general_ai", "optional", "WorkBuddy meetup."),
    "b4sf-02": ("general_ai", "optional", "Large pitch night (Cognition mentioned in description; likely incidental)."),
    "developers-after-dark": ("general_ai", "optional", "WorkOS developers social - good init() follow-on."),
    "j2d9fhek": ("researchers_safety_rationalist", "strong", "AI4Science evening - researcher-heavy room."),
    "fldrgzgq": ("gtm_growth", "strong", "a16z speedrun SR007 masquerade with Mercury & Persona. Cohort event (approval) - use Persona relationship to get in."),
    "the_gtm_afterparty": ("gtm_growth", "strong", "Smartlead GTM afterparty - outbound/GTM operator crowd for intro exchange."),
    "cyberhack": ("general_ai", "optional", "tokens& cyberdefense hackathon (full day)."),
    "3t95uj7s": ("general_ai", "optional", "AI Native Summit (PAI Palooza)."),
    "staaake-203w": ("general_ai", "optional", "Basketball networking for AI founders."),
    "7wn8tsf7": ("ai_infra_compute", "strong", "SF Tech Week Agent Day (Open Source for AI, Menlo Park) - agent-infra developer crowd."),
    "tzyvkp9j": ("general_ai", "optional", "Neighborhood build-a-thon."),
    "smartleadxchatbase": ("gtm_growth", "optional", "Bowling mixer with GTM crowd."),
    "tavily-u13g": ("target_customer", "must_go", "Builders & Brews: Hack Edition - co-hosted by Replit Events (with Tavily, Nebius, Merge). Direct Replit contact in a small-room hack format."),
    "ThePerformanceEconomy": ("general_ai", "skip", "Human-performance capital panel."),
    "g5sdw0b6": ("general_ai", "skip", "Hardware meetup."),
    "fukxek8f": ("general_ai", "optional", "Founders social (evening)."),
    "staaake-mc1x": ("general_ai", "optional", "Boxing intro for founders."),
    "oct10lab": ("ai_infra_compute", "strong", "tokens& production-agent workshop (hands-on, Saturday)."),
    "j34m6r1z": ("general_ai", "optional", "AI-native startup hackathon (weekend)."),
    "mlvc-e0o4": ("general_ai", "optional", "Tech basketball run."),
    "staaake-j15s": ("general_ai", "optional", "Tech Week hangover social."),
    "oct-hackathon": ("general_ai", "optional", "Company-brain agent hackathon (Menlo Park, Monday daytime)."),
    "qo2dliwb": ("general_ai", "optional", "Future-of-work mixer with open demos (Claude mentioned)."),
    "rwhh6mha": ("general_ai", "skip", "DTC focus group."),
    "Agentic_AI_10-13": ("ai_infra_compute", "strong", "Agentic + AI observability meetup during Disrupt week (OpenAI involvement)."),
    "aibuilders_techcrunch": ("key_ai_company", "must_go", "Modal's AI Builder's Night during TechCrunch Disrupt, with Together AI involvement - two key infra companies in one room."),
    "k8u3voz2": ("researchers_safety_rationalist", "optional", "Latent.Space LLM Paper Club - VIRTUAL (Zoom)."),
    "sxoqc4og": ("researchers_safety_rationalist", "strong", "Bay Area Frontier Research Club #27: Embodied AI (dinner). Same organiser as #23 the user attended."),
    "signalfire-arthaus": ("gtm_growth", "strong", "SignalFire's Disrupt after-party - VC/founder density during Disrupt."),
    "nachon-9ui9": ("gtm_growth", "strong", "Disrupt SaaS & AI founder + investor happy hour (NachoNacho)."),
    "lqqg6oue": ("general_ai", "skip", "Book event, Berkeley."),
}

def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")

count = 0
for w in win:
    slug = w["slug"]
    if slug not in CLASSIFY:
        continue  # non-Bay-Area entries are out of scope (see NOTES.md)
    p = PATCH.get(slug, {})
    city = p.get("city", w.get("city"))
    if city == "Unknown" and w.get("calendar") in ("The Commons", "Weights & Biases by CoreWeave", "Latent.Space (Paper Club, AI in Action, Meetups & Confs)"):
        city = {"The Commons": "San Francisco"}.get(w.get("calendar"), "Unknown")
    cat, pri, note = CLASSIFY[slug]
    sold_out = p.get("sold_out", w.get("sold_out"))
    approval = p.get("require_approval", w.get("require_approval"))
    reg = "sold_out" if sold_out else ("waitlist_or_approval" if approval else ("open" if approval is not None else "Unknown"))
    companies = sorted(set((w.get("target_hits") or []) + (w.get("keyco_hits") or []) + p.get("keyco_hits", [])))
    ent = {
        "_meta": {
            "last_researched": "2026-09-16",
            "sources": [{"publisher": "Luma (api.lu.ma)", "url": f"https://luma.com/{slug}", "retrieved": "2026-09-16"}],
        },
        "name": w["name"],
        "url": f"https://luma.com/{slug}",
        "platform": "luma",
        "start_date": w["date"],
        "start_time": w["time"],
        "city": city or "Unknown",
        "host_calendar": p.get("calendar_full") or w.get("calendar_full") or w.get("calendar") or "Unknown",
        "hosts": w.get("hosts") or "Unknown",
        "companies_involved": companies or [],
        "relevance_category": cat,
        "priority": pri,
        "registration_status": reg,
        "in_trip_window": True,
        "description_snippet": (w.get("desc_first400") or "Unknown")[:300],
        "note": note,
    }
    fn = ENT / f"{w['date']}-{slugify(slug)}.yaml"
    fn.write_text(yaml.safe_dump(ent, sort_keys=False, allow_unicode=True, width=100))
    count += 1

# --- manual anchor + recurring entities (non-Luma or not yet published) -----
manual = [
    {
        "_meta": {"last_researched": "2026-09-16", "sources": [
            {"publisher": "TechCrunch", "url": "https://techcrunch.com/events/techcrunch-disrupt/", "retrieved": "2026-09-16"},
            {"publisher": "Moscone Center", "url": "https://www.moscone.com/events/techcrunch-disrupt-2026", "retrieved": "2026-09-16"}]},
        "name": "TechCrunch Disrupt 2026",
        "url": "https://techcrunch.com/events/techcrunch-disrupt/",
        "platform": "other",
        "start_date": "2026-10-13", "start_time": "07:30", "end_date": "2026-10-15",
        "city": "San Francisco", "venue": "Moscone West",
        "host_calendar": "TechCrunch",
        "hosts": ["TechCrunch"],
        "companies_involved": ["Replit (CEO Amjad Masad)", "Lovable (GTM lead Ben Broca)", "Anthropic (Cat de Jong)", "OpenAI (Tara Seshan)", "NVIDIA (Les Karpas)"],
        "relevance_category": "mega_conference",
        "priority": "must_go",
        "registration_status": "open",
        "in_trip_window": True,
        "description_snippet": "3-day startup conference at Moscone West. Attendee pass $849. Early badge pickup Oct 12, 1-5pm.",
        "note": "Everyone-is-there anchor like Dreamforce. Speakers include two target customers (Replit CEO, Lovable GTM lead) plus Anthropic/OpenAI leadership - book sessions and side events around it.",
    },
    {
        "_meta": {"last_researched": "2026-09-16", "sources": [
            {"publisher": "a16z Tech Week", "url": "https://www.tech-week.com/", "retrieved": "2026-09-16"},
            {"publisher": "Luma", "url": "https://luma.com/sftw", "retrieved": "2026-09-16"}]},
        "name": "SF Tech Week 2026 (a16z) - umbrella",
        "url": "https://www.tech-week.com/",
        "platform": "other",
        "start_date": "2026-10-05", "start_time": "Unknown", "end_date": "2026-10-11",
        "city": "San Francisco",
        "host_calendar": "a16z Tech Week",
        "hosts": ["a16z"],
        "companies_involved": [],
        "relevance_category": "mega_conference",
        "priority": "must_go",
        "registration_status": "open",
        "in_trip_window": True,
        "description_snippet": "Decentralized city-wide festival, hundreds of independently hosted events Oct 5-11. Official Luma calendar (luma.com/sftw) is live with ~48 events and growing weekly.",
        "note": "Anchor week 1 of the trip around this. Re-check luma.com/sftw and tech-week.com weekly - most events publish in the final 3 weeks.",
    },
    {
        "_meta": {"last_researched": "2026-09-16", "sources": [
            {"publisher": "User's September list (weekly recurring)", "url": "Unknown", "retrieved": "2026-09-16"}]},
        "name": "Constellation happy hour (AI safety community)",
        "url": "Unknown",
        "platform": "other",
        "start_date": "2026-10-08", "start_time": "Unknown",
        "city": "Berkeley",
        "host_calendar": "Constellation",
        "hosts": ["Constellation"],
        "companies_involved": [],
        "relevance_category": "researchers_safety_rationalist",
        "priority": "strong",
        "registration_status": "invite_only",
        "in_trip_window": True,
        "description_snippet": "Weekly Thursday happy hour at Constellation (AI safety research center). Expect Oct 8 and Oct 15 during the trip.",
        "note": "No public listing; entry via safety-community contacts. Back door to senior LLM/safety people per user's strategy.",
    },
    {
        "_meta": {"last_researched": "2026-09-16", "sources": [
            {"publisher": "Partiful", "url": "https://partiful.com/e/h8vMdhfYda2NIQqSnz8n", "retrieved": "2026-09-16"}]},
        "name": "Litter picking with rationalists (weekly Sunday)",
        "url": "https://partiful.com/e/h8vMdhfYda2NIQqSnz8n",
        "platform": "partiful",
        "start_date": "2026-10-04", "start_time": "09:30",
        "city": "San Francisco",
        "host_calendar": "Rationalist community (Partiful)",
        "hosts": "Unknown",
        "companies_involved": [],
        "relevance_category": "researchers_safety_rationalist",
        "priority": "strong",
        "registration_status": "Unknown",
        "in_trip_window": True,
        "description_snippet": "Weekly Sunday morning stroll ending at Manny's. Expect Oct 4 and Oct 11 occurrences.",
        "note": "The linked Partiful page is a stale past occurrence - each week gets a fresh link shared in the community. Rationalist crowd = user's researcher back door.",
    },
    {
        "_meta": {"last_researched": "2026-09-16", "sources": [
            {"publisher": "Partiful", "url": "https://partiful.com/e/wfMPN5nyulhzciyAmqQC", "retrieved": "2026-09-16"}]},
        "name": "Taco Tuesdays (Mox community, weekly)",
        "url": "https://partiful.com/e/wfMPN5nyulhzciyAmqQC",
        "platform": "partiful",
        "start_date": "2026-10-06", "start_time": "18:30",
        "city": "San Francisco",
        "host_calendar": "Mox community (Partiful)",
        "hosts": "Unknown",
        "companies_involved": [],
        "relevance_category": "researchers_safety_rationalist",
        "priority": "strong",
        "registration_status": "Unknown",
        "in_trip_window": True,
        "description_snippet": "Weekly Tuesday tacos with the Mox (rationalist/EA coworking) crowd. Expect Oct 6 and Oct 13 occurrences.",
        "note": "Linked Partiful page is a stale past occurrence - fresh link is shared weekly in the community.",
    },
]
for m in manual:
    fn = ENT / f"{m['start_date']}-{slugify(m['name'])[:50]}.yaml"
    fn.write_text(yaml.safe_dump(m, sort_keys=False, allow_unicode=True, width=100))
    count += 1

print(f"wrote {count} entity files to {ENT}")
