# GitHub — private repo setup

Target: **https://github.com/neonoodles-ctrl/syx-llm-overlord** (private until Ivan reviews).

---

## Before first push

1. Ensure secrets are **not** committed:
   - `bridge/config.yaml` (gitignored)
   - `.env` (gitignored)
   - `logs/` (gitignored)
2. Review diff: `git status` / `git diff`
3. Confirm `wiki/memory/live-log.md` is gitignored (auto-generated)

---

## Create private repo (one time)

From the project root:

```bash
cd "/home/hermesprime/CODE/Boiler Room/_current/syx-llm-overlord"

git remote remove origin 2>/dev/null || true
git remote add origin git@github.com:neonoodles-ctrl/syx-llm-overlord.git

gh repo create neonoodles-ctrl/syx-llm-overlord \
  --private \
  --source=. \
  --remote=origin \
  --description "LLM plays Songs of Syx — Java mod + Python bridge + dashboard"
```

If the repo already exists:

```bash
git push -u origin main
```

---

## When ready to go public

```bash
gh repo edit neonoodles-ctrl/syx-llm-overlord --visibility public
```

Add topics: `songs-of-syx`, `llm`, `game-ai`, `ollama`, `openrouter`, `modding`

---

## Clone instructions (for others)

```bash
git clone git@github.com:neonoodles-ctrl/syx-llm-overlord.git
cd syx-llm-overlord
cp .env.example .env
./install.sh
./run.sh
```

They need their own Songs of Syx purchase and `SongsOfSyx.jar` on disk.

---

## CI (future)

Mod build CI is awkward because `SongsOfSyx.jar` is commercial. Options:

- Document manual build only (current)
- Optional: CI builds bridge Python tests with mocked game client
- Do not redistribute the game JAR
