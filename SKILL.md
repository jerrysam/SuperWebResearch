---
name: SuperWebResearch
description: When doing online research tasks with structured data, where we need to compare many entities, add new columns/fields derived from the raw data, gather information from multiple sources, store (and classify) the entities consistently, use this skill to create a yaml schema to populate for all entities then filter + load into context to give a better answer.

---



# How to research with human-level intelligence

## Hard rules (non-negotiable)

- Do NOT answer the user's question from ad-hoc web searches or by reading individual pages. The answer must come from filtering the entity YAML library you build.
- Do NOT run any entity research until the topic directory and `schema/entity.schema.yaml` exist in the research-databases repo. Schema first, always.
- Search engines are for discovering data sources only, never for enumerating entities. Enumerate entities by scripted retrieval from the sources themselves (internal JSON APIs, listing pages, scraping) so coverage is complete, not whatever a search index surfaced.
- If you catch yourself clicking through result pages one by one, stop: that is the failure mode this skill exists to prevent.

Before starting, clone this repo as your 'database', and just check that the same query hasn't been researched already. If so, still create a fresh folder, copy the schema, and re-generate the individual entities for freshness.

First, identify some of the main data sources for the users query. For property listings in London, maybe Rightmove and OnTheMarket (which you can spoof the browser headers of to get thier internal JSON api) and SpareRoom and Zoopla (which you can browse with Daytona web research agents).

Using a few example entities, identify the unified schema that matches all sources. Build a .yaml schema that outlines the consistent format and data you need to gather from each entity as part of answering the users query. For example, for a property query, the property sites all have price, rooms, etc.
Also add research provenance (sources at the yaml file level, date researched, etc)

Then, figure out what derived entities are needed for answering the user queries (these fields are query-shaped, NOT source-shaped). For example, if they want the price per room between £500 - £1000, then you need to derive price per room carefully for each entity, as a new column that you can later query and sort over. Another example might be house type (warehouse conversion, council house, new build, etc), which you can't tell from descriptions consistently so you have to look at the photos themselves (which can be expensive so perhaps filter what you can first).
If you need to define any guidelines (e.g. all prices should be monthly, normalise price per week to monthly), use a description field to add those in the schema too. 

Then, get all entities (download raw data/file), and start outputting a valid .yaml file for each entity, building up your library. Once complete, you will be able to load and sort/filter to get the most relevant information to present to the user.


All research output lives in the dedicated repo https://github.com/jerrysam/research-databases — clone it (or pull if already cloned), create/reuse a topic directory at its root per the README, do all work there, and commit + push when done.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Clone/pull the research-databases repo and create the topic directory
- [ ] Step 2: Identify sources and unify key fields to generate schema (GATE: no entity research until the schema file is committed)
- [ ] Step 3: Add derivative fields matching the user query to the schema, and ensure it's correct for the final research loop
- [ ] Step 4: Research loop — populate one YAML per entity
- [ ] Step 5: Filter with a script and present best answers
```

## Deep research with Daytona sandboxes

For heavy scraping (many pages, JS-rendered sites, or when local network access is blocked), run the research loop inside a Daytona sandbox instead of locally:

1. Use the Daytona CLI only (do not use Daytona MCP tools even if present): `daytona sandbox create` to provision, `daytona exec` to run commands (requires `daytona login` or `DAYTONA_API_KEY`).
2. In the sandbox: install Python + `requests`, `beautifulsoup4`, `pyyaml` (add `playwright` only if pages need JS rendering), run the scraping script there, writing entity YAML files inside the sandbox.
3. Download the resulting `entities/*.yaml` back into the topic directory in the research-databases repo, then destroy the sandbox.
4. If Daytona is unavailable (no CLI, no MCP tools, no API key), do the research locally and note the limitation to the user.

## Conventions

- All YAML lives in the topic directory inside the `research-databases` repo (see above), never in the current project's workspace.
- Slugs: lowercase, hyphenated, from stable identifying fields (e.g. for a property, address + postcode: `12-acacia-ave-n4-2ab.yaml`).
- Never fabricate entity data; missing = `Unknown`.
- Respect rate limits: stagger requests, stop and tell the user if blocked.
