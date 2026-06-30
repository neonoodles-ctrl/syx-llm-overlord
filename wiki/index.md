---
tags:
  - syx
  - wiki
  - moc
---

# Syx LLM Overlord Wiki

Knowledge base for the AI overlord: how it plays, what it remembers, and how the stack fits together.

## Rules & playbooks

- [[rules/playbook|Starter Playbook]] — **source of truth** injected into every LLM tick
- [[modes/teacher|Teacher mode]] — teaches player while playing
- [[modes/civil-flow|Civil Flow State]] — wiki-backed expert autopilot
- [[rules/commands|Command API]] — what actions work vs stubs
- [[rules/rooms|Room types & aliases]] — build targets the mod understands
- [[rules/failures|Failure messages]] — how to read and recover from errors

## Memory system

- [[memory/live-log|Live session log]] — **auto-updated** mirror of JSONL (bridge writes each tick)
- [[memory/overview|Memory overview]] — session log + prompt injection
- [[memory/log-format|JSONL log format]] — file structure and entry kinds
- [[memory/operations|Operations]] — API, dashboard, manual notes

## Architecture

- [[architecture/stack|Stack diagram]] — mod → bridge → LLM → dashboard
- [[architecture/paths|Paths & ports]] — where everything lives on disk

## Research

- [[research/prior-art|Prior art]] — has anyone done this before?

## Project

- [[../project|Project hub]] — status, links, launcher

## Editing rules

When you edit [[rules/playbook]], changes apply on the **next tick** automatically (bridge reads the file each decision). Optional: `POST http://localhost:3847/api/playbook/reload` to verify load.

Memory is **runtime** (JSONL at `logs/overlord-memory.jsonl`). The bridge mirrors the tail into [[memory/live-log]] each tick. Copy durable lessons into [[rules/playbook]] or add manual notes via dashboard / `POST /api/memory`.
