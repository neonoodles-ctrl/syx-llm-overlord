# Staging game lab — scope

**Goal:** AI agents run Syx LLM Overlord **E2E on staging** (`10.0.10.202`), never launching the game on Ivan’s CachyOS desktop (`:0`).

**Date:** 2026-07-07  
**Repo:** `/home/hermesprime/CODE/Boiler Room/_current/syx-llm-overlord`

---

## Current state (audited)

| Item | Staging `10.0.10.202` | CachyOS (live play) |
|------|------------------------|---------------------|
| OS | Ubuntu 24.04, 4 vCPU, 8 GB RAM, **28 GB free** | — |
| GPU | VirtIO Mesa (`/dev/dri/card1`), **no NVIDIA** | Desktop GPU |
| DISPLAY | unset over SSH | `:0` KDE |
| Steam | **installed** (`/usr/games/steam`), `~/.steam` present | Ivan library |
| Java | **OpenJDK 21** | yes |
| Xvfb | **installed** | n/a |
| Songs of Syx | **not installed** | Demo ~416 MB, `V69` |
| syx-llm-overlord | rsync’d to `~/projects/syx-llm-overlord`, bridge **:3847 up** | main dev |
| NewAPI / Gemini | **not reachable** from staging (new-api on Cachy `127.0.0.1:3100` only) | works |
| Agent rule | `the workspace agent rules` + `SYX_DISABLE_GAME_LAUNCH=1` | Ivan play |

---

## Architecture (target)

```
┌─────────────────────┐     rsync      ┌──────────────────────────────┐
│ CachyOS (Ivan)      │ ─────────────► │ Staging VM 10.0.10.202       │
│ - play / saves      │                │ - Xvfb :99 (no KDE popups)   │
│ - bridge optional   │                │ - Steam + Syx Demo           │
│ - new-api (move LAN)│ ◄── HTTP ──── │ - mod :47823                 │
└─────────────────────┘                │ - bridge :3847               │
         │                             │ - agent verify + E2E         │
         │  NEWAPI @ 10.0.10.151:3100  └──────────────────────────────┘
         └──────────────────────────────────────────────►
```

**Principle:** Game process + virtual framebuffer live **only on staging**. CachyOS agents: pytest, bridge curl, dashboard vision — **no** `POST /api/restart`, no Steam, no `DISPLAY=:0`.

---

## Phases

### Phase 0 — LAN LLM gateway (blocker, ~1 slice)

**Why:** Staging cannot use `127.0.0.1:3100` on Cachy.

| Task | Owner | Done when |
|------|-------|-----------|
| Bind new-api on Unraid or dedicated host to `10.0.10.151:3100` (LAN, not `0.0.0.0` public) | Ivan / infra | `curl http://10.0.10.151:3100/v1/models` from staging returns gemini models |
| Firewall: allow `10.0.10.0/24` → `:3100` only | Ivan | staging curl works; WAN blocked |
| Document `SYX_LLM_BASE_URL=http://10.0.10.151:3100/v1` | builder | in this doc + `config.example.yaml` note |

**Do not** rsync `NEWAPI_API_KEY` with the repo. One-time on staging:

```bash
# on 10.0.10.202 only — Ivan or agent after approval
echo 'NEWAPI_API_KEY=…' >> ~/.hermes/.env
```

---

### Phase 1 — Spike: Syx on Xvfb (go/no-go, ~½ day)

**Risk:** Syx is OpenGL/Java; software rendering on a VM may fail or be unusably slow.

| Step | Command / check |
|------|-----------------|
| Install Syx Demo on staging (see Phase 2) | `SongsOfSyx.jar` exists |
| `Xvfb :99 -screen 0 1920x1080x24` + `DISPLAY=:99` | X server up |
| Launch `java -jar SongsOfSyx.jar` or `LinuxNvidiaFix.sh` | process stays up ≥60s |
| Enable mod, new game | `curl http://127.0.0.1:47823/api/health` or bridge `game_connected: true` |

**Go:** mod API responds on staging without Ivan’s monitor.  
**No-go:** document “staging = bridge-only CI”; game E2E stays Ivan-manual + screen recording.

---

### Phase 2 — Steam + game install on staging (Ivan-once, ~30–60 min)

Steam is already on the VM; **Syx is not**.

| Option | Pros | Cons |
|--------|------|------|
| **A. Steam GUI via SSH X11 forward** | Official install, updates | Needs one interactive session; slow over SSH |
| **B. Steam remote desktop / VNC to staging** | Easier GUI | Extra setup |
| **C. Rsync game tree from Cachy** | Fast spike | Version drift; license/update path unclear; use only for dev spike |
| **D. steamcmd + App 1162750** | Scriptable | Steam Guard, beta/demo ID, headless quirks |

**Recommended:** **A or D** for a proper lab; **C** only for Phase 1 spike if Steam login blocks.

After install:

- `SONGSOFSYX_JAR` / `SONGSOFSYX_DIR` in `~/projects/syx-llm-overlord/.env` on staging
- `./install.sh` on staging → mod JAR under `~/.local/share/songsofsyx/mods/syx-llm-overlord/<version>/`

**Disk budget:** game ~0.5 GB + Steam + Java + bridge venv + playwright ≈ **2–4 GB** (fits in 28 GB free).

---

### Phase 3 — Staging launcher scripts (builder slice)

Add **`scripts/staging-game-lab.sh`** (repo):

```bash
# Intended usage on 10.0.10.202 only
export DISPLAY=:99
export SYX_DISABLE_GAME_LAUNCH=0          # agents MAY restart game HERE
export SYX_LLM_BASE_URL=http://10.0.10.151:3100/v1
export SYX_OVERLORD_ROOT=~/projects/syx-llm-overlord

start-xvfb()   # idempotent Xvfb :99
start-bridge()
start-game()   # portable restart-game-only, DISPLAY=:99
wait-mod-api() # poll :47823
full-smoke()   # health + game_connected + one /api/instruct
```

**Never** call this script from CachyOS agent sessions (rule enforces).

Add **`scripts/staging-verify-full.sh`** — invoked via SSH from builder:

1. `staging_deploy` rsync
2. pytest + mvn on VM
3. `staging-game-lab.sh full-smoke`
4. write `output/handoff/verify-slice-N-staging-e2e.json`

---

### Phase 4 — Bridge config per environment

| Env var | CachyOS (agents) | Staging |
|---------|------------------|---------|
| `SYX_DISABLE_GAME_LAUNCH` | `1` | `0` |
| `SYX_LLM_BASE_URL` | `http://10.0.10.151:3100/v1` (after Phase 0) | same |
| `SYX_BRIDGE_PORT` | `3847` | `3847` |
| `DISPLAY` | unset / do not launch | `:99` |

Gitignored `bridge/config.yaml` on staging:

```yaml
llm:
  provider: openai
  model: gemini-2.5-flash-lite
  fallback_model: gemini-2.5-flash
  base_url: http://10.0.10.151:3100/v1
```

---

### Phase 5 — Agent workflow (verify gate update)

| Gate | CachyOS builder | Staging E2E |
|------|-----------------|-------------|
| G1 pytest | yes | yes |
| G2 mod build | yes (local JAR) | yes (staging JAR) |
| G4 bridge curl | yes | yes |
| G6 dashboard vision | headless Playwright | headless on `10.0.10.202:3847` |
| **G8 game mod API** | skip | `game_connected: true`, `:47823` health |
| **G9 instruct smoke** | skip | one chat via bridge |

Critic session: require **staging E2E JSON** for slices that touch game/LLM integration; CachyOS-only verify is **warn** for G8/G9.

---

## Ivan-only checklist (before agents run E2E)

- [ ] Phase 0: new-api reachable at `10.0.10.151:3100` from staging
- [ ] `NEWAPI_API_KEY` in staging `~/.hermes/.env` (not in git)
- [ ] Syx Demo installed on staging; mod enabled in launcher once
- [ ] Phase 1 spike passed (game + mod API on `:99`)
- [ ] Confirm OK to use **Demo** license on staging (or full Syx if required)

---

## Out of scope (for now)

- GPU passthrough to staging VM
- Running Steam on CachyOS from agents
- Public exposure of new-api or bridge ports beyond LAN
- Automated Steam Guard / account sharing in repo
- Save-game sync between Cachy live play and staging (separate instances)

---

## Suggested slice order

1. **Slice 5b** — Phase 0 new-api LAN + `SYX_LLM_BASE_URL` in bridge config loader  
2. **Slice 6** — Phase 1 spike doc + `staging-game-lab.sh` skeleton  
3. **Slice 7** — Ivan installs Syx on staging; Phase 3–5 staging full verify script  
4. Update `neonoodles-ctrl/2. BOILER ROOM/syx-llm-overlord/slices.md` with staging E2E line

---

## Next action

**Ivan:** pick Steam install path (A GUI vs D steamcmd) and confirm new-api can move to `10.0.10.151:3100` LAN.

**Builder:** after Phase 0 + Ivan install, run Phase 1 spike on staging and record go/no-go in `output/handoff/staging-spike-YYYY-MM-DD.md`.
