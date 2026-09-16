# sf-ai-events-oct-2026

**Query:** Build an SF Bay Area event calendar for a GTM trip Oct 2-16 2026, selling a
post-training / AI research product. Selection criteria from the user: growth/GTM
intro-exchange events; AI infra/compute with big companies; events by key AI companies
(Baseten, NVIDIA, SGLang, Fireworks, Together AI, Anthropic, OpenAI, Liquid, Gradient,
Grok/xAI, CoreWeave, Mercor); researcher/rationalist/EA/safety community events; senior
eng-leader events; corp-dev content; SPC; mega-conferences. Target customers (Customer
Success / Law / Vibecoding): Sierra, Decagon, ElevenLabs, Parloa, Harvey, Legora,
Lovable, Replit, Cognition, Vercel v0.

## Sources (enumerated by script, 2026-09-16)

- `api.lu.ma/url` + `api.lu.ma/calendar/get-items` over 52 calendars: every calendar
  behind the user's September list, plus company calendars (Baseten, NVIDIA, Anthropic,
  OpenAI, Fireworks, Together AI, Mercor, SGLang, Modal, W&B/CoreWeave, ElevenLabs,
  Harvey, Legora, Lovable, Cognition, Vercel, Conviction, SPC, Latent.Space, etc.),
  plus the SF Tech Week calendar (`luma.com/sftw`, cal-bR2dxhC1V6wCtK8).
- Luma SF discover feed (discplace-BDj7GNbGlsF7Cka), paginated to Oct 17.
- Web search only to confirm SF Tech Week (Oct 5-11) and TechCrunch Disrupt
  (Oct 13-15, Moscone West) dates.
- Partiful pages for the two recurring community events (stale single-occurrence pages;
  recorded as weekly recurring).

## Decisions / caveats

- Scope: Bay Area only. ~35 in-window events from tracked calendars were excluded as
  out-of-area (NYC, London, Paris, Berlin, Barcelona, Stockholm) - NVIDIA, Fireworks,
  Arize, Fin, W&B and Brderless all run non-SF events during this window.
- SF Tech Week calendar had 48 events on research date and grows weekly; most Tech Week
  events publish in the final 3 weeks. Re-run `fetch_luma.py` + `fetch_discover_pages.py`
  + `extract_window.py` + `gen_entities.py` near the trip for a refresh.
- Anthropic, OpenAI, Grok/xAI, Baseten, Mercor, ElevenLabs, Harvey, Legora, Lovable,
  Cognition, Vercel, SGLang, Gradient calendars had zero published Bay Area events in
  the window on research date. Sierra, Decagon, Parloa, Replit have no public Luma
  calendars; target-customer coverage instead comes from events they co-host/speak at
  (Builders & Brews w/ Replit Events; init() by WorkOS; Germany at the Frontier;
  TechCrunch Disrupt speakers incl. Replit CEO + Lovable GTM lead).
- Weekly recurring events (Commons public hours, litter picking, Taco Tuesdays,
  Constellation happy hour) only have their next occurrence (or none) published;
  entities carry the expected occurrence pattern in `note`.
- 5 event detail fetches were rate-limited (HTTP 429); data patched from the first
  extraction run's output (see PATCH in gen_entities.py).
- LA Tech Week is Oct 12-18, directly after SF - not researched (user is SF-based for
  this trip) but worth knowing.

## Files

- `fetch_luma.py` - enumerate calendars + discover feed -> sources/all_entries.json
- `fetch_discover_pages.py` - paginate discover feed through the window
- `extract_window.py` - filter to Oct 2-16 LA time + fetch per-event details -> sources/window.json
- `gen_entities.py` - classify (per schema x-guidelines) and emit entities/*.yaml
- `filter_calendar.py` - load entities, drop skips, print the day-by-day calendar
