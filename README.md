# research-databases

A store of structured research databases produced by LLM web-research runs.
Each research topic lives in its own sibling directory at the repo root.

## Layout

```
research-databases/
  london-flats-aug-2026/          # one directory per research topic
    schema/
      entity.schema.yaml          # JSON Schema (in YAML), incl. x-guidelines
    entities/
      <slug>.yaml                 # one file per entity
    sources/                      # optional raw fetched material (markdown)
      <slug>/
        2026-08-30-rightmove.md
    NOTES.md                      # topic-level notes: query, decisions, caveats
  <another-topic>/
    ...
```

## Conventions

- Topic directory names: lowercase, hyphenated, include a date if the research
  is time-sensitive (e.g. `london-flats-aug-2026`).
- One YAML file per entity; slugs are lowercase and hyphenated.
- Every entity carries `_meta` with `last_researched` and `sources`.
- Schemas include an `x-guidelines` block with classification rules.
- Missing data is recorded as `Unknown`, never fabricated.
- Commit after every research run with a message like
  `topic: london-flats-aug-2026 — researched 42 entities`.
