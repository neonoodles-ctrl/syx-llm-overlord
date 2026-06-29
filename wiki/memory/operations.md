# Memory operations

## Dashboard

- **Direct Order** — queued as `order` + injected next tick
- **Session Memory** — live tail of JSONL; **Clear** wipes log

## API

```bash
# Read last 50 entries
curl http://localhost:3847/api/memory

# Add a note the overlord will remember
curl -X POST http://localhost:3847/api/memory \
  -H 'Content-Type: application/json' \
  -d '{"text":"Home built at 386,128. Do not rebuild there."}'

# Clear session memory (new world)
curl -X DELETE http://localhost:3847/api/memory

# Player order (also logs to memory)
curl -X POST http://localhost:3847/api/instruct \
  -H 'Content-Type: application/json' \
  -d '{"message":"Build farms east of throne only."}'
```

## Restart bridge (after playbook edits)

```bash
/home/hermesprime/GAMES/Neonoodles-ctrl/syx/scripts/restart-bridge.sh
```

## Tail log in terminal

```bash
tail -f /home/hermesprime/GAMES/Neonoodles-ctrl/syx/logs/overlord-memory.jsonl
```
